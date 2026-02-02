"""
Финальный тест всего проекта B2B-WC Converter v2.0.
Проверяет полный цикл конвертации от CSV до готового файла WooCommerce.
"""
import sys
from pathlib import Path
import csv
import tempfile
import shutil

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from v2.converter import ConverterV2


def create_comprehensive_test_csv() -> Path:
    """
    Создает комплексный тестовый CSV файл со всеми типами данных.
    """
    test_data = """Наименование;Артикул;НС-код;Бренд;Название категории;Характеристики;Изображение;Видео;Статья;Чертежи;Сертификаты;Промоматериалы;Инструкции;Штрих код;Цена;Эксклюзив
Пластиковый контейнер 10л;PC-10;NS001;PlasticPro;Тара - Контейнеры - Пластиковые;Масса товара (нетто): 0.5 кг / Высота товара: 30 см / Ширина товара: 20 см / Глубина товара: 15 см / Область применения: Хранение / Цвет корпуса: Белый / Страна производства: Россия / Гарантийный срок: 2 года;https://example.com/container1.jpg,https://example.com/container2.jpg;https://youtube.com/watch?v=dQw4w9WgXcQ;<h2>Пластиковый контейнер 10л</h2><p>Идеальное решение для хранения продуктов и вещей. Герметичная крышка обеспечивает защиту от влаги и запахов.</p>;https://example.com/drawing.pdf;https://example.com/certificate.pdf;https://example.com/promo.pdf;https://example.com/instructions.pdf;5901234123457/5901234123458;"14990 руб.";"Эксклюзив - Нет"
Металлический шкаф MS-200;MS-200;NS002;MetalWorks;Мебель - Шкафы - Офисные;Масса товара (нетто): 15 кг / Высота товара: 180 см / Ширина товара: 60 см / Глубина товара: 40 см / Область применения: Офис / Цвет корпуса: Серый / Материал: Металл / Страна производства: Россия;https://example.com/cabinet1.jpg,https://example.com/cabinet2.jpg,https://example.com/cabinet3.jpg;;<p>Прочный металлический шкаф для офиса. Вместительные полки, надежные замки.</p>;;;;;9781234567890;"24500 руб.";"Эксклюзив - Да"
Электрический чайник 1.7л;EK-170;NS003;ElectroHome;Бытовая техника - Кухонная - Чайники;Мощность: 2200 Вт / Объем: 1.7 л / Напряжение: 220 В / Цвет: Белый / Материал корпуса: Пластик / Материал нагревателя: Нержавеющая сталь;https://example.com/kettle.jpg;https://youtu.be/abcdefghijk;<p>Быстрый электрический чайник с автоматическим отключением.</p>;;https://example.com/certificate_tech.pdf;;;1234567890123;"3990 руб.";"Эксклюзив - нет"
Товар без изображений;NO-IMG;NS004;TestBrand;Категория - Тестовая;Вес: 1 кг / Цвет: Черный;;;;<p>Товар без изображений для тестирования.</p>;;;;;;"5000 руб.";"Эксклюзив - Нет"
Товар с ошибкой (без названия);ERROR-001;NS005;Brand;;Характеристики;;;;<p>Товар с ошибкой</p>;;;;;;"1000 руб.";"Эксклюзив - Нет"
"""
    
    # Создаем временный файл
    temp_dir = tempfile.mkdtemp()
    csv_path = Path(temp_dir) / "final_test.csv"
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(test_data)
    
    print(f"📁 Тестовый CSV создан: {csv_path}")
    return csv_path, temp_dir


