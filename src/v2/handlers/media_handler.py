"""
MediaHandler - обработчик медиа для B2B-WC Converter v2.0.
"""
import os
import re
import requests
import time
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Пробуем разные варианты импорта
try:
    # Вариант 1: относительный импорт (предпочтительный)
    from .base_handler import BaseHandler
except ImportError:
    try:
        # Вариант 2: абсолютный импорт
        from src.v2.handlers.base_handler import BaseHandler
    except ImportError:
        # Вариант 3: прямой импорт (если файл в той же папке)
        import sys
        from pathlib import Path
        
        # Добавляем текущую директорию в sys.path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        from base_handler import BaseHandler

try:
    # Импорты из src/v2 - используем относительные импорты
    from ..models import RawProduct
    from ..config_manager import ConfigManager
    
    print(f"✅ Основные импорты успешны")
    
    # Импорты из utils - используем относительные импорты
    from ..utils import (
        get_logger,
        extract_youtube_id,
        is_valid_url,
        generate_slug,
        split_image_urls,
        sanitize_filename,
        download_file,
        get_file_extension_from_url,
        ensure_directory,
        ImageProcessor,
        FTPUploader,
        ImageStatusTracker
    )
    
    print(f"✅ Все импорты успешны")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Текущий файл: {__file__}")
    raise

# Создаем логгер
logger = get_logger(__name__)

