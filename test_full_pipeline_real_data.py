"""
test_full_pipeline_real_data.py
Полный тест pipeline с реальными данными характеристик
"""

import sys
import os
import logging
import tempfile
import json

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processors.attribute_parser import AttributeParser
from data_processors.description_builder import DescriptionBuilder
from data_processors.xlsx_parser import XLSXParser
from output_managers.csv_exporter import CSVExporter
from config.wc_fields_config import get_wc_fields, get_wc_default_row

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_real_test_product():
    """
    Создание тестового товара с реальными характеристиками
    """
    return {
        'name': 'Термостат Ballu Evolution Transformer system BMT-2',
        'sku': 'BMT-2',
        'brand': 'Ballu',
        'category': 'Тепловое оборудование > Термостаты и регуляторы',
        'price': 2890.0,
        'characteristics_raw': """
            Wi-Fi модуль: Нет; Вариант размещения: Горизонтальное; 
            Вид управления: Механическое; Вид установки (крепления): Монтаж присоединительный; 
            Высота товара: 9.1 см; Высота упаковки товара: 9.5 см; 
            Гарантийный документ: Гарантийный талон; Гарантийный срок: 3 года; 
            Глубина товара: 8.6 см; Глубина упаковки товара: 10 см; 
            Защита кнопок управления от детей: Нет; Защита от перегрева: Да; 
            Инверторная технология: Нет; Индивидуальное программирование: Нет; 
            Индикация включения: Да; Индикация режимов работы: Нет; 
            Индикация температуры нагрева: Нет; Кабель для подключения к системе отопления: Нет; 
            Класс пылевлагозащищенности: IP24; Количество режимов нагрева: 2; 
            Макс. потребляемая мощность: 0.1 кВт; Масса товара (нетто): 0.29 кг; 
            Масса товара с упаковкой (брутто): 0.35 кг; Материал корпуса: Пластик; 
            Набор крепежных элементов в комплекте: Да; 
            Назначение и соответствие: совместим с Ballu Evolution Transformer system; 
            Напряжение электропитания, В: 220 - 240 В; 
            Область применения: Бытовое оборудование (для домашнего использования); 
            Объединение в инверторную систему отопления: Нет; Подсветка дисплея: Нет; 
            Пульт управления в комплекте: Нет; Регулировка температуры: Да; 
            Режим защиты от замерзания: Нет; Серия: Transformer system; 
            Система самодиагностики неисправности: Нет; 
            Сохранение настроек при отключении электричества: Нет; Срок службы: 10 лет; 
            Страна производства: КНР; Таймер на отключение: Нет; 
            Тип термостата: Механический; Точность установки температуры: 1,0 °С; 
            Управление c мобильного приложения по Wi-Fi: Нет; 
            Цвет корпуса: Cветло-серый; Цифровой дисплей: Нет; 
            Ширина товара: 14.8 см; Ширина упаковки товара: 16 см
        """,
        'images_raw': 'https://example.com/termostat1.jpg,https://example.com/termostat2.jpg',
        'description_raw': '<p>Термостат Ballu Evolution Transformer system BMT-2 предназначен для точного поддержания температуры в системе отопления.</p>',
        'documents': {
            'Инструкции': 'https://example.com/instruction.pdf'
        },
        'additional_info': {
            'Штрих код': '4601234567890',
            'НС-код': 'НС-987654',
            'Эксклюзив': 'Нет'
        }
    }


