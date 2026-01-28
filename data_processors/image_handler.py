"""
data_processors/image_handler.py
Обработчик для скачивания и переименования изображений товаров
"""

import os
import re
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, unquote
from pathlib import Path
import time
from datetime import datetime

# Настройка логгера
logger = logging.getLogger(__name__)


class ImageHandler:
    """
    Класс для скачивания и обработки изображений товаров
    """
    
    def __init__(self, download_dir: str = None, max_workers: int = 3):
        """
        Инициализация обработчика изображений
        
        Args:
            download_dir: Директория для сохранения изображений
            max_workers: Максимальное количество одновременных загрузок
        """
        # Загружаем настройки
        self._load_settings()
        
        # Переопределяем настройки если переданы
        if download_dir:
            self.download_dir = download_dir
        
        self.max_workers = max_workers
        
        # Создаем директорию если не существует
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Статистика
        self.stats = {
            'total_images': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'total_size_bytes': 0,
            'start_time': None,
            'end_time': None,
        }
        
        # Настройки запросов
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
        # Таймауты (секунды)
        self.timeout = 30
        self.max_retries = 2
        
        logger.info(f"Инициализирован обработчик изображений. Директория: {self.download_dir}")
    
    def _load_settings(self):
        """
        Загрузка настроек из конфигурации
        """
        try:
            from config import settings
            
            self.download_dir = settings.IMAGES_DOWNLOAD_DIR
            self.wc_images_path = settings.IMAGES_CSV_PATH
            
            logger.debug("Настройки изображений загружены успешно")
            
        except ImportError as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            # Значения по умолчанию
            self.download_dir = "downloads/images"
            self.wc_images_path = "/wp-content/uploads/products/"
    
    def slugify_text(self, text: str) -> str:
        """
        Преобразование текста в slug для имени файла
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Slug (только латинские буквы, цифры, дефисы)
        """
        if not text:
            return ""
        
        try:
            # Транслитерация кириллицы в латиницу
            # Для простоты сначала базовое преобразование
            text = text.strip().lower()
            
            # Заменяем русские буквы на латинские аналоги
            cyrillic_map = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
                'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
                'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
                'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
                'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
                'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
                'э': 'e', 'ю': 'yu', 'я': 'ya',
            }
            
            # Простая транслитерация
            transliterated = []
            for char in text:
                if char in cyrillic_map:
                    transliterated.append(cyrillic_map[char])
                else:
                    transliterated.append(char)
            
            text = ''.join(transliterated)
            
            # Заменяем пробелы и специальные символы на дефисы
            text = re.sub(r'[^\w\s-]', '', text)
            text = re.sub(r'[-\s]+', '-', text)
            
            # Удаляем дефисы в начале и конце
            text = text.strip('-')
            
            # Ограничиваем длину
            if len(text) > 100:
                text = text[:100].rstrip('-')
            
            return text
            
        except Exception as e:
            logger.error(f"Ошибка slugify текста '{text[:50]}...': {e}")
            # Возвращаем безопасное значение
            return re.sub(r'[^\w-]', '', text.lower().replace(' ', '-'))[:50]
    
    def get_extension_from_url(self, url: str) -> str:
        """
        Получение расширения файла из URL
        
        Args:
            url: URL изображения
            
        Returns:
            str: Расширение файла (.jpg, .png и т.д.)
        """
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            
            # Извлекаем расширение
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            
            # Если нет расширения или оно слишком длинное
            if not ext or len(ext) > 6:
                # Пытаемся определить по content-type или используем .jpg по умолчанию
                return '.jpg'
            
            # Приводим к нижнему регистру
            ext = ext.lower()
            
            # Проверяем допустимые расширения
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
            for valid_ext in valid_extensions:
                if ext.startswith(valid_ext):
                    return valid_ext
            
            # Если не нашли допустимое расширение
            return '.jpg'
            
        except Exception as e:
            logger.warning(f"Не удалось определить расширение для {url[:50]}...: {e}")
            return '.jpg'
    
    def generate_filename(self, sku: str, product_name: str, index: int, url: str) -> str:
        """
        Генерация имени файла по шаблону
        
        Args:
            sku: Артикул товара
            product_name: Название товара
            index: Порядковый номер изображения
            url: URL изображения (для определения расширения)
            
        Returns:
            str: Имя файла
        """
        # Очищаем SKU
        clean_sku = re.sub(r'[^\w-]', '', sku)
        
        # Создаем slug из названия товара
        slug_title = self.slugify_text(product_name)
        
        # Получаем расширение
        extension = self.get_extension_from_url(url)
        
        # Формируем имя файла
        filename = f"{clean_sku}-{slug_title}-{index:02d}{extension}"
        
        # Удаляем возможные двойные дефисы
        filename = re.sub(r'-+', '-', filename)
        
        # Убеждаемся что имя не слишком длинное
        if len(filename) > 150:
            # Сокращаем часть с названием товара
            max_sku_part = 30
            max_title_part = 100
            max_total = 150
            
            sku_part = clean_sku[:max_sku_part]
            title_part = slug_title[:max_title_part]
            
            filename = f"{sku_part}-{title_part}-{index:02d}{extension}"
            filename = filename[:max_total]
        
        return filename
    
    def download_single_image(self, url: str, filepath: str) -> bool:
        """
        Скачивание одного изображения
        
        Args:
            url: URL изображения
            filepath: Полный путь для сохранения
            
        Returns:
            bool: Успешно ли скачано
        """
        if not url or not url.strip():
            logger.warning(f"Пустой URL, пропускаем")
            return False
        
        url = url.strip()
        
        # Пропускаем если файл уже существует
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size > 1024:  # Если файл больше 1KB, считаем валидным
                logger.debug(f"Изображение уже существует: {os.path.basename(filepath)}")
                self.stats['skipped'] += 1
                return True
            else:
                logger.debug(f"Существующий файл слишком мал, перезаписываем: {os.path.basename(filepath)}")
        
        try:
            logger.debug(f"Скачивание: {url[:60]}...")
            
            # Загружаем с таймаутами
            response = self.session.get(
                url, 
                timeout=self.timeout,
                stream=True
            )
            
            # Проверяем статус
            response.raise_for_status()
            
            # Проверяем content-type
            content_type = response.headers.get('content-type', '').lower()
            if 'image' not in content_type and 'octet-stream' not in content_type:
                logger.warning(f"Не image content-type: {content_type} для {url[:50]}...")
                # Но продолжаем, иногда серверы отдают без правильного content-type
            
            # Сохраняем файл
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Проверяем что файл не пустой
            file_size = os.path.getsize(filepath)
            if file_size < 1024:  # Меньше 1KB
                logger.warning(f"Скачанный файл слишком мал ({file_size} байт): {os.path.basename(filepath)}")
                os.remove(filepath)
                return False
            
            self.stats['downloaded'] += 1
            self.stats['total_size_bytes'] += file_size
            
            logger.debug(f"Успешно скачано: {os.path.basename(filepath)} ({file_size // 1024} KB)")
            return True
            
        except requests.exceptions.Timeout:
            logger.warning(f"Таймаут при скачивании: {url[:50]}...")
            self.stats['failed'] += 1
            return False
            
        except requests.exceptions.ConnectionError:
            logger.warning(f"Ошибка соединения: {url[:50]}...")
            self.stats['failed'] += 1
            return False
            
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP ошибка {e.response.status_code}: {url[:50]}...")
            self.stats['failed'] += 1
            return False
            
        except Exception as e:
            logger.error(f"Ошибка скачивания {url[:50]}...: {e}")
            self.stats['failed'] += 1
            return False
    
    def parse_image_urls(self, images_str: str) -> List[str]:
        """
        Парсинг строки с URL изображений
        
        Args:
            images_str: Строка с URL через запятую
            
        Returns:
            List[str]: Список URL
        """
        if not images_str:
            return []
        
        urls = []
        
        try:
            # Разделяем по запятой
            raw_urls = [url.strip() for url in images_str.split(',') if url.strip()]
            
            # Фильтруем валидные URL
            for url in raw_urls:
                # Проверяем что это похоже на URL
                if url.startswith(('http://', 'https://')):
                    urls.append(url)
                else:
                    logger.warning(f"Некорректный URL, пропускаем: {url[:50]}...")
        
        except Exception as e:
            logger.error(f"Ошибка парсинга URL изображений: {e}")
        
        return urls
    
    def process_product_images(self, sku: str, product_name: str, images_str: str, 
                              max_images: int = 10) -> Dict[str, Any]:
        """
        Обработка всех изображений товара
        
        Args:
            sku: Артикул товара
            product_name: Название товара
            images_str: Строка с URL изображений
            max_images: Максимальное количество изображений для скачивания
            
        Returns:
            Dict[str, Any]: Результаты обработки
        """
        result = {
            'success': False,
            'downloaded_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'filenames': [],
            'wc_paths': [],
            'errors': []
        }
        
        try:
            # Парсим URL
            urls = self.parse_image_urls(images_str)
            
            if not urls:
                result['errors'].append("Нет URL изображений")
                logger.info(f"Товар {sku}: нет изображений для скачивания")
                return result
            
            # Ограничиваем количество
            urls = urls[:max_images]
            
            logger.info(f"Товар {sku}: начинаю скачивание {len(urls)} изображений")
            
            # Обрабатываем каждое изображение
            for i, url in enumerate(urls, 1):
                try:
                    # Генерируем имя файла
                    filename = self.generate_filename(sku, product_name, i, url)
                    filepath = os.path.join(self.download_dir, filename)
                    
                    # Скачиваем
                    success = self.download_single_image(url, filepath)
                    
                    if success:
                        result['downloaded_count'] += 1
                        result['filenames'].append(filename)
                        result['wc_paths'].append(f"{self.wc_images_path}{filename}")
                    else:
                        result['failed_count'] += 1
                        result['errors'].append(f"Ошибка скачивания изображения {i}")
                        
                except Exception as e:
                    result['failed_count'] += 1
                    result['errors'].append(f"Ошибка обработки изображения {i}: {str(e)}")
                    logger.error(f"Ошибка обработки изображения {i} для товара {sku}: {e}")
            
            # Обновляем статистику
            self.stats['total_images'] += len(urls)
            
            # Результат
            result['success'] = result['downloaded_count'] > 0
            
            if result['success']:
                logger.info(f"Товар {sku}: успешно скачано {result['downloaded_count']}/{len(urls)} изображений")
            else:
                logger.warning(f"Товар {sku}: не удалось скачать ни одного изображения")
            
            return result
            
        except Exception as e:
            error_msg = f"Критическая ошибка обработки изображений товара {sku}: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def process_batch(self, products_data: List[Dict[str, Any]], max_images_per_product: int = 10) -> List[Dict[str, Any]]:
        """
        Обработка изображений для партии товаров
        
        Args:
            products_data: Список данных товаров
            max_images_per_product: Максимум изображений на товар
            
        Returns:
            List[Dict[str, Any]]: Товары с добавленной информацией об изображениях
        """
        self.stats['start_time'] = datetime.now()
        
        logger.info(f"Начало обработки изображений для {len(products_data)} товаров")
        
        processed_products = []
        
        for i, product_data in enumerate(products_data, 1):
            try:
                sku = product_data.get('sku', f"unknown_{i}")
                name = product_data.get('name', '')
                images_str = product_data.get('images_raw', '')
                
                logger.debug(f"Обработка товара {i}/{len(products_data)}: {sku}")
                
                # Обрабатываем изображения
                images_result = self.process_product_images(
                    sku=sku,
                    product_name=name,
                    images_str=images_str,
                    max_images=max_images_per_product
                )
                
                # Добавляем результаты к данным товара
                enhanced_product = product_data.copy()
                enhanced_product['images_processing'] = images_result
                
                # Формируем строку путей для WC CSV
                if images_result['wc_paths']:
                    enhanced_product['wc_image_paths'] = ' | '.join(images_result['wc_paths'])
                else:
                    enhanced_product['wc_image_paths'] = ''
                
                processed_products.append(enhanced_product)
                
                # Периодический лог
                if i % 10 == 0:
                    logger.info(f"Обработано {i}/{len(products_data)} товаров")
                    
            except Exception as e:
                logger.error(f"Ошибка обработки товара {i}: {e}")
                # Добавляем товар без информации об изображениях
                product_data['images_processing'] = {
                    'success': False,
                    'errors': [str(e)]
                }
                product_data['wc_image_paths'] = ''
                processed_products.append(product_data)
        
        self.stats['end_time'] = datetime.now()
        
        # Итоговая статистика
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        logger.info(f"Обработка изображений завершена за {duration:.1f} секунд")
        logger.info(f"Статистика: всего {self.stats['total_images']}, "
                   f"скачано {self.stats['downloaded']}, "
                   f"ошибок {self.stats['failed']}, "
                   f"пропущено {self.stats['skipped']}")
        
        return processed_products
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики обработки
        
        Returns:
            Dict[str, Any]: Статистика
        """
        stats = self.stats.copy()
        
        # Добавляем вычисляемые поля
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['duration_seconds'] = duration
            
            if duration > 0:
                stats['images_per_second'] = stats['total_images'] / duration
            else:
                stats['images_per_second'] = 0
        
        # Размер в мегабайтах
        stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024) if stats['total_size_bytes'] > 0 else 0
        
        return stats


# Функции для быстрого использования
def download_product_images(sku: str, product_name: str, images_str: str, 
                           download_dir: str = None) -> Dict[str, Any]:
    """
    Быстрое скачивание изображений товара
    
    Args:
        sku: Артикул товара
        product_name: Название товара
        images_str: Строка с URL изображений
        download_dir: Директория для сохранения
        
    Returns:
        Dict[str, Any]: Результаты обработки
    """
    handler = ImageHandler(download_dir)
    return handler.process_product_images(sku, product_name, images_str)


def process_images_batch(products_data: List[Dict[str, Any]], 
                        download_dir: str = None) -> List[Dict[str, Any]]:
    """
    Быстрая обработка изображений для партии товаров
    
    Args:
        products_data: Список данных товаров
        download_dir: Директория для сохранения
        
    Returns:
        List[Dict[str, Any]]: Товары с добавленной информацией об изображениях
    """
    handler = ImageHandler(download_dir)
    return handler.process_batch(products_data)