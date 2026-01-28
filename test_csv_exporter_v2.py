"""
test_csv_exporter_v2.py
Тестирование нового CSV экспортера с разделителем ;
"""

import sys
import os
import logging
import tempfile
import csv

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from output_managers.csv_exporter import CSVExporter, export_to_csv
from config.wc_fields_config import get_wc_fields

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_aggregated_data():
    """
    Создание тестовых агрегированных данных для экспорта
    """
    return [
        {
            'name': 'Конвектор электрический Ballu IP 54 BEC/CMR-2000',
            'sku': 'BEC/CMR-2000',
            'brand': 'Ballu',
            'category': 'Тепловое оборудование > Бытовые электрические обогреватели > Электрические конвекторы',
            'price': 46990.0,
            'characteristics_raw': 'Аварийное отключение при сильном наклоне: Да; Мощность: 2 кВт; Цвет: Белый; Страна производства: РОССИЯ',
            'images_raw': 'https://example.com/image1.jpg ! alt : Конвектор Ballu ! title : Конвектор электрический ! desc :  ! caption :  | https://example.com/image2.jpg ! alt :  ! title :  ! desc :  ! caption : ',
            'description_raw': '<p>Электрический конвектор Ballu с Х-образным монолитным нагревательным элементом...</p>',
            'post_content': '<h3>Технические характеристики</h3><ul><li>Мощность: 2 кВт</li><li>Цвет: Белый</li><li>Страна производства: Россия</li></ul>',
            'post_excerpt': 'Электрический конвектор Ballu с защитой IP54 для влажных помещений',
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
            },
            'wc_image_paths': '/wp-content/uploads/products/BEC-CMR-2000-convektor-ballu-01.jpg | /wp-content/uploads/products/BEC-CMR-2000-convektor-ballu-02.jpg',
            'additional_info': {
                'Штрих код': '4660294720440/4660294720441',
                'НС-код': 'НС-1659333',
                'Эксклюзив': 'Нет'
            },
            '_aggregation_meta': {
                'sources': ['xlsx_parser', 'description_builder', 'image_handler'],
                'completeness_check': {
                    'has_all_required': True,
                    'has_description': True,
                    'has_images': True,
                    'has_attributes': True
                }
            },
            '_aggregation_status': 'complete'
        },
        {
            'name': 'Стойка для кнопки вызова помощника из нержавеющей стали',
            'sku': '62464',
            'brand': 'Исток-Смарт',
            'category': 'Оборудование для создания доступной среды > Система вызова помощника',
            'price': 16300.0,
            'characteristics_raw': 'Материал: Нержавеющая сталь; Высота: 2000 мм; Диаметр: 38 мм; Вес: 4.5 кг',
            'images_raw': 'https://example.com/stand1.jpg',
            'description_raw': '<p>Стойка для кнопки вызова предназначена для закрепления кнопки вызова...</p>',
            'post_content': '<h3>Технические характеристики</h3><ul><li>Материал: Нержавеющая сталь</li><li>Высота: 2000 мм</li><li>Диаметр: 38 мм</li></ul>',
            'post_excerpt': 'Стойка для кнопки вызова помощника из нержавеющей стали',
            'wc_attributes': {
                'attributes': {
                    'pa_material': 'Нержавеющая сталь',
                    'pa_dimensions': '2000 x 38 мм'
                },
                'attributes_data': {
                    'pa_material_data': '1:0|0',
                    'pa_dimensions_data': '1:0|0'
                }
            },
            'extracted_fields': {
                'weight': '4.5 кг',
                'height': '2000 мм',
                'width': '38 мм'
            },
            'wc_image_paths': '/wp-content/uploads/products/62464-stojka-dlja-knopki-01.jpg',
            'additional_info': {
                'Штрих код': '4601234567890',
                'НС-код': 'НС-21581',
                'Эксклюзив': 'Да'
            },
            '_aggregation_meta': {
                'sources': ['xlsx_parser', 'description_builder', 'image_handler'],
                'completeness_check': {
                    'has_all_required': True,
                    'has_description': True,
                    'has_images': True,
                    'has_attributes': True
                }
            },
            '_aggregation_status': 'complete'
        },
        {
            'name': 'Тестовый товар без полных данных',
            'sku': 'TEST-001',
            'brand': '',
            'category': '',
            'price': 1000.0,
            'characteristics_raw': '',
            'images_raw': '',
            'description_raw': '',
            'post_content': '',
            'post_excerpt': '',
            'wc_attributes': {},
            'extracted_fields': {},
            'wc_image_paths': '',
            'additional_info': {},
            '_aggregation_meta': {
                'sources': ['xlsx_parser'],
                'completeness_check': {
                    'has_all_required': False,
                    'has_description': False,
                    'has_images': False,
                    'has_attributes': False
                }
            },
            '_aggregation_status': 'partial'
        }
    ]


