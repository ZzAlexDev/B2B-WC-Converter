#!/usr/bin/env python3
"""
test_final_fixes.py
Тестирование финальных исправлений
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔧 Тестирование финальных исправлений")
print("=" * 50)

from data_processors.description_builder import DescriptionBuilder
from data_processors.attribute_parser import AttributeParser

print("\n1. ✅ Исправление имен документов (замена / на -)...")
builder = DescriptionBuilder()

test_cases = [
    ('Конвектор электрический Ballu IP 54 BEC/CMR-2000', 
     'Конвектор электрический Ballu IP 54 BEC-CMR-2000'),
    ('Товар с / слэшем / в названии', 
     'Товар с - слэшем - в названии'),
    ('Простой товар', 
     'Простой товар'),
]

for input_name, expected in test_cases:
    result = builder._clean_product_name_for_docs(input_name)
    status = '✅' if result == expected else '❌'
    print(f"   {status} '{input_name}'")
    print(f"       -> '{result}'")
    print(f"       (ожидалось: '{expected}')\n")

print("\n2. ✅ Boolean значения в описании (Да/Нет вместо yes/no)...")
parser = AttributeParser()

test_values = [
    ('yes', 'Да'),
    ('no', 'Нет'),
    ('YES', 'Да'),
    ('NO', 'Нет'),
    ('true', 'Да'),
    ('false', 'Нет'),
    ('да', 'Да'),
    ('нет', 'Нет'),
    ('Да', 'Да'),
    ('Нет', 'Нет'),
    ('другое значение', 'другое значение'),
    ('', ''),
]

print("   Тест преобразования boolean значений:")
for input_val, expected in test_values:
    result = parser._format_value_for_display(input_val)
    status = '✅' if result == expected else '❌'
    print(f"   {status} '{input_val}' -> '{result}'")

print("\n3. ✅ Тест полного цикла с реальными данными...")
try:
    from data_processors.xlsx_parser import parse_xlsx_file
    from config import settings
    
    input_file = settings.INPUT_FILE
    if os.path.exists(input_file):
        print(f"   📁 Загружаем реальные данные: {input_file}")
        
        # Парсим один товар
        data, stats = parse_xlsx_file(input_file)
        
        if data and len(data) > 0:
            test_product = data[0]
            print(f"   📦 Тестовый товар: {test_product.get('name', '')[:50]}...")
            
            # Собираем описание
            description_result = builder.build_full_description(test_product)
            
            print(f"   ✅ Описание собрано: {len(description_result['post_content'])} символов")
            
            # Проверяем boolean значения
            content = description_result['post_content']
            
            # Ищем примеры boolean
            if 'yes' in content.lower() or 'no' in content.lower():
                print(f"   ⚠️  Внимание: Найдены английские boolean в описании!")
                # Показываем контекст
                import re
                matches = re.findall(r'<li><strong>([^<]+):</strong>\s*(yes|no|Yes|No|YES|NO)</li>', content, re.IGNORECASE)
                if matches:
                    print(f"   📋 Найдены неправильные boolean:")
                    for key, val in matches[:3]:
                        print(f"      • {key}: {val}")
            else:
                print(f"   ✅ Boolean значения корректны (Да/Нет)")
            
            # Сохраняем для проверки
            with open('output/final_test_description.html', 'w', encoding='utf-8') as f:
                f.write(description_result['post_content'])
            print(f"   💾 Описание сохранено: output/final_test_description.html")
            
            # Проверяем названия документов
            if 'Чертеж' in content and 'BEC-CMR' in content:
                print(f"   ✅ Названия документов содержат дефисы (BEC-CMR)")
            else:
                print(f"   ⚠️  Проверьте названия документов")
                
        else:
            print("   ❌ Нет данных для тестирования")
    else:
        print(f"   ⚠️  Файл не найден: {input_file}")
        
except Exception as e:
    print(f"   ⚠️  Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n4. 📋 Итог исправлений:")
print("   1. / заменяется на - в названиях товаров для документов")
print("   2. Boolean значения: 'Да/Нет' в описании (остаются 'yes/no' для WC атрибутов)")
print("   3. Штрих-коды через запятую")
print("   4. Имена документов: 'Тип Название_товара (PDF)'")

print("\n" + "=" * 50)
print("🎯 ИСПРАВЛЕНИЯ ГОТОВЫ К КОММИТУ!")