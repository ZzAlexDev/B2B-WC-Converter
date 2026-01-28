"""
output_managers/csv_exporter.py
Экспортер данных в CSV формат WooCommerce с разделителем ;
"""

import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# Импорты из наших модулей
from config.wc_fields_config import (
    get_wc_fields, 
    get_wc_default_row, 
    generate_seo_for_product,
    generate_slug_from_title,
    clean_images_for_wc
)
from utils.date_generator import get_next_product_date, reset_date_generator

# Настройка логгера
logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Класс для экспорта данных в CSV формат WooCommerce с разделителем ;
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
        
        # Сбрасываем генератор дат при каждой новой экспорте
        reset_date_generator()
        
        # Получаем список полей из конфигурации
        self.wc_fields = get_wc_fields()
        
        # Получаем строку с дефолтными значениями
        self.default_row = get_wc_default_row()
        
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
        logger.info(f"Используется {len(self.wc_fields)} полей")
        logger.info(f"Разделитель CSV: ';'")
    
    def _load_settings(self):
        """
        Загрузка настроек из конфигурации
        """
        try:
            from config import settings
            self.output_path = settings.OUTPUT_FILE
            self.encoding = settings.FILE_ENCODING
            logger.debug("Настройки экспортера загружены успешно")
        except ImportError as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            # Значения по умолчанию
            self.output_path = "output/wc_products.csv"
            self.encoding = "utf-8"
    
    def prepare_wc_data(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Подготовка данных товара для формата WooCommerce
        
        Args:
            product_data: Полные данные товара из DataAggregator
            
        Returns:
            Dict[str, str]: Данные в формате WC для всех 138 полей
        """
        wc_row = self.default_row.copy()  # Начинаем с дефолтных значений
        
        try:
            # 1. Базовые данные товара
            product_name = product_data.get('name', '')
            sku = product_data.get('sku', '')
            price = product_data.get('price')
            
            # 2. Основные поля WooCommerce
            wc_row['post_title'] = product_name
            wc_row['post_name'] = generate_slug_from_title(product_name)
            wc_row['post_content'] = product_data.get('post_content', '')
            wc_row['post_excerpt'] = product_data.get('post_excerpt', '')
            
            # 3. SKU и цена
            wc_row['sku'] = sku
            if price is not None:
                wc_row['regular_price'] = str(price)
            
            # 4. Дата публикации (генерируем последовательные даты)
            wc_row['post_date'] = get_next_product_date()
            
            # 5. Изображения (очищаем, оставляем только URL через |)
            if 'wc_image_paths' in product_data:
                wc_row['images'] = product_data['wc_image_paths']
            elif 'images_raw' in product_data:
                wc_row['images'] = clean_images_for_wc(product_data['images_raw'])
            
            # 6. Вес и габариты из extracted_fields
            extracted = product_data.get('extracted_fields', {})
            wc_row['weight'] = extracted.get('weight', '')
            wc_row['length'] = extracted.get('length', '')
            wc_row['width'] = extracted.get('width', '')
            wc_row['height'] = extracted.get('height', '')
            
            # 7. Категория и бренд
            wc_row['tax:product_cat'] = product_data.get('category', '')
            wc_row['tax:product_brand'] = product_data.get('brand', '')
            
            # 8. Атрибуты WooCommerce
            wc_attrs = product_data.get('wc_attributes', {})
            if wc_attrs and 'attributes' in wc_attrs:
                for attr_slug, attr_value in wc_attrs['attributes'].items():
                    # Добавляем только если это поле есть в нашем списке
                    attribute_field = f'attribute:{attr_slug}'
                    if attribute_field in self.wc_fields:
                        wc_row[attribute_field] = attr_value
            
            # 9. Генерация SEO полей Yoast
            seo_fields = generate_seo_for_product(
                product_name=product_name,
                description=product_data.get('post_content', ''),
                sku=sku
            )
            
            for seo_field, seo_value in seo_fields.items():
                if seo_field in self.wc_fields:  # <-- ПРОВЕРКА!
                    wc_row[seo_field] = seo_value
            
            # 10. Дополнительная информация (штрих-код)
            # ПРОВЕРЯЕМ ЧТО ПОЛЕ ЕСТЬ В СПИСКЕ!
            additional_info = product_data.get('additional_info', {})
            if 'Штрих код' in additional_info and 'meta:_gtin' in self.wc_fields:  # <-- ИСПРАВЛЕНИЕ ЗДЕСЬ
                barcodes = additional_info['Штрих код']
                if barcodes:
                    # Берем первый штрих-код
                    barcode_list = [code.strip() for code in barcodes.split('/') if code.strip()]
                    if barcode_list:
                        wc_row['meta:_gtin'] = barcode_list[0]
            
            # 11. Удаляем поля, которых нет в списке wc_fields
            # Это важно! CSV writer требует точного соответствия полей
            fields_to_remove = [field for field in wc_row.keys() if field not in self.wc_fields]
            for field in fields_to_remove:
                del wc_row[field]
            
            # 12. Приводим все значения к строковому типу
            for key in wc_row:
                if wc_row[key] is None:
                    wc_row[key] = ''
                elif not isinstance(wc_row[key], str):
                    wc_row[key] = str(wc_row[key])
            
            logger.debug(f"Подготовлен товар: {sku} - {product_name[:50]}...")
            return wc_row
            
        except Exception as e:
            error_msg = f"Ошибка подготовки товара {product_data.get('sku', 'N/A')}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return {}
    
    def validate_wc_row(self, wc_row: Dict[str, str]) -> Dict[str, Any]:
        """
        Валидация строки данных WooCommerce
        
        Args:
            wc_row: Строка данных для проверки
            
        Returns:
            Dict[str, Any]: Результаты валидации
        """
        validation = {
            'is_valid': False,
            'missing_required': [],
            'warnings': [],
            'fields_count': 0,
            'empty_fields': 0
        }
        
        try:
            # Обязательные поля для WooCommerce
            required_fields = ['post_title', 'sku', 'regular_price', 'post_status']
            missing_required = [field for field in required_fields if not wc_row.get(field)]
            
            if missing_required:
                validation['missing_required'] = missing_required
                validation['is_valid'] = False
                return validation
            
            # Подсчет статистики
            validation['fields_count'] = len(wc_row)
            validation['empty_fields'] = sum(1 for value in wc_row.values() if not value)
            
            # Проверки значений
            if not wc_row.get('post_content'):
                validation['warnings'].append("Отсутствует описание товара (post_content)")
            
            if not wc_row.get('images'):
                validation['warnings'].append("Отсутствуют изображения товара")
            
            if not wc_row.get('tax:product_cat'):
                validation['warnings'].append("Отсутствует категория товара")
            
            # Проверка цены
            try:
                price = float(wc_row.get('regular_price', '0'))
                if price <= 0:
                    validation['warnings'].append(f"Цена должна быть больше 0: {price}")
            except (ValueError, TypeError):
                validation['warnings'].append(f"Некорректный формат цены: {wc_row.get('regular_price')}")
            
            validation['is_valid'] = True
            
        except Exception as e:
            validation['warnings'].append(f"Ошибка валидации: {str(e)}")
            validation['is_valid'] = False
        
        return validation
    
    def generate_csv(self, products_data: List[Dict[str, Any]]) -> bool:
        """
        Генерация CSV файла из данных товаров
        
        Args:
            products_data: Список агрегированных товаров
            
        Returns:
            bool: Успешно ли сгенерирован CSV
        """
        self.stats['total_products'] = len(products_data)
        
        if not products_data:
            logger.error("Нет данных для экспорта")
            return False
        
        logger.info(f"Начало генерации CSV для {len(products_data)} товаров")
        logger.info(f"Используется {len(self.wc_fields)} полей")
        

        try:
            # Подготавливаем все данные
            wc_rows = []
            validation_results = []
            
            for i, product in enumerate(products_data, 1):
                logger.debug(f"Подготовка товара {i}/{len(products_data)}: {product.get('sku', 'N/A')}")
                
                wc_row = self.prepare_wc_data(product)
                
                # ПРОВЕРЯЕМ ЧТО ВСЕ ПОЛЯ В wc_row ЕСТЬ В self.wc_fields
                if wc_row:
                    # Убедимся, что нет лишних полей (двойная проверка)
                    extra_fields = set(wc_row.keys()) - set(self.wc_fields)
                    if extra_fields:
                        logger.warning(f"Товар {i} имеет лишние поля: {extra_fields}")
                        # Удаляем лишние поля
                        for field in extra_fields:
                            del wc_row[field]
                    
                    # Валидация
                    validation = self.validate_wc_row(wc_row)
                    validation_results.append(validation)
                    
                    if validation['is_valid']:
                        wc_rows.append(wc_row)
                        self.stats['exported'] += 1
                        logger.debug(f"Товар {i} подготовлен успешно")
                    else:
                        self.stats['skipped'] += 1
                        logger.warning(f"Товар {i} ({product.get('sku', 'N/A')}) пропущен: {validation['missing_required'] or validation['warnings']}")
                else:
                    self.stats['skipped'] += 1
                    logger.warning(f"Товар {i} ({product.get('sku', 'N/A')}) не удалось подготовить")
                
                # Прогресс
                if i % 10 == 0:
                    logger.info(f"Прогресс: {i}/{len(products_data)} товаров подготовлено")
            
            if not wc_rows:
                logger.error("Не удалось подготовить ни одного товара для экспорта")
                return False
            
            # Записываем CSV с разделителем ;
            logger.info(f"Запись CSV файла: {self.output_path}")
            
            with open(self.output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                # Настройки для WooCommerce с разделителем ;
                if self.encoding == 'utf-8':
                    csvfile.write('\ufeff')  # BOM для Excel
                
                writer = csv.DictWriter(
                    csvfile, 
                    fieldnames=self.wc_fields,  # Используем фиксированный порядок полей
                    delimiter=';',  # Разделитель точка с запятой
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,
                    escapechar='\\'
                )
                
                writer.writeheader()
                writer.writerows(wc_rows)


    # ... остальной код ...
            
            # Статистика валидации
            valid_count = sum(1 for v in validation_results if v['is_valid'])
            avg_fields = sum(v.get('fields_count', 0) for v in validation_results) / len(validation_results) if validation_results else 0
            avg_empty = sum(v.get('empty_fields', 0) for v in validation_results) / len(validation_results) if validation_results else 0
            
            # Итоговая статистика
            logger.info("=" * 60)
            logger.info("ЭКСПОРТ CSV ЗАВЕРШЕН")
            logger.info("=" * 60)
            logger.info(f"Всего товаров: {self.stats['total_products']}")
            logger.info(f"Экспортировано: {self.stats['exported']}")
            logger.info(f"Пропущено: {self.stats['skipped']}")
            logger.info(f"Процент успеха: {(self.stats['exported'] / self.stats['total_products'] * 100):.1f}%")
            logger.info(f"Валидных товаров: {valid_count}/{len(validation_results)}")
            logger.info(f"Среднее полей на товар: {avg_fields:.1f}")
            logger.info(f"Среднее пустых полей: {avg_empty:.1f}")
            logger.info(f"CSV файл создан: {self.output_path}")
            
            # Проверяем размер файла
            if os.path.exists(self.output_path):
                file_size = os.path.getsize(self.output_path)
                logger.info(f"Размер CSV файла: {file_size / 1024:.2f} KB")
                
                # Проверяем количество строк
                with open(self.output_path, 'r', encoding=self.encoding) as f:
                    lines = f.readlines()
                    logger.info(f"Строк в файле: {len(lines)} (заголовок + {len(lines)-1} товаров)")
            
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
            import traceback
            logger.error(traceback.format_exc())
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
        products_data: Список агрегированных товаров
        output_path: Путь для сохранения CSV
        
    Returns:
        bool: Успешно ли экспортировано
    """
    exporter = CSVExporter(output_path)
    return exporter.generate_csv(products_data)