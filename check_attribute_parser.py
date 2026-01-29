"""
check_attribute_parser.py
Проверка структуры AttributeParser
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processors.attribute_parser import AttributeParser

# Создаем экземпляр
parser = AttributeParser()

# Выводим все методы
print("Методы AttributeParser:")
for method_name in dir(parser):
    if not method_name.startswith('_'):
        print(f"  - {method_name}")

# Проверяем конкретные методы
print("\nПроверка конкретных методов:")
methods_to_check = [
    'normalize_value_for_wc',
    'normalize_value',
    'normalize_value_for_wc',
    '_normalize_value_for_wc'
]

for method in methods_to_check:
    has_method = hasattr(parser, method)
    print(f"  {method}: {'✓' if has_method else '✗'}")