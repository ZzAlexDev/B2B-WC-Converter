#!/usr/bin/env python3
"""
test_check_methods.py
Проверка наличия всех методов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processors.attribute_parser import AttributeParser
from data_processors.description_builder import DescriptionBuilder

print("🔍 Проверка наличия всех методов")
print("=" * 50)

parser = AttributeParser()
builder = DescriptionBuilder()

print("\n1. ✅ Проверка AttributeParser:")
methods = [
    '_format_value_for_display',
    'format_for_description', 
    'format_for_display',
    'parse_characteristics_string',
    'parse_and_group',
    'extract_wc_attributes',
]

for method in methods:
    has_method = hasattr(parser, method)
    status = '✅' if has_method else '❌'
    print(f"   {status} {method}")

print("\n2. ✅ Проверка DescriptionBuilder:")
builder_methods = [
    '_clean_product_name_for_docs',
    'build_characteristics_section',
    'build_documents_section',
    'build_full_description',
]

for method in builder_methods:
    has_method = hasattr(builder, method)
    status = '✅' if has_method else '❌'
    print(f"   {status} {method}")

print("\n3. 🧪 Тест работы методов:")
try:
    # Тест boolean преобразования
    test_value = 'yes'
    result = parser._format_value_for_display(test_value)
    print(f"   • _format_value_for_display('{test_value}') = '{result}'")
    
    # Тест форматирования
    test_str = "Цвет: Белый; Статус: yes; Работа: no"
    html = parser.format_for_description(test_str)
    print(f"   • format_for_description: {len(html)} символов")
    print(f"   • Содержит 'Да/Нет': {'Да' in html and 'Нет' in html}")
    
    # Тест алиаса
    html2 = parser.format_for_display(test_str)
    print(f"   • format_for_display работает: {html == html2}")
    
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n" + "=" * 50)
print("🎯 Если все ✅ - можно делать коммит!")