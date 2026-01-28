"""
data_processors/data_aggregator.py
Сборщик данных от всех обработчиков для подготовки к экспорту в WooCommerce
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Настройка логгера
logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Сборщик данных от всех модулей обработки.
    Объединяет данные из XLSX парсера, DescriptionBuilder и ImageHandler
    в единую структуру для CSV экспортера.
    """
    
    def __init__(self):
        """
        Инициализация сборщика данных
        """
        self.stats = {
            'total_processed': 0,
            'successfully_aggregated': 0,
            'partial_aggregation': 0,
            'failed_aggregation': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
        logger.info("Инициализирован сборщик данных")
    
    def _find_product_by_sku(self, sku: str, products_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Поиск товара в списке по SKU
        
        Args:
            sku: Артикул для поиска
            products_list: Список товаров
            
        Returns:
            Optional[Dict[str, Any]]: Найденный товар или None
        """
        if not sku or not products_list:
            return None
        
        for product in products_list:
            if product.get('sku') == sku:
                return product
        
        return None
    
    def aggregate_single_product(self,
                               xlsx_data: Dict[str, Any],
                               description_data: Optional[Dict[str, Any]] = None,
                               images_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Сбор всех данных одного товара в единую структуру
        
        Args:
            xlsx_data: Данные из XLSX парсера (обязательно)
            description_data: Данные из DescriptionBuilder (опционально)
            images_data: Данные из ImageHandler (опционально)
            
        Returns:
            Dict[str, Any]: Полные данные товара
            
        Raises:
            ValueError: Если отсутствуют обязательные данные из XLSX
        """
        # Проверяем обязательные данные
        if not xlsx_data:
            raise ValueError("Обязательны данные из XLSX парсера")
        
        # Начинаем с копии данных из XLSX
        aggregated_product = xlsx_data.copy()
        
        # Добавляем мета-информацию о процессе агрегации
        aggregated_product['_aggregation_meta'] = {
            'aggregated_at': datetime.now().isoformat(),
            'sources': ['xlsx_parser']
        }
        
        # 1. Добавляем данные из DescriptionBuilder если есть
        if description_data:
            # Основные поля описания
            aggregated_product['post_content'] = description_data.get('post_content', '')
            aggregated_product['post_excerpt'] = description_data.get('post_excerpt', '')
            
            # Атрибуты WooCommerce
            aggregated_product['wc_attributes'] = description_data.get('wc_attributes', {})
            
            # Извлеченные поля (вес, габариты и т.д.)
            aggregated_product['extracted_fields'] = description_data.get('extracted_fields', {})
            
            # Добавляем источник
            aggregated_product['_aggregation_meta']['sources'].append('description_builder')
            
            logger.debug(f"Добавлены данные DescriptionBuilder для SKU: {aggregated_product.get('sku', 'N/A')}")
        
        # 2. Добавляем данные из ImageHandler если есть
        if images_data:
            # Результаты обработки изображений
            aggregated_product['images_processing'] = images_data.get('images_processing', {})
            
            # Пути изображений для WC CSV
            aggregated_product['wc_image_paths'] = images_data.get('wc_image_paths', '')
            
            # Добавляем источник
            aggregated_product['_aggregation_meta']['sources'].append('image_handler')
            
            logger.debug(f"Добавлены данные ImageHandler для SKU: {aggregated_product.get('sku', 'N/A')}")
        
        # 3. Проверяем полноту данных
        required_fields = ['name', 'sku', 'price', 'post_content']
        missing_fields = [field for field in required_fields if not aggregated_product.get(field)]
        
        aggregated_product['_aggregation_meta']['completeness_check'] = {
            'has_all_required': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'has_description': 'post_content' in aggregated_product and aggregated_product['post_content'],
            'has_images': 'wc_image_paths' in aggregated_product and aggregated_product['wc_image_paths'],
            'has_attributes': 'wc_attributes' in aggregated_product and aggregated_product['wc_attributes']
        }
        
        # Определяем статус агрегации
        completeness = aggregated_product['_aggregation_meta']['completeness_check']
        if completeness['has_all_required']:
            aggregated_product['_aggregation_status'] = 'complete'
        elif aggregated_product.get('name') and aggregated_product.get('sku'):
            aggregated_product['_aggregation_status'] = 'partial'
        else:
            aggregated_product['_aggregation_status'] = 'incomplete'
        
        return aggregated_product
    
    def aggregate_batch_by_sku(self,
                              xlsx_products: List[Dict[str, Any]],
                              description_products: Optional[List[Dict[str, Any]]] = None,
                              images_products: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Агрегация партии товаров по SKU.
        Сопоставляет товары из разных источников по артикулу.
        
        Args:
            xlsx_products: Список товаров из XLSX парсера (обязательно)
            description_products: Список товаров с описаниями (опционально)
            images_products: Список товаров с изображениями (опционально)
            
        Returns:
            List[Dict[str, Any]]: Агрегированные товары
            
        Raises:
            ValueError: Если xlsx_products пуст
        """
        if not xlsx_products:
            raise ValueError("Список товаров из XLSX парсера не может быть пустым")
        
        self.stats['start_time'] = datetime.now()
        self.stats['total_processed'] = len(xlsx_products)
        
        logger.info(f"Начало агрегации {len(xlsx_products)} товаров")
        logger.info(f"Description products: {len(description_products) if description_products else 0}")
        logger.info(f"Images products: {len(images_products) if images_products else 0}")
        
        aggregated_results = []
        
        for i, xlsx_product in enumerate(xlsx_products):
            try:
                sku = xlsx_product.get('sku', f'unknown_{i}')
                product_name = xlsx_product.get('name', 'Без названия')
                
                logger.debug(f"Агрегация товара {i+1}/{len(xlsx_products)}: {sku} - {product_name[:50]}...")
                
                # Ищем соответствующие данные в других списках
                description_data = None
                if description_products:
                    description_data = self._find_product_by_sku(sku, description_products)
                
                images_data = None
                if images_products:
                    images_data = self._find_product_by_sku(sku, images_products)
                
                # Агрегируем данные
                aggregated_product = self.aggregate_single_product(
                    xlsx_data=xlsx_product,
                    description_data=description_data,
                    images_data=images_data
                )
                
                # Обновляем статистику
                status = aggregated_product.get('_aggregation_status', 'unknown')
                if status == 'complete':
                    self.stats['successfully_aggregated'] += 1
                elif status == 'partial':
                    self.stats['partial_aggregation'] += 1
                else:
                    self.stats['failed_aggregation'] += 1
                
                aggregated_results.append(aggregated_product)
                
                # Логирование прогресса
                if (i + 1) % 10 == 0:
                    logger.info(f"Прогресс: {i + 1}/{len(xlsx_products)} товаров агрегировано")
                    
            except Exception as e:
                error_msg = f"Ошибка агрегации товара {i} (SKU: {xlsx_product.get('sku', 'N/A')}): {str(e)}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                self.stats['failed_aggregation'] += 1
        
        # Завершаем статистику
        self.stats['end_time'] = datetime.now()
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            self.stats['duration_seconds'] = duration
        
        # Итоговый отчет
        logger.info("=" * 60)
        logger.info("АГРЕГАЦИЯ ДАННЫХ ЗАВЕРШЕНА")
        logger.info("=" * 60)
        logger.info(f"Всего обработано товаров: {self.stats['total_processed']}")
        logger.info(f"Полностью агрегировано: {self.stats['successfully_aggregated']}")
        logger.info(f"Частично агрегировано: {self.stats['partial_aggregation']}")
        logger.info(f"Не удалось агрегировать: {self.stats['failed_aggregation']}")
        logger.info(f"Ошибок: {len(self.stats['errors'])}")
        
        if self.stats.get('duration_seconds'):
            logger.info(f"Время выполнения: {self.stats['duration_seconds']:.2f} секунд")
            if self.stats['total_processed'] > 0:
                products_per_second = self.stats['total_processed'] / self.stats['duration_seconds']
                logger.info(f"Скорость обработки: {products_per_second:.2f} товаров/сек")
        
        return aggregated_results
    
    def validate_aggregated_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация агрегированного товара
        
        Args:
            product: Агрегированный товар
            
        Returns:
            Dict[str, Any]: Результаты валидации
        """
        validation_result = {
            'is_valid': False,
            'missing_required': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Обязательные поля
            required_fields = ['name', 'sku', 'price']
            missing_required = [field for field in required_fields if not product.get(field)]
            
            if missing_required:
                validation_result['missing_required'] = missing_required
                validation_result['is_valid'] = False
                return validation_result
            
            # Желательные поля
            desired_fields = ['post_content', 'wc_image_paths', 'category']
            missing_desired = [field for field in desired_fields if not product.get(field)]
            
            if missing_desired:
                validation_result['warnings'].append(f"Отсутствуют желательные поля: {missing_desired}")
            
            # Проверка цены
            price = product.get('price')
            if price is not None:
                try:
                    price_float = float(price)
                    if price_float <= 0:
                        validation_result['warnings'].append(f"Цена должна быть больше 0: {price}")
                    if price_float > 10000000:  # 10 миллионов
                        validation_result['warnings'].append(f"Подозрительно высокая цена: {price}")
                except (ValueError, TypeError):
                    validation_result['warnings'].append(f"Некорректный формат цены: {price}")
            
            # Проверка SKU
            sku = product.get('sku', '')
            if not sku or len(sku) < 2:
                validation_result['warnings'].append(f"Короткий или пустой SKU: {sku}")
            
            # Рекомендации
            if not product.get('post_content'):
                validation_result['recommendations'].append("Добавить описание товара")
            
            if not product.get('wc_image_paths'):
                validation_result['recommendations'].append("Добавить изображения товара")
            
            if not product.get('category'):
                validation_result['recommendations'].append("Указать категорию товара")
            
            validation_result['is_valid'] = True
            
        except Exception as e:
            validation_result['warnings'].append(f"Ошибка валидации: {str(e)}")
            validation_result['is_valid'] = False
        
        return validation_result
    
    def get_summary_report(self) -> str:
        """
        Получить текстовый отчет о результатах агрегации
        
        Returns:
            str: Текстовый отчет
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("ОТЧЕТ ОБ АГРЕГАЦИИ ДАННЫХ")
        report_lines.append("=" * 60)
        report_lines.append(f"Всего товаров: {self.stats['total_processed']}")
        report_lines.append(f"Полностью агрегировано: {self.stats['successfully_aggregated']}")
        report_lines.append(f"Частично агрегировано: {self.stats['partial_aggregation']}")
        report_lines.append(f"Не удалось агрегировать: {self.stats['failed_aggregation']}")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successfully_aggregated'] / self.stats['total_processed']) * 100
            report_lines.append(f"Процент успеха: {success_rate:.1f}%")
        
        if self.stats.get('duration_seconds'):
            report_lines.append(f"Время выполнения: {self.stats['duration_seconds']:.2f} сек")
        
        if self.stats['errors']:
            report_lines.append("\nОШИБКИ:")
            for i, error in enumerate(self.stats['errors'][:10], 1):  # Показываем первые 10 ошибок
                report_lines.append(f"{i}. {error}")
            if len(self.stats['errors']) > 10:
                report_lines.append(f"... и еще {len(self.stats['errors']) - 10} ошибок")
        
        return "\n".join(report_lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику агрегации
        
        Returns:
            Dict[str, Any]: Статистика
        """
        return self.stats.copy()


# Функции для быстрого использования
def aggregate_products(xlsx_products: List[Dict[str, Any]],
                      description_products: List[Dict[str, Any]] = None,
                      images_products: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Быстрая агрегация товаров
    
    Args:
        xlsx_products: Товары из XLSX парсера
        description_products: Товары с описаниями
        images_products: Товары с изображениями
        
    Returns:
        List[Dict[str, Any]]: Агрегированные товары
    """
    aggregator = DataAggregator()
    return aggregator.aggregate_batch_by_sku(xlsx_products, description_products, images_products)


def validate_product_for_export(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Быстрая валидация товара для экспорта
    
    Args:
        product: Товар для валидации
        
    Returns:
        Dict[str, Any]: Результаты валидации
    """
    aggregator = DataAggregator()
    return aggregator.validate_aggregated_product(product)