#!/usr/bin/env python3
"""
test_description_builder.py
Тестирование генератора описаний товаров
"""

import sys
import os
import json
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧪 Тестирование генератора описаний товаров")
print("=" * 60)

try:
    print("\n1. 📦 Импорт модулей...")
    from data_processors.description_builder import (
        DescriptionBuilder,
        build_product_description,
        process_products_descriptions
    )
    print("   ✅ Модули загружены успешно!")
    
    print("\n2. 🔧 Создание генератора...")
    builder = DescriptionBuilder()
    print("   ✅ Генератор создан")
    
    # Тестовые данные
    print("\n3. 📝 Тестирование на тестовых данных...")
    
    test_product = {
        'name': 'Конвектор электрический Ballu IP 54 BEC/CMR-2000',
        'sku': 'BEC-CMR-2000',
        'description_raw': '''<p>Электрический конвектор Ballu с Х-образным монолитным нагревательным элементом и пылевлагозащитой IP54 специально предназначен для общественных помещений, в местах с высоким уровнем пыли и влажности.<br />
Антивандальный металлический корпус предохраняет устройство внутренних элементов и сохраняет внешний вид прибора в агрессивных условиях эксплуатации.</p>
<p>Особенности модели:</p>
<ul>
<li>Повышенная надежность корпуса</li>
<li>Электронный термостат и точная установка температуры</li>
<li>Кронштейн в комплекте</li>
<li>Гарантийный срок- 3 года</li>
</ul>
<p>Конвектор подходит для напольного и настенного размещения. В комплекте опоры с креплением конвектора к полу, а так же усиленные кронштейны для монтажа на стену.</p>''',
        'characteristics_raw': '''Аварийное отключение при сильном наклоне или опрокидывании: Да; Блок управления: Встроенный; Вид управления: Механическое; Вид установки (крепления): Напольная / Настенная; Высота товара: 22 см; Высота упаковки товара: 24 см; Гарантийный срок: 3 года; Глубина товара: 12 см; Глубина упаковки товара: 13 см; Длина кабеля: 1.2 м; Защита от перегрева: Да; Индикация работы функции "открытое окно": false; Класс пылевлагозащищенности: IP54; Комплект напольной установки: Да; Комплект настенного крепления: Да; Макс. потребляемая мощность: 2 кВт; Масса товара (нетто): 5.9 кг; Масса товара с упаковкой (брутто): 6.4 кг; Материал корпуса: Металл; Напряжение электропитания, В: 220 - 240 В; Область применения: Промышленное; Серия: IP 54; Сетевой кабель: Да (с вилкой); Срок службы: 7 лет; Страна производства: РОССИЯ; Таймер на отключение: Нет; Тип нагревательного элемента: Х-образный монолитный нагревательный элемент; Тип термостата: Электронный; Управление c мобильного приложения по Wi-Fi: Нет; Функция "открытое окно": false; Цвет корпуса: Белый; Цифровой дисплей: Да; Ширина товара: 94 см; Ширина упаковки товара: 97 см; Эффективен для помещ. площадью до: 25 м2''',
        'documents': {
            'Чертежи': 'https://rkcdn.ru/products/e9b7a651-8718-11f0-b8e0-00505601218a/src.pdf',
            'Сертификаты': 'https://rkcdn.ru/products/adbbd62c-54d0-11ef-b8d9-00505601218a/src.pdf',
            'Инструкции': 'https://rkcdn.ru/products/adbbd62e-54d0-11ef-b8d9-00505601218a/src.pdf',
        },
        'additional_info': {
            'НС-код': 'НС-1659333',
            'Штрих код': '4660294720440 / 7381032480187',
            'Эксклюзив': 'Нет'
        }
    }
    
    print(f"   📋 Тестовый товар: {test_product['name'][:50]}...")
    print(f"   📏 Характеристики: {len(test_product['characteristics_raw'])} символов")
    print(f"   📎 Документов: {len(test_product['documents'])}")
    
    print("\n4. 🛠️ Тестирование отдельных функций...")
    
    # Очистка HTML
    cleaned_html = builder.clean_html_description(test_product['description_raw'])
    print(f"   • Очистка HTML: {len(cleaned_html)} символов")
    
    # Excerpt
    excerpt = builder.extract_excerpt(cleaned_html)
    print(f"   • Excerpt: {excerpt[:100]}...")
    
    # Парсинг документов
    test_docs = "https://example.com/doc1.pdf,https://example.com/manual.docx"
    parsed_docs = builder.parse_document_links(test_docs)
    print(f"   • Парсинг документов: {len(parsed_docs)} документов")
    for doc in parsed_docs:
        print(f"     - {doc['readable_name']}{doc['file_type']}")
    
    print("\n5. 🎨 Тестирование секций...")
    
    # Секция характеристик
    chars_section = builder.build_characteristics_section(test_product['characteristics_raw'])
    print(f"   • Секция характеристик: {len(chars_section)} символов")
    
    # Секция документации
    docs_section = builder.build_documents_section(test_product['documents'])
    print(f"   • Секция документации: {len(docs_section)} символов")
    
    # Секция доп. информации
    info_section = builder.build_additional_info_section(test_product['additional_info'])
    print(f"   • Секция доп. информации: {len(info_section)} символов")
    
    print("\n6. 🏗️ Тестирование полной сборки...")
    result = builder.build_full_description(test_product)
    
    print(f"   ✅ Описание построено успешно!")
    print(f"   📊 Результаты:")
    print(f"     • Длина описания: {len(result['post_content'])} символов")
    print(f"     • Длина excerpt: {len(result['post_excerpt'])} символов")
    print(f"     • Атрибутов WC: {len(result['wc_attributes'].get('attributes', {}))}")
    print(f"     • Извлеченных полей: {len(result['extracted_fields'])}")
    
    if result['wc_attributes'].get('attributes'):
        print(f"     📋 Атрибуты WC:")
        for slug, value in result['wc_attributes']['attributes'].items():
            print(f"       - {slug}: {value}")
    
    if result['extracted_fields']:
        print(f"     📏 Извлеченные поля:")
        for field, value in result['extracted_fields'].items():
            print(f"       - {field}: {value}")
    
    # Сохраняем результат для просмотра
    with open('output/full_description_sample.html', 'w', encoding='utf-8') as f:
        f.write(result['post_content'])
    print(f"   💾 Полное описание сохранено в: output/full_description_sample.html")
    
    # Сохраняем excerpt
    with open('output/excerpt_sample.txt', 'w', encoding='utf-8') as f:
        f.write(result['post_excerpt'])
    print(f"   💾 Excerpt сохранен в: output/excerpt_sample.txt")
    
    print("\n7. ⚡ Тестирование быстрой функции...")
    quick_result = build_product_description(test_product)
    print(f"   ✅ Быстрая функция работает: {len(quick_result['post_content'])} символов")
    
    print("\n8. 🚀 Тестирование на реальных данных...")
    try:
        from data_processors.xlsx_parser import parse_xlsx_file
        from config import settings
        
        input_file = settings.INPUT_FILE
        if os.path.exists(input_file):
            print(f"   📁 Чтение реального файла: {input_file}")
            
            # Парсим только первые 5 товаров для теста
            data, stats = parse_xlsx_file(input_file)
            
            if data and len(data) > 0:
                print(f"   📊 Загружено товаров: {len(data)}")
                
                # Обрабатываем первые 3 товара
                test_products = data[:3]
                print(f"   🔍 Тестируем {len(test_products)} товаров...")
                
                processed = builder.process_batch(test_products)
                
                print(f"   ✅ Обработано: {len(processed)} товаров")
                print(f"   📊 Статистика: {builder.get_stats()}")
                
                # Сохраняем примеры
                for i, product in enumerate(processed[:2]):
                    filename = f"output/real_description_{i+1}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(product.get('post_content', ''))
                    
                    print(f"   💾 Описание товара {i+1} сохранено в: {filename}")
                    
                    # Показываем статистику по товару
                    print(f"     • {product.get('name', '')[:40]}...")
                    print(f"     • Длина описания: {len(product.get('post_content', ''))}")
                    print(f"     • Атрибутов WC: {len(product.get('wc_attributes', {}).get('attributes', {}))}")
                
                # Сохраняем все обработанные товары в JSON для дальнейшего использования
                with open('output/processed_products_sample.json', 'w', encoding='utf-8') as f:
                    json_data = []
                    for product in processed:
                        json_data.append({
                            'name': product.get('name'),
                            'sku': product.get('sku'),
                            'post_content_length': len(product.get('post_content', '')),
                            'wc_attributes': product.get('wc_attributes', {}),
                            'extracted_fields': product.get('extracted_fields', {})
                        })
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                print(f"   💾 JSON с данными сохранен в: output/processed_products_sample.json")
                
            else:
                print("   ⚠️  Нет данных для тестирования")
        else:
            print(f"   ⚠️  Файл не найден: {input_file}")
            
    except Exception as e:
        print(f"   ⚠️  Ошибка теста реальных данных: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n9. 🔬 Тестирование обработки партии...")
    test_batch = [test_product, test_product]  # Два одинаковых для теста
    batch_result = process_products_descriptions(test_batch)
    
    print(f"   ✅ Обработка партии: {len(batch_result)} товаров")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТИРОВАНИЕ ГЕНЕРАТОРА ОПИСАНИЙ ЗАВЕРШЕНО УСПЕШНО!")
    
    print("\n📋 ИТОГОВАЯ СТАТИСТИКА:")
    stats = builder.get_stats()
    print(f"   • Построено описаний: {stats['descriptions_built']}")
    print(f"   • Средняя длина: {stats['average_length']} символов")
    print(f"   • Ошибок: {len(stats['errors'])}")
    print(f"\n📂 Тестовые файлы сохранены в output/")
    print(f"\n🚀 Генератор описаний готов к работе!")
    
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