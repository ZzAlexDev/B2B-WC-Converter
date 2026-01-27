"""
data_processors/xlsx_parser.py
Парсер для чтения и базовой обработки XLSX файлов
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
import logging
from datetime import datetime

# Настройка логгера
logger = logging.getLogger(__name__)


class XLSXParser:
    """
    Класс для парсинга XLSX файлов каталога товаров
    """
    
    def __init__(self, filepath: str):
        """
        Инициализация парсера
        
        Args:
            filepath: Путь к XLSX файлу
        """
        self.filepath = filepath
        self.dataframe = None
        self.processed_data = []
        self.stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'skipped_rows': 0,
            'errors': []
        }
        
        logger.info(f"Инициализирован парсер для файла: {filepath}")
    
    def read_file(self) -> bool:
        """
        Чтение XLSX файла в pandas DataFrame
        
        Returns:
            bool: Успешно ли прочитан файл
        """
        try:
            logger.info(f"Чтение файла: {self.filepath}")
            
            # Чтение Excel файла
            # engine='openpyxl' для поддержки .xlsx
            self.dataframe = pd.read_excel(
                self.filepath,
                engine='openpyxl',
                dtype=str  # Все данные как строки для сохранения форматов
            )
            
            # Заменяем NaN на пустые строки
            self.dataframe = self.dataframe.replace({np.nan: None})
            
            self.stats['total_rows'] = len(self.dataframe)
            logger.info(f"Файл прочитан успешно. Строк: {self.stats['total_rows']}")
            logger.info(f"Колонки: {list(self.dataframe.columns)}")
            
            return True
            
        except FileNotFoundError:
            error_msg = f"Файл не найден: {self.filepath}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Ошибка чтения файла: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False
    
    def validate_data(self) -> List[str]:
        """
        Базовая валидация данных
        
        Returns:
            List[str]: Список предупреждений
        """
        warnings = []
        
        if self.dataframe is None:
            warnings.append("DataFrame не загружен")
            return warnings
        
        # Проверяем наличие обязательных колонок
        required_columns = ['Наименование', 'Артикул', 'Цена']
        missing_columns = [col for col in required_columns if col not in self.dataframe.columns]
        
        if missing_columns:
            warnings.append(f"Отсутствуют обязательные колонки: {missing_columns}")
        
        # Проверяем пустые значения в обязательных полях
        for col in required_columns:
            if col in self.dataframe.columns:
                empty_count = self.dataframe[col].isnull().sum()
                if empty_count > 0:
                    warnings.append(f"Пустые значения в колонке '{col}': {empty_count}")
        
        # Проверяем уникальность артикулов
        if 'Артикул' in self.dataframe.columns:
            duplicates = self.dataframe['Артикул'].duplicated().sum()
            if duplicates > 0:
                warnings.append(f"Дублирующиеся артикулы: {duplicates}")
        
        logger.info(f"Валидация завершена. Предупреждений: {len(warnings)}")
        return warnings
    
    def clean_sku(self, sku: str) -> str:
        """
        Очистка SKU от лишних символов
        
        Args:
            sku: Исходный SKU
            
        Returns:
            str: Очищенный SKU
        """
        if not sku or pd.isna(sku):
            return ""
        
        sku_str = str(sku).strip()
        
        # Сначала удаляем все пробелы вокруг дефисов и слэшей
        sku_str = re.sub(r'\s*[/\-]\s*', '-', sku_str)
        
        # Заменяем / на - (если остались без пробелов)
        sku_str = sku_str.replace('/', '-')
        
        # Удаление лишних пробелов (теперь их не должно быть)
        sku_str = ' '.join(sku_str.split())
        
        # Замена нескольких дефисов подряд на один
        sku_str = re.sub(r'-+', '-', sku_str)
        
        return sku_str

    def clean_price(self, price_str: str) -> Optional[float]:
        """
        Очистка и преобразование цены
        
        Args:
            price_str: Строка с ценой (например, "14 990 руб.")
            
        Returns:
            Optional[float]: Числовое значение цены или None при ошибке
        """
        if not price_str or pd.isna(price_str):
            return None
        
        try:
            # Преобразуем в строку
            price_text = str(price_str).strip()
            
            # Удаляем текст "руб.", пробелы, валюту
            patterns_to_remove = ['руб.', 'рублей', 'RUB', '₽', '\xa0']
            for pattern in patterns_to_remove:
                price_text = price_text.replace(pattern, '')
            
            # Удаляем пробелы (разделители тысяч)
            price_text = price_text.replace(' ', '')
            
            # Заменяем запятую на точку для десятичных чисел
            price_text = price_text.replace(',', '.')
            
            # Удаляем все нецифровые символы кроме точки и минуса
            # Но нужно обработать случай с тысячными разделителями
            # Удаляем точки, которые не являются десятичными разделителями
            parts = price_text.split('.')
            if len(parts) > 2:
                # Если больше одной точки, это вероятно разделитель тысяч
                # Оставляем только последнюю точку как десятичный разделитель
                price_text = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Удаляем все нецифровые символы кроме точки и минуса
            price_text = re.sub(r'[^\d\.\-]', '', price_text)
            
            if not price_text or price_text == '.':
                return None
            
            # Преобразуем в число
            price = float(price_text)
            
            # Проверяем на разумные пределы
            if price < 0 or price > 10000000:  # 10 миллионов
                logger.warning(f"Подозрительная цена: {price}")
                return None
            
            return price
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Ошибка преобразования цены '{price_str}': {e}")
            return None

    
    def convert_category(self, category_str: str) -> str:
        """
        Преобразование категории в формат WooCommerce
        
        Args:
            category_str: Исходная строка категории
            
        Returns:
            str: Категория в формате WC
        """
        if not category_str or pd.isna(category_str):
            return ""
        
        category = str(category_str).strip()
        
        # Заменяем разделитель " - " на " > "
        category = category.replace(' - ', ' > ')
        
        # Удаляем дублирующиеся части
        parts = category.split(' > ')
        unique_parts = []
        
        for part in parts:
            part = part.strip()
            if part and part not in unique_parts:
                unique_parts.append(part)
        
        # Собираем обратно
        category = ' > '.join(unique_parts)
        
        return category
    
    def extract_product_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Извлечение и очистка данных товара из строки
        
        Args:
            row: Строка DataFrame
            
        Returns:
            Dict[str, Any]: Очищенные данные товара
        """
        product_data = {}
        
        try:
            # Базовые поля
            product_data['_raw'] = row.to_dict()  # Сохраняем исходные данные
            
            # Название товара
            product_data['name'] = str(row.get('Наименование', '')).strip() if pd.notna(row.get('Наименование')) else ''
            
            # SKU (артикул)
            raw_sku = row.get('Артикул', '')
            product_data['sku'] = self.clean_sku(raw_sku)
            
            # Бренд
            product_data['brand'] = str(row.get('Бренд', '')).strip() if pd.notna(row.get('Бренд')) else ''
            
            # Категория
            raw_category = row.get('Название категории', '')
            product_data['category'] = self.convert_category(raw_category)
            
            # Цена
            raw_price = row.get('Цена', '')
            product_data['price'] = self.clean_price(raw_price)
            
            # Характеристики (сырые)
            product_data['characteristics_raw'] = str(row.get('Характеристики', '')).strip() if pd.notna(row.get('Характеристики')) else ''
            
            # Изображения (сырые URL)
            raw_images = row.get('Изображение', '')
            product_data['images_raw'] = str(raw_images).strip() if pd.notna(raw_images) else ''
            
            # Описание (HTML)
            raw_description = row.get('Статья', '')
            product_data['description_raw'] = str(raw_description).strip() if pd.notna(raw_description) else ''
            
            # Документация и доп. поля
            product_data['documents'] = {}
            doc_fields = ['Чертежи', 'Сертификаты', 'Инструкции']
            for field in doc_fields:
                if field in row and pd.notna(row[field]):
                    product_data['documents'][field] = str(row[field]).strip()
            
            # Дополнительная информация
            product_data['additional_info'] = {}
            info_fields = ['НС-код', 'Штрих код', 'Эксклюзив']
            for field in info_fields:
                if field in row and pd.notna(row[field]):
                    product_data['additional_info'][field] = str(row[field]).strip()
            
            # Поля для игнорирования (сохраняем, но не обрабатываем)
            product_data['ignored_fields'] = {}
            ignore_fields = ['Сопут.товар', 'Аналоги', 'Видео', 'Промоматериалы']
            for field in ignore_fields:
                if field in row and pd.notna(row[field]):
                    product_data['ignored_fields'][field] = str(row[field]).strip()
            
            # Статус обработки
            product_data['_processing_status'] = {
                'has_errors': False,
                'errors': [],
                'warnings': []
            }
            
            # Валидация обязательных полей
            if not product_data['name']:
                product_data['_processing_status']['has_errors'] = True
                product_data['_processing_status']['errors'].append("Отсутствует название товара")
            
            if not product_data['sku']:
                product_data['_processing_status']['has_errors'] = True
                product_data['_processing_status']['errors'].append("Отсутствует SKU")
            
            if product_data['price'] is None:
                product_data['_processing_status']['has_errors'] = True
                product_data['_processing_status']['errors'].append("Некорректная цена")
            
            logger.debug(f"Обработан товар: {product_data['name'][:50]}...")
            
        except Exception as e:
            logger.error(f"Ошибка обработки строки: {e}")
            product_data['_processing_status'] = {
                'has_errors': True,
                'errors': [f"Ошибка обработки: {str(e)}"],
                'warnings': []
            }
        
        return product_data
    
    def process_all(self) -> bool:
        """
        Обработка всех строк файла
        
        Returns:
            bool: Успешно ли обработан файл
        """
        if self.dataframe is None:
            logger.error("DataFrame не загружен")
            return False
        
        logger.info(f"Начало обработки {len(self.dataframe)} товаров")
        self.processed_data = []
        
        for index, row in self.dataframe.iterrows():
            try:
                product_data = self.extract_product_data(row)
                
                if product_data['_processing_status']['has_errors']:
                    self.stats['skipped_rows'] += 1
                    logger.warning(f"Пропущен товар #{index}: {product_data.get('name', 'Без названия')}")
                    logger.warning(f"Причины: {product_data['_processing_status']['errors']}")
                else:
                    self.processed_data.append(product_data)
                    self.stats['processed_rows'] += 1
                    
            except Exception as e:
                self.stats['skipped_rows'] += 1
                self.stats['errors'].append(f"Строка {index}: {str(e)}")
                logger.error(f"Критическая ошибка в строке {index}: {e}")
        
        # Статистика
        success_rate = (self.stats['processed_rows'] / self.stats['total_rows'] * 100) if self.stats['total_rows'] > 0 else 0
        
        logger.info(f"Обработка завершена. Результаты:")
        logger.info(f"  Всего товаров: {self.stats['total_rows']}")
        logger.info(f"  Успешно обработано: {self.stats['processed_rows']}")
        logger.info(f"  Пропущено: {self.stats['skipped_rows']}")
        logger.info(f"  Успешность: {success_rate:.1f}%")
        logger.info(f"  Ошибок: {len(self.stats['errors'])}")
        
        return self.stats['processed_rows'] > 0
    
    def get_processed_data(self) -> List[Dict[str, Any]]:
        """
        Получить обработанные данные
        
        Returns:
            List[Dict[str, Any]]: Список обработанных товаров
        """
        return self.processed_data
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику обработки
        
        Returns:
            Dict[str, Any]: Статистика
        """
        return self.stats.copy()
    
    def save_sample_to_csv(self, output_path: str, sample_size: int = 10) -> bool:
        """
        Сохранение выборки обработанных данных в CSV для тестирования
        
        Args:
            output_path: Путь для сохранения CSV
            sample_size: Количество товаров в выборке
            
        Returns:
            bool: Успешно ли сохранено
        """
        try:
            if not self.processed_data:
                logger.warning("Нет обработанных данных для сохранения")
                return False
            
            # Берем выборку
            sample = self.processed_data[:min(sample_size, len(self.processed_data))]
            
            # Создаем упрощенный DataFrame для просмотра
            sample_data = []
            for product in sample:
                sample_data.append({
                    'Наименование': product.get('name', ''),
                    'SKU': product.get('sku', ''),
                    'Бренд': product.get('brand', ''),
                    'Категория': product.get('category', ''),
                    'Цена': product.get('price', ''),
                    'Характеристики (длина)': len(product.get('characteristics_raw', '')),
                    'Изображения (количество)': len(product.get('images_raw', '').split(',') if product.get('images_raw') else []),
                })
            
            df_sample = pd.DataFrame(sample_data)
            
            # Сохраняем
            df_sample.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"Выборка сохранена в: {output_path}")
            logger.info(f"Сохранено товаров: {len(sample)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения выборки: {e}")
            return False


# Функция для быстрого использования
def parse_xlsx_file(filepath: str, output_sample: Optional[str] = None) -> Tuple[List[Dict], Dict]:
    """
    Быстрая функция для парсинга XLSX файла
    
    Args:
        filepath: Путь к XLSX файлу
        output_sample: Путь для сохранения выборки (опционально)
        
    Returns:
        Tuple[List[Dict], Dict]: (обработанные данные, статистика)
    """
    parser = XLSXParser(filepath)
    
    # Чтение файла
    if not parser.read_file():
        return [], parser.get_stats()
    
    # Валидация
    warnings = parser.validate_data()
    if warnings:
        logger.warning(f"Предупреждения при валидации: {warnings}")
    
    # Обработка
    if not parser.process_all():
        logger.error("Ошибка обработки файла")
        return [], parser.get_stats()
    
    # Сохранение выборки если указан путь
    if output_sample:
        parser.save_sample_to_csv(output_sample)
    
    return parser.get_processed_data(), parser.get_stats()