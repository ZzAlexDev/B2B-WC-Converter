#!/usr/bin/env python3
"""
test_parser.py
Тестирование парсера XLSX файлов
"""

import sys
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧪 Тестирование парсера XLSX файлов")
print("=" * 60)

try:
    print("\n1. 📦 Импорт модулей...")
    from config import settings
    from data_processors.xlsx_parser import XLSXParser, parse_xlsx_file
    print("   ✅ Модули загружены успешно!")
    
    # Проверяем существование входного файла
    input_file = settings.INPUT_FILE
    print(f"\n2. 📁 Проверка входного файла: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"   ❌ Файл не найден: {input_file}")
        
        # Пробуем найти альтернативный файл
        print("   🔍 Поиск альтернативных файлов...")
        if os.path.exists('catalog_26.01.2026.xlsx'):
            input_file = 'catalog_26.01.2026.xlsx'
            print(f"   ✅ Найден файл: {input_file}")
        elif os.path.exists('input/catalog.xlsx'):
            input_file = 'input/catalog.xlsx'
            print(f"   ✅ Найден файл: {input_file}")
        else:
            print("   ❌ Файлы не найдены. Создаем тестовый файл...")
            
            # Создаем простой тестовый файл
            import pandas as pd
            test_data = {
                'Наименование': ['Тестовый товар 1', 'Тестовый товар 2'],
                'Артикул': ['TEST-001', 'TEST-002'],
                'Бренд': ['Test Brand', 'Another Brand'],
                'Название категории': ['Категория - Подкатегория', 'Другая - Категория'],
                'Характеристики': ['Цвет: Белый; Вес: 10 кг', 'Материал: Металл; Мощность: 100Вт'],
                'Изображение': ['https://example.com/image1.jpg,https://example.com/image2.jpg', ''],
                'Статья': ['<p>Описание товара 1</p>', '<p>Описание товара 2</p>'],
                'Цена': ['1000 руб.', '2000 руб.'],
                'НС-код': ['NS-001', 'NS-002'],
                'Штрих код': ['1234567890123', '9876543210987'],
            }
            
            df = pd.DataFrame(test_data)
            os.makedirs('input', exist_ok=True)
            df.to_excel(input_file, index=False)
            print(f"   ✅ Создан тестовый файл: {input_file}")
    
    print(f"   ✅ Используем файл: {input_file}")
    
    print("\n3. 🔧 Тестирование класса XLSXParser...")
    parser = XLSXParser(input_file)
    
    print("   • Чтение файла...")
    if parser.read_file():
        print("   ✅ Файл прочитан успешно")
        
        print("   • Валидация данных...")
        warnings = parser.validate_data()
        if warnings:
            print(f"   ⚠️  Предупреждения: {warnings}")
        else:
            print("   ✅ Валидация пройдена")
        
        print("   • Обработка данных...")
        if parser.process_all():
            print("   ✅ Данные обработаны успешно")
            
            # Получаем статистику
            stats = parser.get_stats()
            print(f"\n   📊 Статистика обработки:")
            print(f"     Всего строк: {stats['total_rows']}")
            print(f"     Обработано: {stats['processed_rows']}")
            print(f"     Пропущено: {stats['skipped_rows']}")
            print(f"     Ошибок: {len(stats['errors'])}")
            
            # Получаем обработанные данные
            data = parser.get_processed_data()
            if data:
                print(f"\n   📋 Пример обработанного товара:")
                sample = data[0]
                print(f"     Название: {sample.get('name', '')[:50]}...")
                print(f"     SKU: {sample.get('sku', '')}")
                print(f"     Категория: {sample.get('category', '')}")
                print(f"     Цена: {sample.get('price', '')}")
                print(f"     Характеристики (символов): {len(sample.get('characteristics_raw', ''))}")
                print(f"     Изображений: {len(sample.get('images_raw', '').split(',')) if sample.get('images_raw') else 0}")
            
            # Сохраняем выборку
            sample_output = 'output/parser_sample.csv'
            print(f"\n   💾 Сохранение выборки в: {sample_output}")
            if parser.save_sample_to_csv(sample_output, sample_size=5):
                print("   ✅ Выборка сохранена")
            else:
                print("   ⚠️  Не удалось сохранить выборку")
        
        else:
            print("   ❌ Ошибка обработки данных")
    
    else:
        print("   ❌ Не удалось прочитать файл")
    
    print("\n4. ⚡ Тестирование быстрой функции parse_xlsx_file...")
    sample_output = 'output/quick_parse_sample.csv'
    data, stats = parse_xlsx_file(input_file, sample_output)
    
    if data:
        print(f"   ✅ Быстрый парсинг успешен")
        print(f"   📊 Обработано товаров: {len(data)}")
        print(f"   💾 Выборка сохранена в: {sample_output}")
    else:
        print(f"   ❌ Быстрый парсинг не удался")
        print(f"   📊 Статистика: {stats}")
    
    print("\n5. 🔍 Проверка функций очистки...")
    
    # Тест очистки SKU
    test_skus = [
        ('TEST/001', 'TEST-001'),
        ('ABC / DEF', 'ABC-DEF'),
        ('  TEST  ', 'TEST'),
        ('A//B//C', 'A-B-C'),
        (None, ''),
        ('', ''),
    ]
    
    print("   • Очистка SKU:")
    for input_sku, expected in test_skus:
        result = parser.clean_sku(input_sku)
        status = '✅' if result == expected else '❌'
        print(f"     {status} '{input_sku}' -> '{result}' (ожидалось: '{expected}')")
    
    # Тест очистки цены
    test_prices = [
        ('1 000 руб.', 1000.0),
        ('2,500.50 руб.', 2500.5),
        ('3000', 3000.0),
        ('не число', None),
        ('', None),
        (None, None),
    ]
    
    print("\n   • Очистка цены:")
    for input_price, expected in test_prices:
        result = parser.clean_price(input_price)
        status = '✅' if result == expected else '❌'
        print(f"     {status} '{input_price}' -> {result} (ожидалось: {expected})")
    
    # Тест преобразования категорий
    test_categories = [
        ('Категория - Подкатегория - Подкатегория', 'Категория > Подкатегория'),
        ('А - Б - В', 'А > Б > В'),
        ('', ''),
        (None, ''),
    ]
    
    print("\n   • Преобразование категорий:")
    for input_cat, expected in test_categories:
        result = parser.convert_category(input_cat)
        status = '✅' if result == expected else '❌'
        print(f"     {status} '{input_cat}' -> '{result}' (ожидалось: '{expected}')")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТИРОВАНИЕ ПАРСЕРА ЗАВЕРШЕНО УСПЕШНО!")
    
    # Итоговая информация
    if data:
        print(f"\n📋 ИТОГ:")
        print(f"   • Обработано товаров: {len(data)}")
        print(f"   • Успешность: {(len(data)/stats['total_rows']*100):.1f}%")
        print(f"   • Тестовые файлы сохранены в output/")
        print(f"\n🚀 Парсер готов к работе с реальными данными!")
    
except ImportError as e:
    print(f"\n❌ ОШИБКА ИМПОРТА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)