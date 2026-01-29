"""
Парсер для колонки "Изображение"
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests

from .base_parser import BaseParser, ParseResult
from src.utils.file_utils import download_file, clean_filename, ensure_dir_exists
from src.utils.logger import log_error, log_info, log_warning


class ImagesParser(BaseParser):
    """
    Парсер для колонки "Изображение"
    
    Обрабатывает:
    1. Разбор строки с URL изображений (через запятую)
    2. Скачивание изображений
    3. Переименование по шаблону: {sku}-{slug}-{номер}.{расширение}
    4. Форматирование для WC
    5. Генерация структуры папок по категории
    """
    
    def __init__(
        self, 
        download_path: str = "data/downloads/images",
        max_images: int = 5,
        skip_download: bool = False
    ):
        """
        Инициализация парсера изображений
        
        Args:
            download_path: Путь для скачивания изображений
            max_images: Максимальное количество скачиваемых изображений
            skip_download: Пропустить скачивание (только обработка URL)
        """
        super().__init__(column_name="Изображение")
        self.download_path = download_path
        self.max_images = max_images
        self.skip_download = skip_download
        
        # Поддерживаемые расширения изображений
        self.supported_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.JPG', '.JPEG', '.PNG', '.GIF', '.BMP', '.WEBP'
        }
    
    def parse(
        self, 
        value: str,
        sku: str,
        slug: str,
        category_hierarchy: List[str],
        product_name: str
    ) -> ParseResult:
        """
        Парсинг изображений
        
        Args:
            value: Строка с URL изображений (через запятую)
            sku: SKU товара (для именования файлов)
            slug: Slug товара (для именования файлов)
            category_hierarchy: Иерархия категорий (для структуры папок)
            product_name: Название товара (для alt/title атрибутов)
        
        Returns:
            ParseResult с данными:
            {
                "urls": ["url1", "url2"],  # Оригинальные URL
                "local_paths": ["path1", "path2"],  # Локальные пути
                "wc_paths": ["wc_path1", "wc_path2"],  # Пути для WC
                "wc_format": "URL1 ! alt: ! title: | URL2 ...",  # Формат для WC
                "main_image": "path/to/main.jpg",  # Главное изображение
                "gallery_images": ["path1", "path2"],  # Галерея
                "success_count": 3,  # Успешно обработано
                "failed_count": 1,   # Не удалось обработать
            }
        """
        errors = []
        warnings = []
        
        # Очищаем значение
        cleaned_value = self.clean_value(value)
        
        # Если нет изображений
        if not cleaned_value:
            warnings.append("Изображения не указаны")
            return self.create_result(
                data=self._create_empty_result(),
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        
        try:
            # 1. Разбираем URL изображений
            image_urls = self._parse_image_urls(cleaned_value)
            
            if not image_urls:
                errors.append("Не удалось извлечь URL изображений")
                return self.create_result(
                    data=self._create_empty_result(),
                    original_value=value,
                    errors=errors,
                    warnings=warnings
                )
            
            # Ограничиваем количество изображений
            if len(image_urls) > self.max_images:
                warnings.append(f"Ограничение изображений: {len(image_urls)} > {self.max_images}")
                image_urls = image_urls[:self.max_images]
            
            # 2. Подготавливаем структуру папок
            category_path = self._create_category_path(category_hierarchy)
            full_download_path = os.path.join(self.download_path, category_path)
            
            # 3. Скачиваем и обрабатываем изображения
            processed_images = []
            failed_urls = []
            
            for idx, url in enumerate(image_urls, 1):
                result = self._process_single_image(
                    url=url,
                    index=idx,
                    sku=sku,
                    slug=slug,
                    download_path=full_download_path,
                    product_name=product_name
                )
                
                if result["success"]:
                    processed_images.append(result)
                else:
                    failed_urls.append(url)
                    log_warning(f"Не удалось обработать изображение {url}: {result.get('error', 'Unknown error')}")
            
            # 4. Форматируем для WooCommerce
            wc_format = self._format_for_wc(processed_images, product_name)
            
            # 5. Подготавливаем данные
            data = {
                "urls": image_urls,
                "local_paths": [img["local_path"] for img in processed_images if img["local_path"]],
                "wc_paths": [img["wc_path"] for img in processed_images if img["wc_path"]],
                "wc_format": wc_format,
                "main_image": processed_images[0]["wc_path"] if processed_images else "",
                "gallery_images": [img["wc_path"] for img in processed_images[1:] if img["wc_path"]],
                "success_count": len(processed_images),
                "failed_count": len(failed_urls),
                "failed_urls": failed_urls,
                "category_path": category_path,
                "download_path": full_download_path,
            }
            
            # Логирование результатов
            log_info(f"Обработано изображений: {len(processed_images)} успешно, "
                    f"{len(failed_urls)} с ошибками")
            
            if failed_urls:
                warnings.append(f"Не удалось обработать {len(failed_urls)} изображений")
            
            return self.create_result(
                data=data,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Ошибка при обработке изображений: {str(e)}")
            self.logger.error(f"Ошибка обработки изображений: {e}", exc_info=True)
            return self.create_result(
                data=self._create_empty_result(),
                original_value=value,
                errors=errors,
                warnings=warnings
            )
    
    def _parse_image_urls(self, image_str: str) -> List[str]:
        """
        Разбор строки с URL изображений
        
        Args:
            image_str: Строка с URL через запятую
        
        Returns:
            Список URL
        """
        if not image_str:
            return []
        
        # Разделяем по запятой
        urls = [url.strip() for url in image_str.split(',') if url.strip()]
        
        # Фильтруем пустые и невалидные URL
        valid_urls = []
        for url in urls:
            if self._is_valid_image_url(url):
                valid_urls.append(url)
            else:
                log_warning(f"Невалидный URL изображения: {url}")
        
        return valid_urls
    
    def _is_valid_image_url(self, url: str) -> bool:
        """
        Проверка валидности URL изображения
        
        Args:
            url: URL для проверки
        
        Returns:
            True если URL валидный
        """
        if not url or not url.strip():
            return False
        
        # Проверяем что это HTTP/HTTPS URL
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Проверяем расширение файла
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Проверяем расширение
        for ext in self.supported_extensions:
            if path.endswith(ext.lower()):
                return True
        
        # Если нет явного расширения, все равно считаем валидным
        # (могут быть URL с параметрами)
        return True
    
    def _create_category_path(self, category_hierarchy: List[str]) -> str:
        """
        Создание пути папки на основе категории
        
        Args:
            category_hierarchy: Иерархия категорий
        
        Returns:
            Путь для сохранения изображений
        """
        if not category_hierarchy:
            return "uncategorized"
        
        # Берем последнюю категорию (самую конкретную)
        category = category_hierarchy[-1] if category_hierarchy else "uncategorized"
        
        # Очищаем название категории для использования в пути
        # Транслитерация и замена недопустимых символов
        import cyrtranslit
        
        try:
            category_slug = cyrtranslit.to_latin(category, 'ru')
        except:
            category_slug = category
        
        # Очищаем от недопустимых символов
        category_slug = re.sub(r'[^\w\s-]', '', category_slug)
        category_slug = re.sub(r'[-\s]+', '-', category_slug)
        category_slug = category_slug.strip('-').lower()
        
        # Ограничиваем длину
        if len(category_slug) > 50:
            category_slug = category_slug[:50]
        
        return category_slug
    
    def _process_single_image(
        self,
        url: str,
        index: int,
        sku: str,
        slug: str,
        download_path: str,
        product_name: str
    ) -> Dict[str, Any]:
        """
        Обработка одного изображения
        
        Args:
            url: URL изображения
            index: Порядковый номер (1, 2, 3...)
            sku: SKU товара
            slug: Slug товара
            download_path: Путь для скачивания
            product_name: Название товара
        
        Returns:
            Результат обработки
        """
        result = {
            "url": url,
            "success": False,
            "error": "",
            "local_path": "",
            "wc_path": "",
            "filename": "",
        }
        
        try:
            # 1. Получаем расширение файла
            extension = self._get_file_extension(url)
            if not extension:
                result["error"] = "Не удалось определить расширение файла"
                return result
            
            # 2. Генерируем имя файла
            filename = self._generate_filename(sku, slug, index, extension)
            
            # 3. Полный путь для сохранения
            local_path = os.path.join(download_path, filename)
            
            # 4. Скачиваем изображение (если не пропущено)
            if not self.skip_download:
                # Создаем директорию если не существует
                ensure_dir_exists(download_path)
                
                # Скачиваем файл
                success = download_file(url, local_path)
                if not success:
                    result["error"] = "Не удалось скачать изображение"
                    return result
                
                log_info(f"Скачано изображение {index}: {filename}")
            else:
                # Только имитация пути
                local_path = os.path.join(download_path, filename)
                log_info(f"Пропущено скачивание изображения {index}: {filename}")
            
            # 5. Генерируем путь для WC
            # Предполагаем что изображения будут загружены на сайт
            # по аналогичной структуре
            wc_path = f"https://ваш-сайт.ru/wp-content/uploads/2026/02/images/{self._create_category_path([slug])}/{filename}"
            
            result.update({
                "success": True,
                "local_path": local_path,
                "wc_path": wc_path,
                "filename": filename,
                "extension": extension,
                "index": index,
            })
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            log_error(f"Ошибка обработки изображения {url}: {e}")
            return result
    
    def _get_file_extension(self, url: str) -> Optional[str]:
        """
        Получение расширения файла из URL
        
        Args:
            url: URL изображения
        
        Returns:
            Расширение файла (с точкой) или None
        """
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # Извлекаем расширение
            _, ext = os.path.splitext(path)
            
            # Нормализуем расширение
            if ext:
                ext = ext.lower()
                # Проверяем что это поддерживаемое расширение
                if ext in self.supported_extensions:
                    return ext
                # Если расширение в верхнем регистре
                elif ext.upper() in self.supported_extensions:
                    return ext.lower()
            
            # Если не нашли расширение, используем .jpg по умолчанию
            return ".jpg"
            
        except Exception:
            return ".jpg"  # Fallback
    
    def _generate_filename(self, sku: str, slug: str, index: int, extension: str) -> str:
        """
        Генерация имени файла
        
        Args:
            sku: SKU товара
            slug: Slug товара
            index: Порядковый номер
            extension: Расширение файла
        
        Returns:
            Имя файла
        """
        # Очищаем SKU и slug от недопустимых символов
        safe_sku = re.sub(r'[^\w\-]', '_', sku)
        safe_slug = re.sub(r'[^\w\-]', '_', slug)
        
        # Ограничиваем длину
        safe_sku = safe_sku[:30]
        safe_slug = safe_slug[:50]
        
        # Формируем имя файла
        filename = f"{safe_sku}-{safe_slug}-{index}{extension}"
        
        # Очищаем от множественных подчеркиваний
        filename = re.sub(r'_+', '_', filename)
        
        return filename.lower()
    
    def _format_for_wc(self, images: List[Dict[str, Any]], product_name: str) -> str:
        """
        Форматирование изображений для WooCommerce
        
        Args:
            images: Список обработанных изображений
            product_name: Название товара
        
        Returns:
            Строка в формате WC
        """
        if not images:
            return ""
        
        wc_parts = []
        
        for img in images:
            if img.get("wc_path"):
                # Формат: URL ! alt: текст ! title: текст
                alt_text = product_name[:100]  # Ограничиваем длину alt
                title_text = product_name[:100]  # Ограничиваем длину title
                
                wc_part = f"{img['wc_path']} ! alt: {alt_text} ! title: {title_text}"
                wc_parts.append(wc_part)
        
        return " | ".join(wc_parts)
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Создание пустого результата"""
        return {
            "urls": [],
            "local_paths": [],
            "wc_paths": [],
            "wc_format": "",
            "main_image": "",
            "gallery_images": [],
            "success_count": 0,
            "failed_count": 0,
            "failed_urls": [],
            "category_path": "",
            "download_path": "",
        }