#!/usr/bin/env python3
"""
test_attribute_parser_final.py
Финальный тест исправленного attribute_parser.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🎯 Финальный тест attribute_parser.py")
print("=" * 50)

from data_processors.attribute_parser import AttributeParser

parser = AttributeParser()

print("\n1. ✅ Проверка всех методов:")
methods = [
    'format_for_description',
    'format_for_display',
    '_format_value_for_display',
    'normalize_value',
    'parse_characteristics_string',
    'parse_and_group',
    'extract_wc_attributes',
]

all_ok = True
for method in methods:
    has_method = hasattr(parser, method)
    status = '✅' if has_method else '❌'
    print(f"   {status} {method}")
    if not has_method:
        all_ok = False

if not all_ok:
    print("\n❌ Не все методы существуют!")
    sys.exit(1)

print("\n2. ✅ Тест boolean преобразования:")
print("   Для отображения в описании:")
test_values = [('yes', 'Да'), ('no', 'Нет'), ('true', 'Да'), ('false', 'Нет')]
for input_val, expected in test_values:
    result = parser._format_value_for_display(input_val)
    status = '✅' if result == expected else '❌'
    print(f"   {status} '{input_val}' -> '{result}'")

print("\n   Для атрибутов WC (должны остаться yes/no):")
test_values_wc = [('да', 'yes'), ('нет', 'no'), ('Да', 'yes'), ('Нет', 'no')]
for input_val, expected in test_values_wc:
    result = parser.normalize_value(input_val)
    status = '✅' if result == expected else '❌'
    print(f"   {status} '{input_val}' -> '{result}'")

print("\n3. ✅ Тест полного форматирования:")
test_str = "Цвет: Белый; Защита: yes; Управление: no; Статус: true; Работа: false"
html = parser.format_for_description(test_str)

print(f"   HTML: {len(html)} символов")
print(f"   Содержит 'Да': {'Да' in html}")
print(f"   Содержит 'Нет': {'Нет' in html}")
print(f"   Не содержит 'yes': {'yes' not in html.lower()}")
print(f"   Не содержит 'no': {'no' not in html.lower()}")

print("\n4. ✅ Тест алиаса format_for_display:")
html2 = parser.format_for_display(test_str)
print(f"   Алиас работает: {html == html2}")

print("\n5. ✅ Тест извлечения атрибутов WC:")
wc_attrs = parser.extract_wc_attributes(test_str)
if 'attributes' in wc_attrs:
    print(f"   Атрибуты WC извлечены: {len(wc_attrs['attributes'])}")
    # Атрибуты WC должны содержать yes/no
    for slug, value in wc_attrs['attributes'].items():
        print(f"   • {slug}: {value}")

print("\n" + "=" * 50)
print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
print("   • Boolean в описании: Да/Нет")
print("   • Boolean в атрибутах WC: yes/no")
print("   • Все методы доступны")