def test_attribute_parser():
    """Тест парсера характеристик"""
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ 1: Парсер характеристик")
    logger.info("="*60)
    
    test_product = create_real_test_product()
    characteristics = test_product['characteristics_raw']
    
    parser = AttributeParser()
    
    # Тест парсинга
    grouped = parser.parse_and_group(characteristics)
    
    logger.info(f"Найдено групп характеристик: {len(grouped)}")
    total_chars = sum(len(chars) for chars in grouped.values())
    logger.info(f"Всего характеристик: {total_chars}")
    
    # Проверка групп
    expected_groups = ['Общие сведения', 'Габариты и вес', 'Управление', 'Безопасность']
    for group in expected_groups:
        if group in grouped:
            logger.info(f"✓ Группа '{group}' найдена: {len(grouped[group])} характеристик")
        else:
            logger.warning(f"✗ Группа '{group}' не найдена")
    
    # Тест извлечения WC атрибутов
    wc_attrs = parser.extract_wc_attributes(characteristics)
    
    logger.info(f"\nИзвлечено WC атрибутов: {len(wc_attrs.get('attributes', {}))}")
    
    # Ожидаемые основные атрибуты
    expected_main_attributes = {
        'pa_placement': 'Горизонтальное',
        'pa_application': 'Бытовое оборудование (для домашнего использования)',
        'pa_warranty': '3',
        'pa_color': 'Cветло-серый',
        'pa_country': 'КНР',
        'pa_power': '0.1',
        'pa_weight': '0.29',
        'pa_width': '14.8',
        'pa_depth': '8.6',
        'pa_height': '9.1',
        'pa_lifetime': '10',
        'pa_material': 'Пластик',
        'pa_thermostat': 'Механический',
        'pa_ip_rating': 'IP24',
        'pa_control_type': 'Механическое',
    }
    
    logger.info("\nПроверка основных атрибутов:")
    found_count = 0
    for attr_slug, expected_value in expected_main_attributes.items():
        actual_value = wc_attrs.get('attributes', {}).get(attr_slug)
        if actual_value:
            found_count += 1
            status = "✓" if str(actual_value) == str(expected_value) else "✗"
            logger.info(f"{status} {attr_slug}: {actual_value}")
        else:
            logger.warning(f"✗ {attr_slug}: НЕ НАЙДЕН (ожидалось: {expected_value})")
    
    success_rate = (found_count / len(expected_main_attributes)) * 100
    logger.info(f"\nУспешность извлечения атрибутов: {success_rate:.1f}%")
    
    return parser, grouped, wc_attrs


def test_description_builder():
    """Тест сборщика описаний"""
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ 2: Сборщик описаний")
    logger.info("="*60)
    
    test_product = create_real_test_product()
    
    builder = DescriptionBuilder()
    
    # Собираем описание
    description_result = builder.build_full_description(test_product)
    
    logger.info(f"post_content длина: {len(description_result.get('post_content', ''))}")
    logger.info(f"post_excerpt длина: {len(description_result.get('post_excerpt', ''))}")
    
    # Проверяем ключевые элементы
    html_content = description_result.get('post_content', '')
    
    check_points = [
        ('<h3>Технические характеристики</h3>', 'Заголовок характеристик'),
        ('<div id="product-characteristics">', 'Якорь для характеристик'),
        ('Область применения', 'Основной атрибут в описании'),
        ('Макс. потребляемая мощность', 'Основной атрибут в описании'),
        ('Срок службы', 'Основной атрибут в описании'),
        ('class="wc-attribute"', 'Класс для WC атрибутов'),
    ]
    
    logger.info("\nПроверка HTML описания:")
    for text, description in check_points:
        if text in html_content:
            logger.info(f"✓ Найдено: {description}")
        else:
            logger.warning(f"✗ Не найдено: {description}")
    
    # Проверяем excerpt
    excerpt = description_result.get('post_excerpt', '')
    if '#product-characteristics' in excerpt:
        logger.info("✓ Excerpt содержит ссылку на характеристики")
    else:
        logger.warning("✗ Excerpt не содержит ссылку на характеристики")
    
    logger.info(f"\nExcerpt пример: {excerpt[:100]}...")
    
    return builder, description_result


def test_wc_fields_config():
    """Тест конфигурации полей WC"""
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ 3: Конфигурация полей WooCommerce")
    logger.info("="*60)
    
    wc_fields = get_wc_fields()
    default_row = get_wc_default_row()
    
    logger.info(f"Всего полей в конфигурации: {len(wc_fields)}")
    
    # Проверяем что нет ненужных атрибутов
    unwanted_attributes = [
        'pa_proizvoditel',
        'pa_sposob-primenenija', 
        'pa_tip-narushenij',
        'pa_tip-uchrezhdenij',
        'pa_tip-ustrojstva',
        'pa_zona-primenenija'
    ]
    
    found_unwanted = []
    for field in wc_fields:
        for unwanted in unwanted_attributes:
            if unwanted in field:
                found_unwanted.append(field)
    
    if found_unwanted:
        logger.error(f"✗ Найдены ненужные атрибуты: {found_unwanted}")
    else:
        logger.info("✓ Ненужные атрибуты отсутствуют")
    
    # Проверяем наличие основных атрибутов
    required_attributes = [
        'pa_placement',
        'pa_application',
        'pa_warranty',
        'pa_color',
        'pa_country',
        'pa_power',
        'pa_weight',
        'pa_width',
        'pa_depth',
        'pa_height',
        'pa_lifetime'
    ]
    
    found_required = []
    missing_required = []
    
    for attr in required_attributes:
        attribute_field = f'attribute:{attr}'
        attribute_data_field = f'attribute_data:{attr}'
        
        if attribute_field in wc_fields and attribute_data_field in wc_fields:
            found_required.append(attr)
        else:
            missing_required.append(attr)
    
    logger.info(f"\nОсновные атрибуты найдены: {len(found_required)}/{len(required_attributes)}")
    
    if missing_required:
        logger.error(f"✗ Отсутствуют атрибуты: {missing_required}")
    else:
        logger.info("✓ Все основные атрибуты присутствуют")
    
    # Проверяем дефолтные значения
    required_defaults = ['post_status', 'comment_status', 'post_author', 'tax:product_type']
    for field in required_defaults:
        if field in default_row:
            logger.info(f"✓ Дефолтное значение для '{field}': {default_row[field]}")
        else:
            logger.warning(f"✗ Нет дефолтного значения для '{field}'")
    
    return wc_fields, default_row


