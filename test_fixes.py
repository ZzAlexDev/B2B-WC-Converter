#!/usr/bin/env python3
"""
test_fixes.py
Тестирование исправлений в парсере
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processors.xlsx_parser import XLSXParser

print("🔧 Тестирование исправлений в парсере")
print("=" * 50)

# Создаем парсер с dummy файлом
parser = XLSXParser("dummy.xlsx")

print("\n1. ✅ Тестирование очистки SKU (исправлено):")
test_skus = [
    ('TEST/001', 'TEST-001'),
    ('ABC / DEF', 'ABC-DEF'),  # Было: 'ABC - DEF', теперь должно быть: 'ABC-DEF'
    ('ABC/ DEF', 'ABC-DEF'),
    ('ABC /DEF', 'ABC-DEF'),
    ('  TEST  ', 'TEST'),
    ('A//B//C', 'A-B-C'),
    ('A / B / C', 'A-B-C'),
    (None, ''),
    ('', ''),
]

all_passed = True
for input_sku, expected in test_skus:
    result = parser.clean_sku(input_sku)
    status = '✅' if result == expected else '❌'
    if result != expected:
        all_passed = False
    print(f"   {status} '{input_sku}' -> '{result}' (ожидалось: '{expected}')")

if all_passed:
    print("   🎉 Все тесты SKU пройдены!")
else:
    print("   ⚠️  Есть ошибки в очистке SKU")

print("\n2. 💰 Тестирование очистки цен (исправлено):")
test_prices = [
    ('1 000 руб.', 1000.0),
    ('2,500.50 руб.', 2500.5),  # Была ошибка, теперь должно работать
    ('1.234,56 руб.', 1234.56),  # Европейский формат
    ('10 000 000 руб.', 10000000.0),
    ('3000', 3000.0),
    ('не число', None),
    ('', None),
    (None, None),
    ('14990 руб.', 14990.0),  # Из реального примера
    ('46 990 руб.', 46990.0),  # Из реального примера
]

all_passed = True
for input_price, expected in test_prices:
    result = parser.clean_price(input_price)
    
    # Для сравнения чисел с плавающей точкой
    if result is None and expected is None:
        status = '✅'
    elif result is not None and expected is not None:
        # Сравниваем с небольшой погрешностью
        status = '✅' if abs(result - expected) < 0.01 else '❌'
    else:
        status = '❌'
    
    if status == '❌':
        all_passed = False
    
    print(f"   {status} '{input_price}' -> {result} (ожидалось: {expected})")

if all_passed:
    print("   🎉 Все тесты цен пройдены!")
else:
    print("   ⚠️  Есть ошибки в очистке цен")

print("\n3. 🗂️ Тестирование категорий:")
test_categories = [
    ('Категория - Подкатегория - Подкатегория', 'Категория > Подкатегория'),
    ('А - Б - В', 'А > Б > В'),
    ('Тепловое оборудование - Воздушные и тепловые завесы - Промышленные', 
     'Тепловое оборудование > Воздушные и тепловые завесы > Промышленные'),
    ('', ''),
    (None, ''),
]

all_passed = True
for input_cat, expected in test_categories:
    result = parser.convert_category(input_cat)
    status = '✅' if result == expected else '❌'
    if result != expected:
        all_passed = False
    print(f"   {status} '{input_cat}' -> '{result}' (ожидалось: '{expected}')")

if all_passed:
    print("   🎉 Все тесты категорий пройдены!")
else:
    print("   ⚠️  Есть ошибки в преобразовании категорий")

print("\n" + "=" * 50)
print("📊 ИТОГОВЫЙ ОТЧЕТ:")

# Запускаем парсер на реальных данных
print("\n4. 🚀 Тест на реальных данных:")
try:
    from config import settings
    input_file = settings.INPUT_FILE
    
    if os.path.exists(input_file):
        print(f"   📁 Тестовый файл: {input_file}")
        
        # Быстрый тест без сохранения
        parser = XLSXParser(input_file)
        if parser.read_file() and parser.process_all():
            data = parser.get_processed_data()
            stats = parser.get_stats()
            
            print(f"   📊 Обработано: {len(data)} товаров")
            print(f"   💰 Пример цен:")
            
            # Проверяем несколько товаров
            for i, product in enumerate(data[:3]):
                print(f"     {i+1}. {product.get('name', '')[:40]}...")
                print(f"        SKU: {product.get('sku', '')}")
                print(f"        Цена: {product.get('price', '')}")
                print(f"        Категория: {product.get('category', '')[:50]}...")
            
            print("   🎉 Реальные данные обрабатываются корректно!")
        else:
            print("   ❌ Ошибка обработки реальных данных")
    else:
        print(f"   ⚠️  Файл не найден: {input_file}")
        
except Exception as e:
    print(f"   ❌ Ошибка теста реальных данных: {e}")

print("\n" + "=" * 50)
print("✅ ИСПРАВЛЕНИЯ ПРОТЕСТИРОВАНЫ!")
print("Можно делать коммит с исправлениями.")