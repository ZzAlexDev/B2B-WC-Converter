#!/usr/bin/env python3
"""
test_quick_fix.py
Быстрая проверка исправлений
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processors.attribute_parser import AttributeParser

print("🔧 Быстрая проверка исправлений")
print("=" * 50)

parser = AttributeParser()

# Тест 1: Проверка метода
print("\n1. Проверка метода _format_value_for_display:")
test_cases = [
    ('yes', 'Да'),
    ('no', 'Нет'),
    ('true', 'Да'),
    ('false', 'Нет'),
    ('да', 'Да'),
    ('нет', 'Нет'),
    ('Другое', 'Другое'),
    ('', ''),
]

for input_val, expected in test_cases:
    try:
        result = parser._format_value_for_display(input_val)
        status = '✅' if result == expected else '❌'
        print(f"   {status} '{input_val}' -> '{result}'")
    except AttributeError:
        print(f"   ❌ Метод _format_value_for_display не найден!")
        break

# Тест 2: Проверка полного форматирования
print("\n2. Проверка format_for_description:")
test_str = "Цвет: Белый; Защита: Да; Управление: Нет; Статус: true"
try:
    html = parser.format_for_description(test_str)
    print(f"   HTML создан: {len(html)} символов")
    
    # Проверяем преобразования
    if 'Да' in html and 'Нет' in html:
        print("   ✅ Boolean преобразованы: Да/Нет")
    else:
        print("   ❌ Boolean не преобразованы")
        
    if 'true' not in html.lower() and 'false' not in html.lower():
        print("   ✅ Английские boolean удалены")
    else:
        print("   ❌ Английские boolean остались")
        
    # Показываем результат
    print(f"   Результат:")
    for line in html.split('\n')[:4]:
        if line.strip():
            print(f"   {line}")
            
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n" + "=" * 50)
print("🎯 Если все тесты пройдены - исправления работают!")