def test_csv_exporter():
    """Тест CSV экспортера"""
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ 4: CSV экспортер с реальными данными")
    logger.info("="*60)
    
    temp_file = None
    
    try:
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            temp_file = tmp.name
        
        # Создаем тестовые данные
        test_products = [create_real_test_product()]
        
        # Добавляем обработанные данные
        parser = AttributeParser()
        builder = DescriptionBuilder()
        
        for product in test_products:
            # Обрабатываем характеристики
            wc_attrs = parser.extract_wc_attributes(product['characteristics_raw'])
            product['wc_attributes'] = wc_attrs
            
            # Собираем описание
            desc_result = builder.build_full_description(product)
            product.update(desc_result)
        
        # Экспортируем в CSV
        exporter = CSVExporter(output_path=temp_file)
        success = exporter.generate_csv(test_products)
        
        logger.info(f"Результат экспорта: {'✓ Успех' if success else '✗ Ошибка'}")
        
        if success:
            stats = exporter.get_stats()
            logger.info(f"Статистика: {stats}")
            
            # Читаем и проверяем CSV файл
            if os.path.exists(temp_file):
                with open(temp_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    logger.info(f"Строк в файле: {len(lines)}")
                    
                    if lines and lines[0]:
                        headers = lines[0].split(';')
                        logger.info(f"Заголовков: {len(headers)}")
                        
                        # Проверяем разделитель
                        if ';' in lines[0]:
                            logger.info("✓ Разделитель ';' используется")
                        else:
                            logger.error("✗ Разделитель ';' не найден")
                        
                        # Проверяем наличие основных полей
                        required_headers = ['post_title', 'sku', 'regular_price', 'post_status']
                        for header in required_headers:
                            if header in headers:
                                logger.info(f"✓ Обязательное поле '{header}' присутствует")
                            else:
                                logger.error(f"✗ Обязательное поле '{header}' отсутствует")
                        
                        # Проверяем атрибуты
                        attribute_headers = [h for h in headers if h.startswith('attribute:')]
                        logger.info(f"Атрибутов в CSV: {len(attribute_headers)}")
                        
                        # Проверяем что нет ненужных атрибутов
                        unwanted_in_csv = [h for h in attribute_headers if any(
                            unwanted in h for unwanted in ['proizvoditel', 'sposob-primenenija', 'tip-narushenij']
                        )]
                        
                        if unwanted_in_csv:
                            logger.error(f"✗ В CSV есть ненужные атрибуты: {unwanted_in_csv}")
                        else:
                            logger.info("✓ Ненужные атрибуты отсутствуют в CSV")
                    
                    # Проверяем данные
                    if len(lines) > 1 and lines[1]:
                        data = lines[1].split(';')
                        if len(data) == len(headers):
                            logger.info("✓ Количество данных соответствует заголовкам")
                            
                            # Создаем словарь для проверки
                            data_dict = dict(zip(headers, data))
                            
                            # Проверяем основные значения
                            checks = [
                                ('post_title', 'Термостат Ballu Evolution'),
                                ('sku', 'BMT-2'),
                                ('post_status', 'publish'),
                                ('comment_status', 'closed'),
                                ('post_author', '2'),
                            ]
                            
                            for field, expected_part in checks:
                                if field in data_dict:
                                    value = data_dict[field]
                                    if expected_part in value:
                                        logger.info(f"✓ Поле '{field}' содержит '{expected_part}'")
                                    else:
                                        logger.warning(f"✗ Поле '{field}': '{value}' (ожидалось '{expected_part}')")
                                else:
                                    logger.warning(f"✗ Поле '{field}' отсутствует в данных")
                        
                        # Проверяем атрибуты в данных
                        if len(data) > 0 and len(headers) > 0:
                            data_dict = dict(zip(headers, data))
                            
                            # Проверяем основные атрибуты
                            main_attrs_to_check = [
                                'attribute:pa_placement',
                                'attribute:pa_application',
                                'attribute:pa_color',
                                'attribute:pa_country',
                                'attribute:pa_power'
                            ]
                            
                            for attr_field in main_attrs_to_check:
                                if attr_field in data_dict:
                                    value = data_dict[attr_field]
                                    if value:
                                        logger.info(f"✓ Атрибут '{attr_field}': '{value}'")
                                    else:
                                        logger.warning(f"✗ Атрибут '{attr_field}' пустой")
                                else:
                                    logger.warning(f"✗ Атрибут '{attr_field}' отсутствует")
        
        # Очистка
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        
        logger.info("✓ Тест CSV экспортера завершен")
        return success
        
    except Exception as e:
        logger.error(f"✗ Ошибка тестирования CSV экспортера: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        
        return False


def test_full_pipeline():
    """Тест полного pipeline"""
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ 5: Полный pipeline обработки")
    logger.info("="*60)
    
    try:
        # 1. Тест парсера характеристик
        parser, grouped, wc_attrs = test_attribute_parser()
        
        # 2. Тест сборщика описаний
        builder, description_result = test_description_builder()
        
        # 3. Тест конфигурации полей
        wc_fields, default_row = test_wc_fields_config()
        
        # 4. Тест CSV экспортера
        csv_success = test_csv_exporter()
        
        # Итоговая проверка
        logger.info("\n" + "="*60)
        logger.info("ИТОГОВАЯ ПРОВЕРКА СИСТЕМЫ")
        logger.info("="*60)
        
        # Проверяем что атрибуты правильно разделяются
        test_product = create_real_test_product()
        characteristics = test_product['characteristics_raw']
        
        wc_attrs = parser.extract_wc_attributes(characteristics)
        attributes_count = len(wc_attrs.get('attributes', {}))
        
        # WC атрибуты должны быть в описании
        html = builder.build_full_description(test_product)['post_content']
        
        # Ключевые проверки
        checks = [
            ("WC атрибутов извлечено", attributes_count > 5, f"{attributes_count} атрибутов"),
            ("Атрибуты в описании", 'Область применения' in html, "есть в HTML"),
            ("Якорь характеристик", 'id="product-characteristics"' in html, "добавлен"),
            ("Разделитель CSV", ';' in get_wc_fields()[0] if get_wc_fields() else False, "; используется"),
            ("Нет ненужных атрибутов", not any('proizvoditel' in field for field in get_wc_fields()), "очищено"),
        ]
        
        all_passed = True
        for check_name, condition, details in checks:
            status = "✓" if condition else "✗"
            logger.info(f"{status} {check_name}: {details}")
            if not condition:
                all_passed = False
        
        if all_passed and csv_success:
            logger.info("\n✓ ВСЕ КОМПОНЕНТЫ СИСТЕМЫ РАБОТАЮТ КОРРЕКТНО ✓")
            return True
        else:
            logger.error("\n✗ НЕКОТОРЫЕ КОМПОНЕНТЫ ТРЕБУЮТ ДОРАБОТКИ ✗")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка полного теста: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Основная функция тестирования"""
    logger.info("ПОЛНЫЙ ТЕСТ СИСТЕМЫ B2B-WC-CONVERTER")
    logger.info("Проверка с реальными данными характеристик")
    
    try:
        # Запускаем полный тест
        success = test_full_pipeline()
        
        if success:
            logger.info("\n" + "="*60)
            logger.info("ТЕСТИРОВАНИЕ УСПЕШНО ЗАВЕРШЕНО!")
            logger.info("Система готова к работе с реальными данными.")
            logger.info("="*60)
            return 0
        else:
            logger.error("\n" + "="*60)
            logger.error("ТЕСТИРОВАНИЕ ЗАВЕРШИЛОСЬ С ОШИБКАМИ")
            logger.error("Требуется доработка компонентов.")
            logger.info("="*60)
            return 1
            
    except Exception as e:
        logger.error(f"Критическая ошибка тестирования: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())