class MediaHandler(BaseHandler):
    """
    Обработчик медиафайлов товара.
    Скачивает изображения, генерирует пути, обрабатывает видео и документы.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует MediaHandler.
        
        Args:
            config_manager: Менеджер конфигураций
        """
        super().__init__(config_manager)

        print(f"\n🔍 DEBUG MediaHandler.__init__:")
        
        # 1. Получаем все конфигурации ОДИН РАЗ
        self.media_config = self.config_manager.get_setting('media', {}) if self.config_manager else {}
        self.image_processing_config = self.config_manager.get_setting('image_processing', {}) if self.config_manager else {}
        self.paths_config = self.config_manager.get_setting('paths', {}) if self.config_manager else {}
        self.ftp_config = self.config_manager.get_setting('ftp', {}) if self.config_manager else {}
        
        print(f"   media_config: {self.media_config}")
        print(f"   image_processing_config keys: {list(self.image_processing_config.keys()) if self.image_processing_config else 'EMPTY'}")
        print(f"   paths_config: {self.paths_config}")
        print(f"   ftp_config: {self.ftp_config}")
        
        # 2. Настройки обработки изображений
        # Проверяем, что секция image_processing существует И не пустая
        if not self.image_processing_config or 'enabled' not in self.image_processing_config:
            print(f"⚠️ Секция 'image_processing' не найдена или неполная: {self.image_processing_config}")
            print("   Создаем из media_config с fallback значениями")
            self.image_processing_config = {
                'enabled': self.media_config.get('enabled', True),  # Используем 'enabled' из media, а не 'image_processing_enabled'
                'quality': 85,
                'output_format': 'webp',
                'max_file_size_mb': 1.0,
                'delete_original': False,
                'skip_processed': False,
                'target_width': 1000,
                'target_height': 1000,
                'add_noise': True,
                'noise_level': 0.02,
                'preserve_metadata': False,
                'auto_orient': True
            }
        
        # ТЕПЕРЬ безопасно получаем значения
        self.image_processing_enabled = self.image_processing_config.get('enabled', True)
        
        # ✅ ДОБАВЬТЕ ЭТИ ПЕРЕМЕННЫЕ:
        self.skip_processed = self.image_processing_config.get('skip_processed', False)
        self.delete_original = self.image_processing_config.get('delete_original', False)
        
        print(f"   ✅ image_processing_enabled: {self.image_processing_enabled}")
        print(f"   ✅ skip_processed: {self.skip_processed}")
        print(f"   ✅ delete_original: {self.delete_original}")
        print(f"   ✅ Все настройки image_processing: {self.image_processing_config}")


        
        # 3. Настройки загрузки
        self.download_timeout = self.media_config.get('download_timeout', 
                               self.media_config.get('timeout_seconds', 30))
        self.max_retries = self.media_config.get('max_retries', 3)
        self.max_workers = self.media_config.get('max_workers', 5)
        
        # 4. Пути к директориям (только один раз!)
        self.download_dir = Path(
            self.paths_config.get('local_image_download', 'data/downloads/images/')
        )
        self.converted_dir = Path(
            self.paths_config.get('local_image_converted', 'data/downloads/converted/')
        )
        self.temp_dir = Path(self.media_config.get('temp_dir', 'temp/media'))
        self.output_dir = Path(self.media_config.get('output_dir', 'output/media'))
        
        print(f"   download_dir: {self.download_dir}")
        print(f"   converted_dir: {self.converted_dir}")
        
        # 5. Создаем директории
        ensure_directory(self.download_dir)
        ensure_directory(self.converted_dir)
        ensure_directory(self.temp_dir)
        ensure_directory(self.output_dir)
        
        # 6. Инициализируем утилиты (только один раз!)
        self.image_processor = ImageProcessor(self.image_processing_config) if ImageProcessor else None
        print(f"   image_processor создан: {self.image_processor}")
        
        # Для FTPUploader собираем полный конфиг
        ftp_full_config = {
            'ftp': self.ftp_config,
            'paths': self.paths_config
        }
        self.ftp_uploader = FTPUploader(ftp_full_config) if FTPUploader else None
        
        self.status_tracker = ImageStatusTracker() if ImageStatusTracker else None
        
        # 7. Настройки FTP из .env
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Проверяем флаг из .env ИЛИ из конфига
        ftp_enabled_env = os.getenv('FTP_ENABLED', 'false').lower() == 'true'
        ftp_enabled_config = self.ftp_config.get('enabled', False)
        
        self.ftp_upload_enabled = ftp_enabled_env or ftp_enabled_config
        
        # Проверяем наличие обязательных переменных
        ftp_host = os.getenv('FTP_HOST') or self.ftp_config.get('host')
        ftp_username = os.getenv('FTP_USERNAME') or self.ftp_config.get('username')
        ftp_password = os.getenv('FTP_PASSWORD') or self.ftp_config.get('password')
        
        if self.ftp_upload_enabled and (not ftp_host or not ftp_username or not ftp_password):
            print("⚠️ FTP включен, но отсутствуют обязательные настройки")
            self.ftp_upload_enabled = False
        
        print(f"   ftp_upload_enabled: {self.ftp_upload_enabled}")
        
        # 8. Счетчики
        self.downloaded_images = 0
        self.failed_downloads = 0
        self.skipped_images = 0  # Новый счетчик для пропущенных
        
        # 9. Сессия requests
        self._init_requests_session()

        # ⭐ ДОБАВЛЯЕМ ФИЛЬТРЫ В САМЫЙ КОНЕЦ
        self.filters_config = self.config_manager.get_setting('filters', {})
        self.filters_enabled = self.filters_config.get('enabled', False)
        
        # Логируем статус фильтров
        print(f"🔍 MediaHandler: фильтры {'ВКЛЮЧЕНЫ' if self.filters_enabled else 'ВЫКЛЮЧЕНЫ'}")
        if self.filters_enabled:
            print(f"   Режим: {self.filters_config.get('mode', 'AND')}")
            print(f"   Брендов в фильтре: {len(self.filters_config.get('brands', []))}")
            print(f"   Категорий в фильтре: {len(self.filters_config.get('categories', []))}")
       
        
        logger.info(f"MediaHandler инициализирован: "
                   f"image_processing={self.image_processing_enabled}, "
                   f"ftp_upload={self.ftp_upload_enabled}")
        
    def validate(self, data: Any) -> bool:
        """
        Валидация данных для обработки
        
        Args:
            data: Данные для валидации
            
        Returns:
            bool: True если данные валидны
        """
        if not data:
            logger.warning("Пустые данные для обработки")
            return False
        
        if isinstance(data, RawProduct):
            # Проверяем наличие медиа в RawProduct
            has_images = bool(data.images and data.images.strip())
            has_video = bool(data.video_url and data.video_url.strip())
            
            if not (has_images or has_video):
                logger.warning(f"RawProduct {data.product_name} не содержит медиа")
                return False
                
        elif isinstance(data, str):
            # Проверяем строку (URL или путь)
            if not data.strip():
                return False
                
        return True
    
    async def process_async(self, data: Any) -> Dict[str, Any]:
        """
        Асинхронная обработка медиа-контента
        
        Args:
            data: Данные для обработки (RawProduct, URL, путь к файлу)
            
        Returns:
            Dict с результатами обработки
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process, data)
    
    def process(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает медиа товара.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полями images и ссылками на документы
        """
        result = {}
        
        # 1. Обрабатываем изображения
        result.update(self._process_images(raw_product))
        
        # 2. Обрабатываем видео
        result.update(self._process_video(raw_product))
        
        # 3. Обрабатываем документы
        result.update(self._process_documents(raw_product))
        
        logger.debug(f"MediaHandler обработал продукт {raw_product.НС_код}: "
                    f"{self.downloaded_images} изображений скачано, "
                    f"{self.skipped_images} пропущено")
        return result
    
    def _init_requests_session(self) -> None:
        """
        Инициализирует сессию requests с заголовками браузера.
        """
        self.session = requests.Session()
        
        # Заголовки, которые отправляет реальный браузер Chrome
        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
        }
        
        self.session.headers.update(browser_headers)
    
    def _transliterate_to_latin(self, text: str) -> str:
        """
        Транслитерирует кириллицу в латиницу.
        
        Args:
            text: Текст для транслитерации
            
        Returns:
            Текст на латинице
        """
        if not text:
            return ""
        
        # Простая таблица транслитерации
        cyr_to_lat = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
            'Е': 'E', 'Ё': 'YO', 'Ж': 'ZH', 'З': 'Z', 'И': 'I',
            'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
            'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
            'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'TS', 'Ч': 'CH',
            'Ш': 'SH', 'Щ': 'SCH', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
            'Э': 'E', 'Ю': 'YU', 'Я': 'YA'
        }
        
        result = []
        for char in text:
            if char in cyr_to_lat:
                result.append(cyr_to_lat[char])
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _process_images(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает изображения товара.
        Генерирует URL всегда, скачивает только если файла нет локально.
        """
        print(f"\n🎨 DEBUG _process_images:")
        print(f"   raw_product.НС_код: {raw_product.НС_код}")
        print(f"   raw_product.Наименование: {raw_product.Наименование}")
        print(f"   image_processing_enabled: {self.image_processing_enabled}")
        
        result = {}
        
        if not hasattr(raw_product, 'Изображение') or not raw_product.Изображение:
            logger.debug(f"Нет изображений для продукта {raw_product.НС_код}")
            return result
        
        image_urls = [url.strip() for url in raw_product.Изображение.split(',') if url.strip()]
        
        if not image_urls:
            logger.debug(f"Пустой список изображений для продукта {raw_product.НС_код}")
            return result
        
        final_image_urls = []
        
        logger.debug(f"Начало обработки изображений для {raw_product.НС_код}: {len(image_urls)} URL")
        
        for idx, image_url in enumerate(image_urls):
            print(f"\n   Обработка изображения {idx+1}: {image_url[:50]}...")
            
            if not image_url:
                continue
            
            try:
                # 1. Определяем локальный путь и финальный URL
                local_path, final_url, should_download = self._prepare_image_paths(
                    image_url, raw_product, idx
                )
                
                logger.debug(f"  Изображение {idx+1}: should_download={should_download}, local_path={local_path}, url={image_url[:50]}...")
                
                # 2. Пытаемся скачать только если нужно
                downloaded = False
                if should_download:
                    print(f"   🚀 Начинаем скачивание...")
                    
                    # Получаем параметры для обработки
                    ns_code = self._get_clean_ns_code(raw_product.НС_код)
                    slug = self._generate_slug_from_title(raw_product.Наименование or "")
                    
                    print(f"   ns_code: {ns_code}")
                    print(f"   slug: {slug}")
                    print(f"   idx: {idx}")
                    
                    downloaded = self._download_single_image_with_session(
                        image_url, 
                        local_path,
                        ns_code,      # передаем параметры
                        slug,         # передаем параметры
                        idx           # передаем параметры
                    )
                    
                    if downloaded:
                        logger.info(f"Скачано новое изображение: {image_url} → {local_path}")
                        self.downloaded_images += 1
                    else:
                        logger.warning(f"Не удалось скачать изображение: {image_url}")
                        self.failed_downloads += 1
                        continue  # Пропускаем это изображение
                else:
                    logger.debug(f"Изображение уже существует: {local_path}")
                    self.skipped_images += 1
                    # Файл уже существует, но мы должны проверить, нужна ли обработка
                    # и FTP загрузка для существующих файлов
                    if not self.skip_processed:
                        ns_code = self._get_clean_ns_code(raw_product.НС_код)
                        slug = self._generate_slug_from_title(raw_product.Наименование or "")
                        self._process_and_upload_image(ns_code, slug, idx, local_path)
                
                # 3. Всегда добавляем финальный URL (даже если не скачивали)
                if final_url:
                    # Форматируем для WooCommerce: URL ! alt : текст ! title : текст
                    clean_name = ' '.join((raw_product.Наименование or "").split()).strip()
                    image_entry = f"{final_url} ! alt : {clean_name} ! title : {clean_name} ! desc : ! caption :"
                    final_image_urls.append(image_entry)
                    
            except Exception as e:
                logger.error(f"Ошибка обработки изображения {image_url}: {e}", exc_info=True)
                # Пропускаем проблемное изображение
        
        # Формируем итоговую строку для WooCommerce
        if final_image_urls:
            result['images'] = " | ".join(final_image_urls)
            logger.debug(f"Для {raw_product.НС_код} сформировано {len(final_image_urls)} изображений")
        else:
            logger.warning(f"Не удалось обработать ни одного изображения для {raw_product.НС_код}")
        
        return result
    
    def _prepare_image_paths(self, image_url: str, raw_product: RawProduct, index: int) -> tuple[Path, str, bool]:
        """
        Подготавливает пути для изображения.
        Возвращает: (локальный путь, финальный URL, нужно ли скачивать)
        """
        print(f"\n🔧 DEBUG _prepare_image_paths:")
        print(f"   index: {index}")
        print(f"   skip_processed: {self.skip_processed}")
        print(f"   raw_product.НС_код: {raw_product.НС_код}")
        
        # 1. Генерируем финальный URL
        final_url = self._generate_final_url(raw_product, index, image_url)
        
        # 2. Извлекаем имя файла из URL
        import os
        url_filename = os.path.basename(final_url)
        
        # 3. Локальный путь
        if self.image_processing_enabled:
            download_dir = self.converted_dir
            if url_filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                url_filename = os.path.splitext(url_filename)[0] + '.webp'
        else:
            download_dir = self.download_dir
        
        download_dir.mkdir(parents=True, exist_ok=True)
        local_path = download_dir / url_filename
        
        print(f"   local_path: {local_path}")
        print(f"   exists: {local_path.exists()}")
        
        # 4. Проверяем, нужно ли скачивать
        # Скачиваем только если файл не существует
        should_download = not local_path.exists()
        
        # Даже если файл существует, проверяем через трекер
        if not should_download and not self.skip_processed and self.status_tracker:
            ns_code_clean = self._get_clean_ns_code(raw_product.НС_код)
            slug = self._generate_slug_from_title(raw_product.Наименование or "")
            
            # Проверяем, нужно ли обработать существующий файл
            needs_processing = self.status_tracker.needs_processing(
                ns_code_clean, slug, index, local_path
            )
            
            # Если нужна обработка, мы не скачиваем заново, а просто используем существующий файл
            # Флаг should_download остается False, но потом будет вызвана обработка
            print(f"   status_tracker.needs_processing: {needs_processing}")
        
        print(f"   should_download: {should_download}")
        return local_path, final_url, should_download
    
    def _get_clean_ns_code(self, ns_code: str) -> str:
        """
        Очищает NS-код для использования в именах файлов.
        """
        if ns_code.startswith("НС-"):
            return "ns-" + ns_code[3:]
        elif ns_code.startswith("нс-"):
            return "ns-" + ns_code[3:]
        else:
            return ns_code
    
    def _generate_final_url(self, raw_product: RawProduct, index: int, image_url: str = "") -> str:
        """
        Генерирует финальный URL для изображения.
        """
        # 1. Нормализуем НС-код (НС → ns)
        ns_code = raw_product.НС_код
        if ns_code.startswith("НС-"):
            ns_code_clean = "ns-" + ns_code[3:]  # "НС-1135450" → "ns-1135450"
        elif ns_code.startswith("нс-"):
            ns_code_clean = "ns-" + ns_code[3:]
        else:
            ns_code_clean = ns_code
        
        safe_ns_code = self._sanitize_filename(ns_code_clean)
        
        # 2. Генерируем slug из названия
        product_name = raw_product.Наименование or ""
        slug = self._generate_slug_from_title(product_name)
        
        # 3. Определяем расширение файла
        if image_url:
            from ..utils.file_utils import get_file_extension_from_url
            original_ext = get_file_extension_from_url(image_url)
            if not original_ext:
                original_ext = 'jpg'
        else:
            original_ext = 'jpg'
        
        # 4. Получаем шаблон URL из конфига
        try:
            final_url_template = self.config_manager.get_setting('paths.final_image_url_template')
        except Exception:
            final_url_template = 'uploads/{ns_code}-{slug}-{index}.webp'
        
        # 5. Заменяем {ext} на .webp если есть
        if '{ext}' in final_url_template:
            final_url_template = final_url_template.replace('{ext}', 'webp')
        
        # 6. Заменяем плейсхолдеры
        final_url = final_url_template.format(
            ns_code=safe_ns_code,
            slug=slug,
            index=index + 1,
            ext=original_ext
        )
        
        return final_url
    
    def _download_single_image_with_session(self, image_url: str, local_path: Path,
                                            ns_code: str = "", slug: str = "", 
                                            index: int = 0) -> bool:
        """
        Скачивает одно изображение с использованием сессии.
        ВОЗВРАЩАЕТ: True если успешно скачано, False если ошибка
        """
        print(f"\n📥 DEBUG _download_single_image_with_session:")
        print(f"   URL: {image_url}")
        print(f"   local_path: {local_path}")
        print(f"   ns_code: {ns_code}, slug: {slug}, index: {index}")
        
        try:
            # Настройки из конфига
            timeout = self.config_manager.get_setting('processing.image_timeout', 30)
            retries = self.config_manager.get_setting('processing.image_retries', 2)
            
            # Пытаемся скачать файл
            for attempt in range(retries):
                try:
                    response = self.session.get(image_url, timeout=timeout)
                    response.raise_for_status()
                    
                    # Проверяем, что это действительно изображение
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        logger.warning(f"URL {image_url} возвращает не изображение: {content_type}")
                        return False
                    
                    # Сохраняем файл
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Проверяем, что файл не пустой
                    if local_path.stat().st_size == 0:
                        logger.warning(f"Скачанный файл пустой: {image_url}")
                        local_path.unlink(missing_ok=True)
                        return False
                    
                    print(f"✅ Изображение успешно скачано")
                    logger.debug(f"Успешно скачано: {image_url} → {local_path}")
                    
                    # ⭐ Обработка и FTP загрузка после успешного скачивания
                    if ns_code and slug and index >= 0:
                        print(f"🚀 Вызываем _process_and_upload_image...")
                        # Отмечаем как скачанный в трекере
                        if self.status_tracker:
                            self.status_tracker.mark_downloaded(ns_code, slug, index, local_path)
                        
                        # Обрабатываем и загружаем на FTP
                        self._process_and_upload_image(ns_code, slug, index, local_path)
                    else:
                        print(f"⚠️ Пропускаем обработку: не хватает данных (ns_code={ns_code}, slug={slug}, index={index})")
                    
                    return True
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403:
                        logger.debug(f"Попытка {attempt+1}: 403 Forbidden для {image_url}")
                        # Пробуем с Referer
                        self.session.headers.update({"Referer": "https://www.google.com/"})
                    else:
                        logger.warning(f"HTTP ошибка {e.response.status_code} для {image_url}")
                    
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Экспоненциальная задержка
                    else:
                        return False
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Ошибка сети для {image_url}: {e}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        return False
        
        except Exception as e:
            print(f"❌ Исключение: {e}")
            logger.error(f"Неожиданная ошибка при скачивании {image_url}: {e}")
            return False
        
        return False
    
    def _process_and_upload_image(self, ns_code: str, slug: str, index: int, 
                                  downloaded_path: Path) -> Optional[Path]:
        """
        Обрабатывает скачанное изображение и загружает на FTP.
        ВОЗВРАЩАЕТ: путь к обработанному файлу или None
        """
        if not downloaded_path.exists():
            logger.warning(f"Файл для обработки не найден: {downloaded_path}")
            return None
        
        processed_path = None
        ftp_index = index + 1 
        
        # ДИАГНОСТИКА: собираем информацию о файле перед обработкой
        print(f"\n📊 ДИАГНОСТИКА ИЗОБРАЖЕНИЯ {index+1}:")
        print(f"   Файл: {downloaded_path.name}")
        print(f"   Размер: {downloaded_path.stat().st_size / 1024:.1f} KB")
        
        # Проверяем размер изображения
        try:
            from PIL import Image
            with Image.open(downloaded_path) as img:
                original_size = img.size
                print(f"   Исходный размер: {original_size[0]}x{original_size[1]}")
                print(f"   Формат: {img.format}")
        except Exception as e:
            print(f"   ❌ Не удалось прочитать размер: {e}")
            original_size = (0, 0)
        
        # 1. ОБРАБОТКА ИЗОБРАЖЕНИЯ
        print(f"\n🔧 ПАРАМЕТРЫ ОБРАБОТКИ:")
        print(f"   image_processing_enabled: {self.image_processing_enabled}")
        print(f"   image_processor: {self.image_processor}")
        
        # Получаем target размеры для проверки
        target_width = self.image_processing_config.get('target_width', 1000)
        target_height = self.image_processing_config.get('target_height', 1000)
        print(f"   target_size: {target_width}x{target_height}")
        print(f"   skip_processed: {self.skip_processed}")
        
        if self.image_processing_enabled and self.image_processor:
            try:
                # Проверяем, нужно ли обрабатывать
                needs_processing = True
                if self.status_tracker:
                    needs_processing = self.status_tracker.needs_processing(
                        ns_code, slug, index, downloaded_path
                    )
                
                print(f"   needs_processing: {needs_processing}")
                
                if needs_processing:
                    print(f"   🚀 Начинаем обработку изображения...")
                    
                    # Выводим настройки обработки
                    print(f"   Качество: {self.image_processing_config.get('quality', 85)}")
                    print(f"   Формат: {self.image_processing_config.get('output_format', 'webp')}")
                    print(f"   Сохранять метаданные: {self.image_processing_config.get('preserve_metadata', False)}")
                    print(f"   Автоориентация: {self.image_processing_config.get('auto_orient', True)}")
                    
                    # Вызываем обработку с диагностикой
                    processed_path = self.image_processor.process_image(downloaded_path)
                    
                    print(f"   Результат обработки: {processed_path}")
                    
                    if processed_path and processed_path.exists():
                        # Проверяем результат
                        try:
                            with Image.open(processed_path) as img:
                                processed_size = img.size
                                print(f"   ✅ Обработанный размер: {processed_size[0]}x{processed_size[1]}")
                                
                                # Проверяем, изменился ли размер
                                if original_size[0] > 0 and processed_size[0] > 0:
                                    if processed_size[0] != target_width and processed_size[1] != target_height:
                                        print(f"   ⚠️  Размер НЕ соответствует target!")
                                        print(f"      Исходный: {original_size[0]}x{original_size[1]}")
                                        print(f"      Обработанный: {processed_size[0]}x{processed_size[1]}")
                                        print(f"      Target: {target_width}x{target_height}")
                        except Exception as e:
                            print(f"   ❌ Не удалось проверить обработанный файл: {e}")
                        
                        # Отмечаем как обработанное
                        if self.status_tracker:
                            self.status_tracker.mark_processed(
                                ns_code, slug, index, downloaded_path, processed_path
                            )
                        
                        # Удаляем оригинал если настроено
                        if self.delete_original:
                            try:
                                downloaded_path.unlink(missing_ok=True)
                                print(f"   🗑️ Удален оригинал: {downloaded_path.name}")
                            except Exception as e:
                                print(f"   ⚠️ Не удалось удалить оригинал: {e}")
                    else:
                        print(f"   ⚠️ Обработка изображения не удалась!")
                        processed_path = downloaded_path
                else:
                    print(f"   ⏭️ Пропускаем обработку (уже обработано)")
                    processed_path = downloaded_path
                    
            except Exception as e:
                print(f"   ❌ Ошибка обработки изображения: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"Ошибка обработки изображения {downloaded_path}: {e}")
                processed_path = downloaded_path
        else:
            print(f"   ⏭️ Обработка отключена или нет процессора")
            processed_path = downloaded_path

        
        # 2. ЗАГРУЗКА НА FTP
        print(f"\n🔍 ОТЛАДКА FTP ЗАГРУЗКИ:")
        print(f"   ftp_upload_enabled: {self.ftp_upload_enabled}")
        print(f"   ftp_uploader: {self.ftp_uploader}")
        print(f"   processed_path: {processed_path}")
        
        if self.ftp_upload_enabled and self.ftp_uploader and processed_path:
            try:
                # Проверяем, нужно ли загружать
                needs_upload = True
                if self.status_tracker:
                    needs_upload = self.status_tracker.needs_upload(ns_code, slug, index)
                
                print(f"   needs_upload: {needs_upload}")
                
                if needs_upload:
                    # Имя файла для FTP (всегда .webp для обработанных)
                    if processed_path.suffix.lower() == '.webp':
                        remote_filename = f"{ns_code}-{slug}-{ftp_index}.webp"
                    else:
                        # Если не .webp, берем оригинальное расширение
                        remote_filename = processed_path.name
                    
                    print(f"   🚀 Загружаем на FTP: {processed_path.name} → {remote_filename}")
                    
                    success = self.ftp_uploader.upload_file(processed_path, remote_filename)
                    
                    if success:
                        if self.status_tracker:
                            self.status_tracker.mark_uploaded(ns_code, slug, index, processed_path)
                        print(f"   ✅ Файл загружен на FTP: {remote_filename}")
                    else:
                        print(f"   ❌ Не удалось загрузить на FTP: {processed_path.name}")
                else:
                    print(f"   ⏭️ Пропускаем FTP загрузку (уже загружено)")
                    
            except Exception as e:
                print(f"   ❌ Ошибка FTP загрузки: {e}")
                logger.error(f"Ошибка FTP загрузки {processed_path}: {e}")
        
        print(f"\n" + "="*50)
        return processed_path
    
    def _generate_slug_from_title(self, title: str) -> str:
        """
        Генерирует slug из названия товара.
        """
        if not title:
            return "product"
        
        # Используем вашу утилиту или стандартную логику
        from ..utils.validators import generate_slug
        
        # Если утилита не импортируется, создаем простую версию
        try:
            return generate_slug(title)
        except:
            # Простая транслитерация и очистка
            import re
            
            # Транслитерация кириллицы
            latin_text = self._transliterate_to_latin(title)
            
            # Заменяем всё, кроме букв, цифр и дефисов
            slug = re.sub(r'[^a-zA-Z0-9-]+', '-', latin_text)
            
            # Убираем лишние дефисы
            slug = re.sub(r'-+', '-', slug)
            
            # Убираем дефисы в начале и конце
            slug = slug.strip('-')
            
            # Нижний регистр и ограничение длины
            return slug.lower()[:50]
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Очищает имя файла от небезопасных символов.
        """
        # Убираем небезопасные символы для файловой системы
        import re
        safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Убираем лишние пробелы
        safe = re.sub(r'\s+', '_', safe)
        # Убираем начальные/конечные точки и пробелы
        safe = safe.strip('. ')
        # Ограничиваем длину
        return safe[:100]
    
    def _process_video(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает видео товара.
        """
        from ..utils.validators import safe_getattr
        
        video_url = safe_getattr(raw_product, "Видео")
        
        if not video_url:
            return {}
        
        # Используем утилиту для извлечения YouTube ID
        youtube_id = extract_youtube_id(video_url)
        
        if not youtube_id:
            return {"meta:видео_url": video_url}
        
        # Генерируем URL превью
        thumbnail_template = self.config_manager.get_setting(
            'paths.video_thumbnail_template',
            'https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg'
        )
        
        thumbnail_url = thumbnail_template.format(youtube_id=youtube_id)
        
        return {
            "meta:видео_url": video_url,
            "meta:видео_превью": thumbnail_url
        }
    
    def _process_documents(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает документы товара.
        """
        result = {}
        
        # Список полей с документами
        doc_fields = [
            ("Чертежи", "чертеж"),
            ("Сертификаты", "сертификат"),
            ("Промоматериалы", "промо"),
            ("Инструкции", "инструкция")
        ]
        
        for field_name, doc_type in doc_fields:
            doc_url = getattr(raw_product, field_name, "").strip()
            
            # Проверяем валидность URL
            if doc_url and is_valid_url(doc_url):
                result[f"meta:{doc_type}_url"] = doc_url
        
        return result
    
    def cleanup(self) -> None:
        """
        Логирует статистику скачивания и обработки.
        """
        # Статистика из трекера если есть
        if self.status_tracker:
            try:
                with open(self.status_tracker.status_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    total = len(data.get("images", {}))
                    processed = sum(1 for img in data["images"].values() if img.get("processed"))
                    uploaded = sum(1 for img in data["images"].values() if img.get("uploaded"))
                    
                    logger.info(f"📊 Статистика обработки изображений:")
                    logger.info(f"   Всего: {total}, Обработано: {processed}, Загружено на FTP: {uploaded}")
            except Exception as e:
                logger.debug(f"Не удалось загрузить статистику: {e}")
        
        # Базовая статистика
        logger.info(f"MediaHandler: скачано {self.downloaded_images} изображений, "
                   f"ошибок: {self.failed_downloads}, "
                   f"пропущено: {self.skipped_images}")
        super().cleanup()