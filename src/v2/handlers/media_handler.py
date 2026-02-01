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
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полем images
        """
        from ..utils.validators import safe_getattr
        
        images_str = safe_getattr(raw_product, "Изображение")
        
        if not images_str:
            return {"images": ""}
        
        # Используем утилиту для разбиения URL
        image_urls = split_image_urls(images_str)
        
        if not image_urls:
            return {"images": ""}
        
        # Генерируем slug из названия товара
        slug = self._generate_slug_from_title(raw_product.Наименование)
        ns_code = raw_product.НС_код or "unknown"
        
        # Скачиваем изображения (если включено в настройках)
        downloaded_files = []
        if self.config_manager.get_setting('processing.download_images', True):
            downloaded_files = self._download_images(image_urls, ns_code, slug)
        
        # Формируем строку для поля images WooCommerce
        images_field = self._generate_images_field(
            image_urls, downloaded_files, ns_code, slug, raw_product
        )
        
        return {"images": images_field}
    
    def _generate_slug_from_title(self, title: str) -> str:
        """
        Генерирует slug из названия товара.
        
        Args:
            title: Название товара
            
        Returns:
            slug
        """
        from ..utils.validators import generate_slug
        return generate_slug(title)
    
    def _download_images(self, image_urls: List[str], ns_code: str, slug: str) -> List[Path]:
        """
        Скачивает изображения в локальную папку.
        
        Args:
            image_urls: Список URL изображений
            ns_code: НС-код товара
            slug: slug товара
            
        Returns:
            Список путей к скачанным файлам
        """
        if not image_urls:
            return []
        
        downloaded_files = []
        max_workers = self.config_manager.get_setting('processing.max_image_workers', 4)
        
        # 🔧 ИСПРАВЛЕНО: Добавляем задержку между запросами для имитации поведения человека
        delay_between_requests = self.config_manager.get_setting('processing.image_delay', 1.0)
        
        # Используем ThreadPoolExecutor для параллельного скачивания
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, url in enumerate(image_urls):
                # 🔧 ИСПРАВЛЕНО: Добавляем задержку между запуском задач
                if i > 0 and delay_between_requests > 0:
                    time.sleep(delay_between_requests)
                    
                future = executor.submit(
                    self._download_single_image,
                    url, ns_code, slug, i + 1
                )
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    downloaded_files.append(result)
        
        return downloaded_files
    
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
    
    def _generate_images_field(self, image_urls: List[str], downloaded_files: List[Path], 
                              ns_code: str, slug: str, raw_product: RawProduct) -> str:
        """
        Формирует строку для поля images WooCommerce.
        
        Args:
            image_urls: Список URL изображений
            downloaded_files: Список путей к скачанным файлам
            ns_code: НС-код товара
            slug: slug товара
            raw_product: Сырые данные продукта
            
        Returns:
            Строка для поля images
        """
        if not image_urls:
            return ""
        
        images_data = []
        template = self.config_manager.get_setting(
            'paths.final_image_url_template',
            'https://kvanta42.ru/wp-content/uploads/2026/02/{ns_code}-{slug}-{index}.webp'
        )
        
        # Транслитерируем ns_code
        latin_ns_code = self._transliterate_to_latin(ns_code)
        safe_ns_code = re.sub(r'[^a-zA-Z0-9_-]', '', latin_ns_code).lower()
        
        # Получаем нормальное название товара для alt/title
        product_name = raw_product.Наименование or ""
        # Очищаем название: убираем лишние пробелы, переносы
        clean_name = ' '.join(product_name.split()).strip()
        
        # Можно добавить номер изображения, но не обязательно
        # alt_title_text = f"{clean_name} - изображение {i+1}"
        alt_title_text = clean_name  # Просто название товара
        
        for i, url in enumerate(image_urls):
            index = i + 1
            
            # Заменяем плейсхолдеры в шаблоне URL
            image_url = template.format(
                ns_code=safe_ns_code,
                slug=slug,
                index=index
            )
            
            # Формат с нормальным названием
            image_entry = f"{image_url} ! alt : {alt_title_text} ! title : {alt_title_text} ! desc : ! caption :"
            images_data.append(image_entry)
        
        return " | ".join(images_data)

        
        # Объединяем все изображения через " | "
        return " | ".join(images_data)
    


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