"""
MediaHandler - обработчик медиа для B2B-WC Converter v2.0.
Обрабатывает: изображения, видео, документы.
"""
import re
import os
from typing import Dict, Any, List, Optional
import logging
from urllib.parse import urlparse, unquote
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_handler import BaseHandler
from ..models import RawProduct
from ..config_manager import ConfigManager

logger = logging.getLogger(__name__)


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
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
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
        
        # Разбиваем строку на отдельные URL
        image_urls = self._split_image_urls(images_str)
        
        if not image_urls:
            return {"images": ""}
        
        # Получаем slug из названия товара для именования файлов
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
    
    def _split_image_urls(self, images_str: str) -> List[str]:
        """
        Разбивает строку с URL изображений на список.
        
        Args:
            images_str: Строка с URL через запятую
            
        Returns:
            Список URL изображений
        """
        if not images_str:
            return []
        
        # Разбиваем по запятой, убираем пробелы
        urls = [url.strip() for url in images_str.split(',') if url.strip()]
        
        # Фильтруем валидные URL
        valid_urls = []
        for url in urls:
            if self._is_valid_url(url):
                valid_urls.append(url)
            else:
                logger.warning(f"Невалидный URL изображения: {url}")
        
        return valid_urls
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Проверяет, является ли строка валидным URL.
        
        Args:
            url: Строка для проверки
            
        Returns:
            True если URL валиден
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _generate_slug_from_title(self, title: str) -> str:
        """
        Генерирует slug из названия товара.
        
        Args:
            title: Название товара
            
        Returns:
            slug
        """
        if not title:
            return ""
        
        # Простая транслитерация и очистка
        slug = title.lower()
        
        # Заменяем кириллицу на латиницу (базовые замены)
        cyr_to_lat = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        
        result = []
        for char in slug:
            if char in cyr_to_lat:
                result.append(cyr_to_lat[char])
            elif char.isalnum():
                result.append(char)
            elif char in [' ', '-', '_']:
                result.append('-')
        
        slug = ''.join(result)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        return slug[:100]  # Ограничиваем длину
    
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
            # Определяем расширение файла из URL
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)
            filename = os.path.basename(path)
            
            # Извлекаем расширение
            if '.' in filename:
                ext = filename.split('.')[-1].lower()
                # Ограничиваем расширение
                if len(ext) > 5:
                    ext = 'jpg'
            else:
                ext = 'jpg'
            
            # Создаем имя файла по шаблону
            safe_ns_code = re.sub(r'[^\w\-]', '_', ns_code)
            safe_slug = re.sub(r'[^\w\-]', '_', slug)
            
            local_filename = f"{safe_ns_code}-{safe_slug}-{index}.{ext}"
            local_path = self.download_dir / local_filename
            
            # Скачиваем файл
            timeout = self.config_manager.get_setting('processing.image_timeout', 30)
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Сохраняем файл
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.downloaded_images += 1
            logger.debug(f"Скачано изображение: {local_filename}")
            return local_path
            
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
        
        # Извлекаем YouTube ID
        youtube_id = self._extract_youtube_id(video_url)
        
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
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Извлекает YouTube ID из URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            YouTube ID или None
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/user\/.*#.*\/[a-zA-Z0-9_-]{11}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
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
            if doc_url:
                result[f"meta:{doc_type}_url"] = doc_url
        
        return result
    
    def cleanup(self) -> None:
        """
        Логирует статистику скачивания.
        """
        logger.info(f"MediaHandler: скачано {self.downloaded_images} изображений, "
                   f"ошибок: {self.failed_downloads}")
        super().cleanup()