#!/usr/bin/env python3
"""
test_docs_with_product_name.py
Тестирование названий документов с именем товара
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processors.description_builder import DescriptionBuilder

print("🔧 Тестирование названий документов с именем товара")
print("=" * 50)

builder = DescriptionBuilder()

print("\n1. 📄 Тестирование создания имен документов...")
test_cases = [
    ('Чертежи', 'Конвектор электрический Ballu IP 54 BEC/CMR-2000', 'Чертеж Конвектор электрический Ballu IP 54 BEC CMR 2000'),
    ('Инструкции', 'Рукосушилка Electrolux EHDA-2500', 'Инструкция Рукосушилка Electrolux EHDA 2500'),
    ('Сертификаты', 'Завеса воздушная Ballu BHC-U15A-PS', 'Сертификат Завеса воздушная Ballu BHC U15A PS'),
    ('', 'Товар с очень длинным названием которое нужно обрезать потому что оно слишком длинное для отображения', 'Документ Товар с очень длинным названием которое нужно обрезать'),
]

for doc_type, product_name, expected in test_cases:
    result = builder._create_readable_filename('', doc_type, product_name)
    status = '✅' if result == expected else '❌'
    print(f"   {status} '{doc_type}' + '{product_name[:30]}...'")
    print(f"       -> '{result}'")
    print(f"       (ожидалось: '{expected}')\n")

print("\n2. 🎯 Пример итогового отображения:")
product_name = "Конвектор электрический Ballu IP 54 BEC/CMR-2000"
test_documents = {
    'Чертежи': 'https://example.com/чертеж.pdf',
    'Инструкции': 'https://example.com/инструкция.pdf',
    'Сертификаты': 'https://example.com/сертификат.pdf',
}

print(f"   Товар: {product_name}")
print(f"   Документы:")

for doc_type, url in test_documents.items():
    doc_name = builder._create_readable_filename('', doc_type, product_name)
    print(f"   • {doc_type}: {doc_name} (PDF)")

print("\n3. 🔍 Проверка полной секции документации с именем товара...")
try:
    test_docs_data = {
        'Чертежи': 'https://rkcdn.ru/products/e9b7a651-8718-11f0-b8e0-00505601218a/src.pdf',
        'Инструкции': 'https://rkcdn.ru/products/adbbd62c-54d0-11ef-b8d9-00505601218a/src.pdf',
    }
    
    html_section = builder.build_documents_section(test_docs_data, product_name)
    
    if html_section:
        print(f"   ✅ HTML секция создана: {len(html_section)} символов")
        
        # Сохраняем для просмотра
        with open('output/test_docs_with_product_name.html', 'w', encoding='utf-8') as f:
            f.write(html_section)
        print(f"   💾 Сохранено в: output/test_docs_with_product_name.html")
        
        # Показываем превью ссылок
        print(f"   📋 Превью ссылок:")
        lines = html_section.split('\n')
        for line in lines:
            if '<a href=' in line:
                # Извлекаем текст ссылки
                import re
                match = re.search(r'<a[^>]*>([^<]+)</a>', line)
                if match:
                    print(f"     • {match.group(1)}")
    else:
        print("   ❌ Не удалось создать секцию")
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🎯 Теперь документы будут содержать название товара!")
print("   Пример: 'Чертеж Конвектор электрический Ballu IP 54 BEC CMR 2000 (PDF)'")