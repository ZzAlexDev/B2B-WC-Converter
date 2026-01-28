"""
test_data_aggregator.py
Тестирование DataAggregator
"""

import sys
import os
import logging

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processors.data_aggregator import DataAggregator, aggregate_products

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_data():
    """
    Создание тестовых данных для агрегатора
    """
    # Тестовые данные из XLSX парсера
    xlsx_products = [
        {
            'name': 'Конвектор электрический Ballu IP 54 BEC/CMR-2000',
            'sku': 'BEC/CMR-2000',
            'brand': 'Ballu',
            'category': 'Тепловое оборудование > Бытовые электрические обогреватели > Электрические конвекторы',
            'price': 46990.0,
            'characteristics_raw': 'Аварийное отключение при сильном наклоне: Да; Мощность: 2 кВт; Цвет: Белый',
            'images_raw': 'https://example.com/image1.jpg,https://example.com/image2.jpg',
            'description_raw': '<p>Электрический конвектор Ballu с Х-образным монолитным нагревательным элементом...</p>',
            'documents': {
                'Чертежи': 'https://example.com/drawing.pdf',
                'Инструкции': 'https://example.com/instructions.pdf'
            },
            'additional_info': {
                'Штрих код': '4660294720440',
                'НС-код': 'НС-1659333',
                'Эксклюзив': 'Нет'
            }
        },
        {
            'name': 'Стойка для кнопки вызова помощника',
            'sku': '62464',
            'brand': '',
            'category': 'Оборудование для создания доступной среды > Система вызова помощника',
            'price': 16300.0,
            'characteristics_raw': 'Материал: Нержавеющая сталь; Высота: 2000 мм; Диаметр: 38 мм',
            'images_raw': 'https://example.com/stand1.jpg',
            'description_raw': '<p>Стойка для кнопки вызова предназначена для закрепления кнопки вызова...</p>',
            'documents': {},
            'additional_info': {}
        }
    ]
    
    # Тестовые данные из DescriptionBuilder
    description_products = [
        {
            'sku': 'BEC/CMR-2000',
            'post_content': '<h3>Технические характеристики</h3><ul><li>Мощность: 2 кВт</li><li>Цвет: Белый</li></ul>',
            'post_excerpt': 'Электрический конвектор Ballu с защитой IP54',
            'wc_attributes': {
                'attributes': {
                    'pa_color': 'Белый',
                    'pa_power': '2 кВт',
                    'pa_country': 'РОССИЯ'
                },
                'attributes_data': {
                    'pa_color_data': '1:0|0',
                    'pa_power_data': '1:0|0',
                    'pa_country_data': '1:0|0'
                }
            },
            'extracted_fields': {
                'weight': '5.9 кг',
                'width': '94 см',
                'height': '22 см',
                'length': '12 см'
            }
        },
        {
            'sku': '62464',
            'post_content': '<h3>Технические характеристики</h3><ul><li>Материал: Нержавеющая сталь</li><li>Высота: 2000 мм</li></ul>',
            'post_excerpt': 'Стойка для кнопки вызова помощника из нержавеющей стали',
            'wc_attributes': {
                'attributes': {
                    'pa_material': 'Нержавеющая сталь',
                    'pa_dimensions': '2000 мм x 38 мм'
                },
                'attributes_data': {
                    'pa_material_data': '1:0|0',
                    'pa_dimensions_data': '1:0|0'
                }
            },
            'extracted_fields': {
                'weight': '4.5 кг',
                'height': '2000 мм'
            }
        }
    ]
    
    # Тестовые данные из ImageHandler
    images_products = [
        {
            'sku': 'BEC/CMR-2000',
            'images_processing': {
                'success': True,
                'downloaded_count': 2,
                'filenames': ['BEC-CMR-2000-convektor-ballu-01.jpg', 'BEC-CMR-2000-convektor-ballu-02.jpg']
            },
            'wc_image_paths': '/wp-content/uploads/products/BEC-CMR-2000-convektor-ballu-01.jpg | /wp-content/uploads/products/BEC-CMR-2000-convektor-ballu-02.jpg'
        },
        {
            'sku': '62464',
            'images_processing': {
                'success': True,
                'downloaded_count': 1,
                'filenames': ['62464-stojka-dlja-knopki-01.jpg']
            },
            'wc_image_paths': '/wp-content/uploads/products/62464-stojka-dlja-knopki-01.jpg'
        }
    ]
    
    return xlsx_products, description_products, images_products