def test_exporter_initialization():
    """
    Тест инициализации экспортера
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Инициализация CSV экспортера")
    logger.info("="*60)
    
    try:
        # Создаем временный файл для тестирования
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            temp_file = tmp.name
        
        exporter = CSVExporter(output_path=temp_file)
        
        # Проверяем свойства
        logger.info(f"Выходной файл: {exporter.output_path}")
        logger.info(f"Кодировка: {exporter.encoding}")
        logger.info(f"Количество полей: {len(exporter.wc_fields)}")
        
        # Проверяем несколько полей
        sample_fields = exporter.wc_fields[:5]
        logger.info(f"Пример полей: {sample_fields}")
        
        # Проверяем что разделитель будет ;
        # (это внутренняя настройка, проверяется при записи файла)
        
        # Проверяем дефолтные значения
        logger.info(f"post_status по умолчанию: {exporter.default_row.get('post_status')}")
        logger.info(f"comment_status по умолчанию: {exporter.default_row.get('comment_status')}")
        logger.info(f"post_author по умолчанию: {exporter.default_row.get('post_author')}")
        
        # Очистка
        os.unlink(temp_file)
        
        logger.info("✓ Инициализация успешна")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка инициализации: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_prepare_wc_data():
    """
    Тест подготовки данных товара
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Подготовка данных WC")
    logger.info("="*60)
    
    try:
        test_data = create_test_aggregated_data()
        test_product = test_data[0]  # Первый товар
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            temp_file = tmp.name
        
        exporter = CSVExporter(output_path=temp_file)
        
        # Подготавливаем данные
        wc_row = exporter.prepare_wc_data(test_product)
        
        # Проверяем ключевые поля
        required_fields = [
            'post_title', 'post_name', 'sku', 'regular_price',
            'post_content', 'post_excerpt', 'post_status', 'post_date'
        ]
        
        logger.info(f"Подготовлено полей: {len(wc_row)}")
        
        for field in required_fields:
            value = wc_row.get(field, 'НЕТ')
            has_value = bool(value)
            logger.info(f"  {field}: {'✓' if has_value else '✗'} {value[:50] if has_value else ''}")
        
        # Проверяем специфические поля
        logger.info(f"  images: {len(wc_row.get('images', ''))} символов")
        logger.info(f"  tax:product_cat: {wc_row.get('tax:product_cat', 'НЕТ')}")
        logger.info(f"  tax:product_brand: {wc_row.get('tax:product_brand', 'НЕТ')}")
        
        # Проверяем SEO поля
        seo_fields = [f for f in wc_row.keys() if 'yoast' in f.lower()]
        logger.info(f"  SEO полей: {len(seo_fields)}")
        for seo_field in seo_fields[:3]:  # Показываем первые 3
            logger.info(f"    {seo_field}: {wc_row.get(seo_field, '')[:30]}...")
        
        # Проверяем атрибуты
        attr_fields = [f for f in wc_row.keys() if f.startswith('attribute:')]
        logger.info(f"  Атрибутов: {len(attr_fields)}")
        for attr_field in attr_fields:
            logger.info(f"    {attr_field}: {wc_row.get(attr_field, '')}")
        
        # Валидация
        validation = exporter.validate_wc_row(wc_row)
        logger.info(f"Валидность: {validation['is_valid']}")
        if validation['warnings']:
            logger.warning(f"Предупреждения: {validation['warnings']}")
        
        # Очистка
        os.unlink(temp_file)
        
        logger.info("✓ Подготовка данных успешна")
        return wc_row
        
    except Exception as e:
        logger.error(f"✗ Ошибка подготовки данных: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def test_csv_generation():
    """
    Тест генерации CSV файла
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Генерация CSV файла")
    logger.info("="*60)
    
    temp_file = None
    
    try:
        test_data = create_test_aggregated_data()
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            temp_file = tmp.name
        
        logger.info(f"Временный файл: {temp_file}")
        
        # Экспортируем данные
        exporter = CSVExporter(output_path=temp_file)
        success = exporter.generate_csv(test_data)
        
        # Проверяем результат
        logger.info(f"Результат экспорта: {'✓ Успех' if success else '✗ Ошибка'}")
        
        if success:
            stats = exporter.get_stats()
            logger.info(f"Статистика: {stats}")
            
            # Проверяем существование файла
            if os.path.exists(temp_file):
                file_size = os.path.getsize(temp_file)
                logger.info(f"Размер файла: {file_size} байт")
                
                # Читаем и проверяем файл
                with open(temp_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    logger.info(f"Строк в файле: {len(lines)}")
                    
                    # Проверяем первую строку (заголовки)
                    if lines and lines[0]:
                        headers = lines[0].split(';')
                        logger.info(f"Заголовков: {len(headers)}")
                        logger.info(f"Пример заголовков: {headers[:5]}...")
                        
                        # Проверяем разделитель
                        if ';' in lines[0]:
                            logger.info("✓ Разделитель ';' используется")
                        else:
                            logger.error("✗ Разделитель ';' не найден в заголовках")
                    
                    # Проверяем данные
                    if len(lines) > 1:
                        logger.info(f"Товаров экспортировано: {len(lines) - 1}")
                        
                        # Парсим вторую строку для проверки
                        if lines[1]:
                            data_parts = lines[1].split(';')
                            logger.info(f"Поля во второй строке: {len(data_parts)}")
                            
                            # Проверяем несколько значений
                            if len(data_parts) > 0:
                                logger.info(f"  post_title: {data_parts[0][:30]}...")
                            if len(data_parts) > 5:
                                logger.info(f"  post_content длина: {len(data_parts[5])}")
            
            # Также проверяем с помощью csv модуля
            with open(temp_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f, delimiter=';')
                rows = list(csv_reader)
                
                logger.info(f"CSV reader строк: {len(rows)}")
                if rows:
                    logger.info(f"CSV reader заголовков: {len(rows[0])}")
        
        # Очистка
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        
        logger.info("✓ Генерация CSV успешна")
        return success
        
    except Exception as e:
        logger.error(f"✗ Ошибка генерации CSV: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Очистка при ошибке
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        
        return False


def test_quick_export_function():
    """
    Тест быстрой функции экспорта
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Быстрая функция экспорта")
    logger.info("="*60)
    
    temp_file = None
    
    try:
        test_data = create_test_aggregated_data()
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            temp_file = tmp.name
        
        logger.info(f"Используем быструю функцию export_to_csv")
        
        # Используем быструю функцию
        success = export_to_csv(test_data, temp_file)
        
        logger.info(f"Результат: {'✓ Успех' if success else '✗ Ошибка'}")
        
        if success and os.path.exists(temp_file):
            # Простая проверка файла
            with open(temp_file, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                
                if ';' in first_line:
                    headers = first_line.strip().split(';')
                    logger.info(f"Создан файл с {len(headers)} заголовками")
                    logger.info(f"Первые 5 заголовков: {headers[:5]}")
                else:
                    logger.error("✗ Разделитель ';' не найден")
        
        # Очистка
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        
        logger.info("✓ Быстрая функция работает")
        return success
        
    except Exception as e:
        logger.error(f"✗ Ошибка быстрой функции: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_wc_fields_config():
    """
    Тест конфигурации полей WC
    """
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ: Конфигурация полей WC")
    logger.info("="*60)
    
    try:
        # Получаем поля из конфигурации
        wc_fields = get_wc_fields()
        
        logger.info(f"Всего полей в конфигурации: {len(wc_fields)}")
        
        # Группируем поля по типам
        field_types = {}
        for field in wc_fields:
            if field.startswith('meta:'):
                field_types.setdefault('meta', []).append(field)
            elif field.startswith('tax:'):
                field_types.setdefault('tax', []).append(field)
            elif field.startswith('attribute:'):
                field_types.setdefault('attribute', []).append(field)
            elif field.startswith('attribute_data:'):
                field_types.setdefault('attribute_data', []).append(field)
            else:
                field_types.setdefault('other', []).append(field)
        
        # Выводим статистику
        for field_type, fields in field_types.items():
            logger.info(f"  {field_type}: {len(fields)} полей")
        
        # Проверяем обязательные поля
        required_fields = ['post_title', 'sku', 'regular_price', 'post_status']
        missing_required = [f for f in required_fields if f not in wc_fields]
        
        if missing_required:
            logger.error(f"✗ Отсутствуют обязательные поля: {missing_required}")
            return False
        else:
            logger.info("✓ Все обязательные поля присутствуют")
        
        # Проверяем атрибуты
        attribute_fields = [f for f in wc_fields if f.startswith('attribute:')]
        logger.info(f"Атрибутов в конфигурации: {len(attribute_fields)}")
        
        for attr_field in attribute_fields:
            logger.debug(f"  {attr_field}")
        
        logger.info("✓ Конфигурация полей корректна")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка конфигурации полей: {e}")
        return False


def main():
    """
    Основная функция тестирования
    """
    logger.info("ЗАПУСК ТЕСТОВ CSV EXPORTER V2")
    logger.info("Версия с разделителем ; и фиксированными полями")
    
    test_results = {}
    
    try:
        # Тест 1: Конфигурация полей
        test_results['config'] = test_wc_fields_config()
        
        # Тест 2: Инициализация экспортера
        test_results['init'] = test_exporter_initialization()
        
        # Тест 3: Подготовка данных
        test_results['prepare'] = test_prepare_wc_data() is not None
        
        # Тест 4: Генерация CSV
        test_results['generate'] = test_csv_generation()
        
        # Тест 5: Быстрая функция
        test_results['quick'] = test_quick_export_function()
        
        # Итоги
        logger.info("\n" + "="*60)
        logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("="*60)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        
        for test_name, result in test_results.items():
            status = "✓ ПРОЙДЕН" if result else "✗ ПРОВАЛЕН"
            logger.info(f"{test_name:15} {status}")
        
        logger.info(f"\nВсего тестов: {total_tests}")
        logger.info(f"Пройдено: {passed_tests}")
        logger.info(f"Успешность: {(passed_tests / total_tests * 100):.1f}%")
        
        if passed_tests == total_tests:
            logger.info("\n✓ ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ ✓")
            return 0
        else:
            logger.error(f"\n✗ НЕ ВСЕ ТЕСТЫ ПРОЙДЕНЫ ({passed_tests}/{total_tests}) ✗")
            return 1
            
    except Exception as e:
        logger.error(f"Критическая ошибка при выполнении тестов: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)