def test_complete_conversion():
    """Тестирует полный цикл конвертации."""
    print("\n" + "="*60)
    print("🚀 ФИНАЛЬНЫЙ ТЕСТ B2B-WC CONVERTER v2.0")
    print("="*60)
    
    csv_path, temp_dir = None, None
    
    try:
        # Создаем тестовый CSV
        csv_path, temp_dir = create_comprehensive_test_csv()
        
        # Инициализируем конвертер
        print("\n🔄 Инициализация конвертера...")
        converter = ConverterV2(config_path="config/v2")
        
        # Определяем путь для выходного файла
        output_path = "data/output/final_conversion_test.csv"
        
        # Запускаем конвертацию
        print("⚙️  Запуск конвертации...")
        result = converter.convert(
            input_path=str(csv_path),
            output_path=output_path,
            skip_errors=True
        )
        
        # Выводим результаты
        print("\n📊 РЕЗУЛЬТАТЫ КОНВЕРТАЦИИ:")
        print("-" * 40)
        print(f"✅ Обработано товаров: {result['processed']}")
        print(f"⚠️  Пропущено товаров: {result['skipped']}")
        print(f"❌ Ошибок: {result['errors']}")
        print(f"📁 Выходной файл: {result['output_path']}")
        print(f"⏱️  Время выполнения: {result['duration']:.2f} секунд")
        print(f"📈 Успешность: {(result['processed'] / max(1, result['processed'] + result['skipped']) * 100):.1f}%")
        
        # Анализируем выходной файл
        print("\n🔍 АНАЛИЗ ВЫХОДНОГО ФАЙЛА:")
        print("-" * 40)
        
        output_file = Path(result['output_path'])
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                
                if rows:
                    print(f"📄 Строк в CSV: {len(rows)}")
                    print(f"📊 Колонок в CSV: {len(rows[0])}")
                    
                    # Анализируем первую строку
                    first_row = rows[0]
                    
                    print("\n📋 ПЕРВАЯ СТРОКА (ключевые поля):")
                    print("-" * 40)
                    
                    key_fields = [
                        ('post_title', 'Название'),
                        ('sku', 'SKU'),
                        ('regular_price', 'Цена'),
                        ('tax:product_cat', 'Категория'),
                        ('post_content', 'Контент'),
                        ('images', 'Изображения'),
                        ('weight', 'Вес'),
                        ('attribute:pa_tsvet-korpusa', 'Цвет')
                    ]
                    
                    for field, description in key_fields:
                        value = first_row.get(field, '')
                        if value:
                            if field == 'post_content':
                                print(f"  📝 {description}: HTML ({len(value)} символов)")
                            elif field == 'images':
                                image_count = len(value.split(' :: ')) if value else 0
                                print(f"  🖼️  {description}: {image_count} изображений")
                            else:
                                print(f"  ✅ {description}: {value[:50]}{'...' if len(value) > 50 else ''}")
                        else:
                            print(f"  ⚠️  {description}: отсутствует")
                    
                    # Проверяем SEO поля
                    print("\n🔍 SEO ПОЛЯ:")
                    print("-" * 40)
                    
                    seo_fields = [k for k in first_row.keys() if 'yoast' in k]
                    filled_seo = 0
                    placeholder_seo = 0
                    
                    for field in seo_fields[:5]:  # Проверяем первые 5 SEO полей
                        value = first_row.get(field, '')
                        if value:
                            if '{' in value and '}' in value:
                                placeholder_seo += 1
                            else:
                                filled_seo += 1
                    
                    print(f"  📈 Всего SEO полей: {len(seo_fields)}")
                    print(f"  ✅ Заполненных: {filled_seo}")
                    print(f"  ⚠️  С плейсхолдерами: {placeholder_seo}")
                    
                    # Проверяем атрибуты
                    print("\n🏷️  АТРИБУТЫ WOOCOMMERCE:")
                    print("-" * 40)
                    
                    attr_fields = [k for k in first_row.keys() if k.startswith('attribute:')]
                    print(f"  📊 Атрибутов WooCommerce: {len(attr_fields)}")
                    
                    for attr in attr_fields[:3]:  # Показываем первые 3
                        value = first_row.get(attr, '')
                        if value:
                            print(f"  ✅ {attr.split(':')[-1]}: {value}")
                    
                    # Проверяем мета-поля
                    print("\n📌 МЕТА-ПОЛЯ:")
                    print("-" * 40)
                    
                    meta_fields = [k for k in first_row.keys() if k.startswith('meta:') and 'yoast' not in k]
                    print(f"  📊 Пользовательских мета-полей: {len(meta_fields)}")
                    
                    for meta in meta_fields[:3]:  # Показываем первые 3
                        value = first_row.get(meta, '')
                        if value:
                            print(f"  ✅ {meta.split(':')[-1]}: {value[:30]}{'...' if len(value) > 30 else ''}")
        
        # Очистка
        converter.cleanup()
        
        print("\n" + "="*60)
        print("🎉 ФИНАЛЬНЫЙ ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("="*60)
        
        # Рекомендации
        print("\n📋 РЕКОМЕНДАЦИИ:")
        print("-" * 40)
        print("1. Проверьте выходной файл в Excel или текстовом редакторе")
        print("2. Убедитесь, что все поля заполнены корректно")
        print("3. Проверьте SEO поля на наличие плейсхолдеров")
        print("4. Протестируйте импорт в WooCommerce через WebToffee")
        print("5. При необходимости настройте конфигурационные файлы")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ПРИ ТЕСТИРОВАНИИ: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Очистка временных файлов
        if temp_dir and Path(temp_dir).exists():
            try:
                shutil.rmtree(temp_dir)
                print(f"\n🗑️  Временные файлы очищены")
            except:
                pass


def validate_configuration():
    """Проверяет конфигурационные файлы."""
    print("\n🔧 ПРОВЕРКА КОНФИГУРАЦИИ:")
    print("-" * 40)
    
    try:
        from v2.config_manager import ConfigManager
        
        config = ConfigManager.from_directory("config/v2")
        
        # Проверяем основные секции
        checks = [
            ("settings.json", bool(config.settings)),
            ("field_mapping.json", len(config.field_mapping) > 0),
            ("attribute_mapping.json", len(config.attribute_mapping) > 0),
            ("seo_templates.json", len(config.seo_templates) > 0)
        ]
        
        all_ok = True
        for file_name, condition in checks:
            if condition:
                print(f"✅ {file_name}: OK")
            else:
                print(f"❌ {file_name}: ПРОБЛЕМА")
                all_ok = False
        
        # Проверяем ключевые настройки
        print("\n📋 КЛЮЧЕВЫЕ НАСТРОЙКИ:")
        print("-" * 40)
        
        key_settings = [
            ('paths.local_image_download', 'Папка для изображений'),
            ('paths.final_image_url_template', 'Шаблон URL изображений'),
            ('processing.skip_on_error', 'Пропуск ошибок'),
            ('default_values.post_status', 'Статус товара')
        ]
        
        for setting_path, description in key_settings:
            value = config.get_setting(setting_path)
            if value is not None:
                print(f"✅ {description}: {value}")
            else:
                print(f"⚠️  {description}: не установлено")
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Ошибка при проверке конфигурации: {e}")
        return False


def main():
    """Главная функция тестирования."""
    print("\n" + "="*60)
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ B2B-WC CONVERTER v2.0")
    print("="*60)
    
    # Проверяем конфигурацию
    config_ok = validate_configuration()
    
    if not config_ok:
        print("\n⚠️  Проблемы с конфигурацией. Исправьте перед тестированием.")
        return
    
    # Запускаем полный тест
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ПОЛНОГО ТЕСТА КОНВЕРТАЦИИ")
    print("="*60)
    
    result = test_complete_conversion()
    
    if result and result['processed'] > 0:
        print("\n🎯 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n📋 ДАЛЬНЕЙШИЕ ШАГИ:")
        print("1. Используйте run_v2.py для конвертации ваших CSV файлов")
        print("2. Настройте config/v2/ под ваши нужды")
        print("3. Проверьте импорт в WooCommerce")
        print("4. При необходимости доработайте обработчики")
    else:
        print("\n⚠️  ТЕСТИРОВАНИЕ ЗАВЕРШИЛОСЬ С ПРОБЛЕМАМИ")
        print("Проверьте логи и конфигурационные файлы.")


if __name__ == "__main__":
    main()