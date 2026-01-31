"""
MediaHandler - обработчик медиа для B2B-WC Converter v2.0.
Обрабатывает: изображения, видео, документы.
"""
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        
        # Создаем папку, если она не существует
        ensure_directory(self.download_dir)
    
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
        images_str = raw_product.Изображение.strip() if raw_product.Изображение else ""
        
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
        
        # Используем ThreadPoolExecutor для параллельного скачивания
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, url in enumerate(image_urls):
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
        Скачивает одно изображение.
        
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
            
            # Используем утилиту для скачивания
            timeout = self.config_manager.get_setting('processing.image_timeout', 30)
            retries = self.config_manager.get_setting('processing.image_retries', 2)
            
            success = download_file(url, local_path, timeout, retries)
            
            if success:
                self.downloaded_images += 1
                logger.debug(f"Скачано изображение: {local_filename}")
                return local_path
            else:
                self.failed_downloads += 1
                return None
            
        except Exception as e:
            self.failed_downloads += 1
            logger.warning(f"Ошибка скачивания изображения {url}: {e}")
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
            'https://вашсайт.ru/wp-content/uploads/products/{ns_code}-{slug}-{index}.webp'
        )
        
        # Шаблон для alt и title
        alt_template = self.config_manager.get_setting(
            'templates.image_alt_title',
            '{category} {product_name}'
        )
        
        # Подготавливаем данные для шаблона
        category = raw_product.Название_категории or ""
        product_name = raw_product.Наименование or ""
        
        alt_text = alt_template.format(
            category=category.split(' - ')[0] if ' - ' in category else category,
            product_name=product_name
        )
        
        for i, url in enumerate(image_urls):
            index = i + 1
            
            # Заменяем плейсхолдеры в шаблоне URL
            image_url = template.format(
                ns_code=ns_code,
                slug=slug,
                index=index
            )
            
            # Формируем строку изображения для WooCommerce
            # Формат: "URL | Alt | Title | Description | Gallery | Featured"
            image_entry = f"{image_url} | {alt_text} | {alt_text} | | {'yes' if i == 0 else 'no'} | {'yes' if i == 0 else 'no'}"
            images_data.append(image_entry)
        
        # Объединяем все изображения через "::"
        return " :: ".join(images_data)
    
    def _process_video(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает видео товара.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полями meta:видео_url и meta:видео_превью
        """
        video_url = raw_product.Видео.strip() if raw_product.Видео else ""
        
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