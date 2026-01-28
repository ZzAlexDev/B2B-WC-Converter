"""
output_managers/csv_exporter.py
Экспортер данных в CSV формат WooCommerce
"""

import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# Настройка логгера
logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Класс для экспорта данных в CSV формат WooCommerce
    """
    
    def __init__(self, output_path: str = None):
        """
        Инициализация экспортера
        
        Args:
            output_path: Путь для сохранения CSV файла
        """
        # Загружаем настройки
        self._load_settings()
        
        # Переопределяем путь если передан
        if output_path:
            self.output_path = output_path
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # Статистика
        self.stats = {
            'total_products': 0,
            'exported': 0,
            'skipped': 0,
            'errors': []
        }
        
        logger.info(f"Инициализирован CSV экспортер. Выходной файл: {self.output_path}")
    
    def _load_settings(self):
        """
        Загрузка настроек из конфигурации
        """
        try:
            from config import settings
            from config import field_map
            
            self.output_path = settings.OUTPUT_FILE
            self.encoding = settings.FILE_ENCODING
            self.wc_defaults = field_map.get_wc_defaults()
            self.wc_attributes = field_map.get_wc_attributes()
            self.wc_output_fields = field_map.get_wc_output_fields_with_attributes()
            
            logger.debug("Настройки экспортера загружены успешно")
            
        except ImportError as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            # Значения по умолчанию
            self.output_path = "output/wc_products.csv"
            self.encoding = "utf-8"
            self.wc_defaults = {}
            self.wc_attributes = {}
            self.wc_output_fields = []
    
    def prepare_wc_data(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Подготовка данных товара для формата WooCommerce
        
        Args:
            product_data: Данные товара из обработчиков
            
        Returns:
            Dict[str, str]: Данные в формате WC
        """
        wc_row = {}
        
        try:
            # 1. Базовые поля
            wc_row['ID'] = ''  # Оставляем пустым, WC сам присвоит
            wc_row['post_title'] = product_data.get('name', '')
            wc_row['post_name'] = self._generate_slug(product_data.get('name', ''))
            wc_row['post_content'] = product_data.get('post_content', '')
            wc_row['post_excerpt'] = product_data.get('post_excerpt', '')
            
            # 2. Данные товара
            wc_row['sku'] = product_data.get('sku', '')
            wc_row['regular_price'] = str(product_data.get('price', ''))
            wc_row['sale_price'] = ''  # Цена со скидкой - оставляем пустой
            
            # 3. Наличие и склад
            wc_row['stock'] = ''  # Пусто = неограниченно
            wc_row['stock_status'] = 'instock'
            wc_row['backorders'] = 'no'
            wc_row['manage_stock'] = 'no'
            wc_row['sold_individually'] = 'no'
            
            # 4. Вес и габариты (из extracted_fields)
            extracted = product_data.get('extracted_fields', {})
            wc_row['weight'] = extracted.get('weight', '')
            wc_row['length'] = extracted.get('length', '')
            wc_row['width'] = extracted.get('width', '')
            wc_row['height'] = extracted.get('height', '')
            
            # 5. Налоги и видимость
            wc_row['tax_class'] = ''
            wc_row['tax_status'] = 'taxable'
            wc_row['visibility'] = 'visible'
            
            # 6. Таксономии
            wc_row['tax:product_cat'] = product_data.get('category', '')
            wc_row['tax:product_brand'] = product_data.get('brand', '')
            wc_row['tax:product_type'] = 'simple'
            wc_row['tax:product_tag'] = ''
            wc_row['tax:product_shipping_class'] = ''
            
            # 7. Изображения
            wc_row['images'] = product_data.get('wc_image_paths', '')
            
            # 8. Мета-поля
            # Штрих-код (берем первый если несколько)
            additional_info = product_data.get('additional_info', {})
            if 'Штрих код' in additional_info:
                barcodes = additional_info['Штрих код']
                # Берем первый штрих-код
                if barcodes:
                    barcode_list = [code.strip() for code in barcodes.split('/') if code.strip()]
                    if barcode_list:
                        wc_row['meta:_gtin'] = barcode_list[0]
            
            # 9. Атрибуты WooCommerce
            wc_attrs = product_data.get('wc_attributes', {})
            if 'attributes' in wc_attrs:
                for attr_slug, attr_value in wc_attrs['attributes'].items():
                    wc_row[f'attribute:{attr_slug}'] = attr_value
                    wc_row[f'attribute_data:{attr_slug}'] = '1:0|0'  # Видимый, не для вариаций
            
            # 10. Применяем дефолтные значения
            for key, value in self.wc_defaults.items():
                if key not in wc_row or not wc_row[key]:
                    wc_row[key] = value
            
            # 11. Очистка значений
            for key in wc_row:
                if wc_row[key] is None:
                    wc_row[key] = ''
                elif isinstance(wc_row[key], (int, float)):
                    wc_row[key] = str(wc_row[key])
            
            logger.debug(f"Подготовлен товар: {product_data.get('sku', 'N/A')}")
            
            return wc_row
            
        except Exception as e:
            error_msg = f"Ошибка подготовки товара {product_data.get('sku', 'N/A')}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return {}
    
    def _generate_slug(self, title: str) -> str:
        """
        Генерация slug из названия товара
        
        Args:
            title: Название товара
            
        Returns:
            str: Slug для post_name
        """
        if not title:
            return ""
        
        # Простая генерация slug
        import re
        
        # Приводим к нижнему регистру
        slug = title.lower().strip()
        
        # Заменяем пробелы и специальные символы на дефисы
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Удаляем дефисы в начале и конце
        slug = slug.strip('-')
        
        # Ограничиваем длину
        if len(slug) > 100:
            slug = slug[:100].rstrip('-')
        
        return slug
    
    def generate_csv(self, products_data: List[Dict[str, Any]]) -> bool:
        """
        Генерация CSV файла из данных товаров
        
        Args:
            products_data: Список данных товаров
            
        Returns:
            bool: Успешно ли сгенерирован CSV
        """
        self.stats['total_products'] = len(products_data)
        
        if not products_data:
            logger.error("Нет данных для экспорта")
            return False
        
        logger.info(f"Начало генерации CSV для {len(products_data)} товаров")
        
        try:
            # Подготавливаем все данные
            wc_rows = []
            for product in products_data:
                wc_row = self.prepare_wc_data(product)
                if wc_row:
                    wc_rows.append(wc_row)
                    self.stats['exported'] += 1
                else:
                    self.stats['skipped'] += 1
            
            if not wc_rows:
                logger.error("Не удалось подготовить ни одного товара для экспорта")
                return False
            
            # Определяем все заголовки
            all_headers = set()
            for row in wc_rows:
                all_headers.update(row.keys())
            
            # Сортируем заголовки для удобства
            headers = sorted(all_headers)
            
            # Записываем CSV
            with open(self.output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                # Настройки для WooCommerce
                if self.encoding == 'utf-8':
                    csvfile.write('\ufeff')  # BOM для Excel
                
                writer = csv.DictWriter(
                    csvfile, 
                    fieldnames=headers,
                    delimiter=',',
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL
                )
                
                writer.writeheader()
                writer.writerows(wc_rows)
            
            # Статистика
            logger.info(f"CSV успешно создан: {self.output_path}")
            logger.info(f"Статистика: всего {self.stats['total_products']}, "
                       f"экспортировано {self.stats['exported']}, "
                       f"пропущено {self.stats['skipped']}, "
                       f"ошибок {len(self.stats['errors'])}")
            
            # Сохраняем отчет об ошибках если есть
            if self.stats['errors']:
                error_report_path = self.output_path.replace('.csv', '_errors.txt')
                with open(error_report_path, 'w', encoding=self.encoding) as f:
                    f.write(f"Отчет об ошибках экспорта CSV\n")
                    f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Всего товаров: {self.stats['total_products']}\n")
                    f.write(f"Экспортировано: {self.stats['exported']}\n")
                    f.write(f"Пропущено: {self.stats['skipped']}\n")
                    f.write(f"Ошибок: {len(self.stats['errors'])}\n\n")
                    
                    for i, error in enumerate(self.stats['errors'], 1):
                        f.write(f"{i}. {error}\n")
                
                logger.info(f"Отчет об ошибках сохранен: {error_report_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Критическая ошибка генерации CSV: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики экспорта
        
        Returns:
            Dict[str, Any]: Статистика
        """
        return self.stats.copy()


# Функции для быстрого использования
def export_to_csv(products_data: List[Dict[str, Any]], output_path: str = None) -> bool:
    """
    Быстрый экспорт данных в CSV
    
    Args:
        products_data: Список данных товаров
        output_path: Путь для сохранения CSV
        
    Returns:
        bool: Успешно ли экспортировано
    """
    exporter = CSVExporter(output_path)
    return exporter.generate_csv(products_data)