def test_single_product_aggregation():
    """
    Тестирование агрегации одного товара
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Агрегация одного товара")
    logger.info("="*60)
    
    xlsx_products, description_products, images_products = create_test_data()
    
    aggregator = DataAggregator()
    
    # Агрегируем первый товар
    aggregated = aggregator.aggregate_single_product(
        xlsx_data=xlsx_products[0],
        description_data=description_products[0],
        images_data=images_products[0]
    )
    
    logger.info(f"Результат агрегации для SKU: {aggregated.get('sku')}")
    logger.info(f"Статус: {aggregated.get('_aggregation_status')}")
    logger.info(f"Источники: {aggregated.get('_aggregation_meta', {}).get('sources', [])}")
    
    # Проверяем наличие ключевых полей
    required_fields = ['name', 'sku', 'price', 'post_content', 'wc_image_paths']
    for field in required_fields:
        if field in aggregated:
            logger.info(f"✓ Поле '{field}' присутствует: {bool(aggregated[field])}")
        else:
            logger.warning(f"✗ Поле '{field}' отсутствует")
    
    # Валидация
    validation = aggregator.validate_aggregated_product(aggregated)
    logger.info(f"Валидность: {validation['is_valid']}")
    if validation['warnings']:
        logger.warning(f"Предупреждения: {validation['warnings']}")
    
    return aggregated


def test_batch_aggregation():
    """
    Тестирование агрегации партии товаров
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Агрегация партии товаров")
    logger.info("="*60)
    
    xlsx_products, description_products, images_products = create_test_data()
    
    # Используем быструю функцию
    aggregated_products = aggregate_products(
        xlsx_products=xlsx_products,
        description_products=description_products,
        images_products=images_products
    )
    
    logger.info(f"Всего агрегировано товаров: {len(aggregated_products)}")
    
    for i, product in enumerate(aggregated_products, 1):
        logger.info(f"\nТовар {i}: {product.get('name', 'Без названия')[:50]}...")
        logger.info(f"  SKU: {product.get('sku')}")
        logger.info(f"  Статус агрегации: {product.get('_aggregation_status')}")
        logger.info(f"  Описание: {'✓' if product.get('post_content') else '✗'}")
        logger.info(f"  Изображения: {'✓' if product.get('wc_image_paths') else '✗'}")
        logger.info(f"  Атрибуты: {len(product.get('wc_attributes', {}).get('attributes', {}))}")
    
    return aggregated_products


def test_missing_data():
    """
    Тестирование агрегации с отсутствующими данными
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Агрегация с отсутствующими данными")
    logger.info("="*60)
    
    xlsx_products, _, _ = create_test_data()
    
    # Создаем товар без описания и изображений
    test_product = xlsx_products[0].copy()
    test_product['sku'] = 'TEST-001'
    test_product['name'] = 'Тестовый товар без данных'
    
    aggregator = DataAggregator()
    
    aggregated = aggregator.aggregate_single_product(
        xlsx_data=test_product,
        description_data=None,
        images_data=None
    )
    
    logger.info(f"Товар: {aggregated.get('name')}")
    logger.info(f"Статус агрегации: {aggregated.get('_aggregation_status')}")
    
    validation = aggregator.validate_aggregated_product(aggregated)
    logger.info(f"Валидность: {validation['is_valid']}")
    if validation['warnings']:
        logger.warning(f"Предупреждения: {validation['warnings']}")
    if validation['recommendations']:
        logger.info(f"Рекомендации: {validation['recommendations']}")
    
    return aggregated


def main():
    """
    Основная функция тестирования
    """
    logger.info("Запуск тестов DataAggregator")
    
    try:
        # Тест 1: Агрегация одного товара
        test_single_product_aggregation()
        
        # Тест 2: Агрегация партии товаров
        test_batch_aggregation()
        
        # Тест 3: Агрегация с отсутствующими данными
        test_missing_data()
        
        logger.info("\n" + "="*60)
        logger.info("ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении тестов: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)