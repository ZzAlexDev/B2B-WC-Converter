"""
MediaHandler - обработчик медиа для B2B-WC Converter v2.0.
Обрабатывает: изображения, видео, документы.
"""
import os
import re
import requests
import time  # 🔧 ИСПРАВЛЕНО: Добавлен импорт для пауз
from typing import Dict, Any, List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..utils.validators import generate_slug

# Используем относительные импорты
try:
    from .base_handler import BaseHandler
    from ..models import RawProduct
    from ..config_manager import ConfigManager
    from ..utils.logger import get_logger
    from ..utils.validators import extract_youtube_id, is_valid_url
    from ..utils.file_utils import (
        split_image_urls,
        sanitize_filename,
        download_file,
        get_file_extension_from_url,
        ensure_directory
    )
except ImportError:
    from base_handler import BaseHandler
    from models import RawProduct
    from config_manager import ConfigManager
    from utils.logger import get_logger
    from utils.validators import extract_youtube_id, is_valid_url
    from utils.file_utils import (
        split_image_urls,
        sanitize_filename,
        download_file,
        get_file_extension_from_url,
        ensure_directory
    )

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
        
        # Счетчик скачанных изображений
        self.downloaded_images = 0
        self.failed_downloads = 0
        
        # Папка для скачивания изображений
        self.download_dir = Path(self.config_manager.get_setting(
            'paths.local_image_download', 
            'data/downloads/images/'
        ))
        
        # 🔧 ИСПРАВЛЕНО: Создаем сессию requests с заголовками браузера
        self._init_requests_session()
        
        # Создаем папку, если она не существует
        ensure_directory(self.download_dir)

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
                    f"{self.downloaded_images} изображений скачано")
        return result
    
    def _process_images(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает изображения товара.
        Генерирует URL всегда, скачивает только если файла нет локально.
        """
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
            if not image_url:
                continue
            
            try:
                # 1. Определяем локальный путь и финальный URL
                local_path, final_url, need_download = self._prepare_image_paths(
                    image_url, raw_product, idx
                )
                
                logger.debug(f"  Изображение {idx+1}: need_download={need_download}, local_path={local_path}, url={image_url[:50]}...")
                
                # 2. Скачиваем только если нужно
                if need_download:
                    success = self._download_single_image_with_session(image_url, local_path)
                    if success:
                        logger.info(f"Скачано новое изображение: {image_url} → {local_path}")
                    else:
                        logger.warning(f"Не удалось скачать изображение: {image_url}")
                        continue  # Пропускаем это изображение
                else:
                    logger.debug(f"Изображение уже существует: {local_path}")
                
                # 3. Всегда добавляем финальный URL (даже если не скачивали)
                if final_url:
                    # Форматируем для WooCommerce: URL ! alt : текст ! title : текст
                    clean_name = ' '.join((raw_product.Наименование or "").split()).strip()
                    image_entry = f"{final_url} ! alt : {clean_name} ! title : {clean_name} ! desc : ! caption :"
                    final_image_urls.append(image_entry)
                    self.downloaded_images += 1
                    
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
        Сначала генерирует финальный URL, затем имя файла берётся из него.
        Гарантирует идентичность имён в URL и локальной файловой системе.
        
        Args:
            image_url: Исходный URL изображения
            raw_product: Объект RawProduct (нужен и НС-код, и название для slug)
            index: Индекс изображения (0-based)
            
        Returns:
            Кортеж: (локальный_путь, финальный_url, нужно_ли_скачивать)
        """
        # 1. Генерируем финальный URL
        final_url = self._generate_final_url(raw_product, index, image_url)
        
        # 2. Извлекаем имя файла из URL (гарантирует совпадение!)
        import os
        url_filename = os.path.basename(final_url)  # "ns-1135450-sushilka-...-1.jpg"
        
        # 3. Локальный путь с ТЕМ ЖЕ именем файла
        download_dir = Path(self.config_manager.get_setting(
            'paths.local_image_download',
            'data/downloads/images/'
        ))
        download_dir.mkdir(parents=True, exist_ok=True)
        local_path = download_dir / url_filename
        
        # 4. Проверяем, нужно ли скачивать
        need_download = not local_path.exists()
        
        # Отладка
        logger.debug(f"Генерация путей для {raw_product.НС_код}, изображение {index+1}")
        logger.debug(f"  Финальный URL: {final_url}")
        logger.debug(f"  Имя файла из URL: {url_filename}")
        logger.debug(f"  Локальный путь: {local_path}")
        logger.debug(f"  need_download: {need_download}")
        
        return local_path, final_url, need_download

    def _generate_final_url(self, raw_product: RawProduct, index: int, image_url: str = "") -> str:
        """
        Генерирует финальный URL для изображения.
        Централизованная генерация - используется для создания и URL, и имени файла.
        
        Args:
            raw_product: Объект RawProduct
            index: Индекс изображения
            image_url: Исходный URL (для определения расширения)
            
        Returns:
            Финальный URL
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
        final_url_template = self.config_manager.get_setting(
            'paths.final_image_url_template',
            'https://kvanta42.ru/wp-content/uploads/2026/02/{ns_code}-{slug}-{index}.webp'            
        )

        # 5. ПРИНУДИТЕЛЬНО заменяем {ext} на .webp если есть
        if '{ext}' in final_url_template:
            # Вариант A: Простая замена
            final_url_template = final_url_template.replace('{ext}', 'webp')
            logger.warning(f"Заменён {{ext}} на 'webp' в шаблоне")

        
        # 6. Заменяем плейсхолдеры
        final_url = final_url_template.format(
            ns_code=safe_ns_code,
            slug=slug,
            index=index + 1,
            ext=original_ext
        )
        
        return final_url
    
    def _download_single_image_with_session(self, image_url: str, local_path: Path) -> bool:
        """
        Скачивает одно изображение с использованием сессии.
        
        Args:
            image_url: URL изображения
            local_path: Локальный путь для сохранения
            
        Returns:
            True если успешно, False если ошибка
        """
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
                    
                    logger.debug(f"Успешно скачано: {image_url} → {local_path}")
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
            logger.error(f"Неожиданная ошибка при скачивании {image_url}: {e}")
            return False
        
        return False
    
    def _generate_slug_from_title(self, title: str) -> str:
        """
        Генерирует slug из названия товара.
        
        Args:
            title: Название товара
            
        Returns:
            slug (латиница, нижний регистр, дефисы)
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
            
            # Транслитерация кириллицы (можно использовать вашу функцию _transliterate_to_latin)
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
        
        Args:
            filename: Исходное имя
            
        Returns:
            Безопасное имя файла
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

 
    def _download_single_image(self, url: str, ns_code: str, slug: str, index: int) -> Optional[Path]:
        """
        Скачивает одно изображение с использованием сессии и заголовков браузера.
        
        Args:
            url: URL изображения
            ns_code: НС-код товара
            slug: slug товара
            index: индекс изображения (начиная с 1)
            
        Returns:
            Путь к скачанному файлу или None при ошибке
        """
        try:
            # Используем утилиту для определения расширения
            ext = get_file_extension_from_url(url)
            if not ext:
                ext = 'jpg'
            
            # Создаем безопасное имя файла
            safe_ns_code = sanitize_filename(ns_code)
            safe_slug = sanitize_filename(slug)
            
            local_filename = f"{safe_ns_code}-{safe_slug}-{index}.{ext}"
            local_path = self.download_dir / local_filename
            
            # 🔧 ИСПРАВЛЕНО: Используем сессию с заголовками браузера
            timeout = self.config_manager.get_setting('processing.image_timeout', 30)
            retries = self.config_manager.get_setting('processing.image_retries', 2)
            
            # Пытаемся скачать файл с использованием сессии
            for attempt in range(retries):
                try:
                    response = self.session.get(url, timeout=timeout)
                    response.raise_for_status()  # Проверяем статус (403, 404 и т.д.)
                    
                    # Сохраняем файл
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.downloaded_images += 1
                    logger.debug(f"Скачано изображение: {local_filename}")
                    return local_path
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403 and attempt < retries - 1:
                        # 🔧 ИСПРАВЛЕНО: При 403 пробуем добавить Referer заголовок
                        logger.debug(f"Попытка {attempt + 1}: 403 Forbidden для {url}, пробуем с Referer...")
                        self.session.headers.update({"Referer": "https://www.google.com/"})
                        time.sleep(2 ** attempt)  # Экспоненциальная задержка
                        continue
                    else:
                        logger.warning(f"Не удалось скачать {url} (попытка {attempt + 1}): {e}")
                        self.failed_downloads += 1
                        return None
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Ошибка сети для {url} (попытка {attempt + 1}): {e}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Экспоненциальная задержка
                    else:
                        self.failed_downloads += 1
                        return None
            
        except Exception as e:
            self.failed_downloads += 1
            logger.warning(f"Неожиданная ошибка при скачивании {url}: {e}")
            return None
    



    def _process_video(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает видео товара.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полями meta:видео_url и meta:видео_превью
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
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полями для документов
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
        Логирует статистику скачивания.
        """
        logger.info(f"MediaHandler: скачано {self.downloaded_images} изображений, "
                   f"ошибок: {self.failed_downloads}")
        super().cleanup()