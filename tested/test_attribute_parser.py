#!/usr/bin/env python3
"""
test_attribute_parser.py
Тестирование парсера характеристик
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

print("🧪 Тестирование парсера характеристик")
print("=" * 60)

try:
    print("\n1. 📦 Импорт модулей...")
    from data_processors.attribute_parser import (
        AttributeParser, 
        parse_characteristics,
        get_wc_attributes_from_characteristics,
        format_characteristics_for_description
    )
    print("   ✅ Модули загружены успешно!")
    
    print("\n2. 🔧 Создание парсера...")
    parser = AttributeParser()
    print("   ✅ Парсер создан")
    
    # Тестовые данные (реальные примеры из XLSX)
    test_characteristics = [
        # Пример 1: Простые характеристики
        "Цвет корпуса: Белый; Материал корпуса: Металл; Мощность: 2 кВт; Страна производства: РОССИЯ",
        
        # Пример 2: Сложные характеристики (из реального файла)
        """Аварийное отключение при сильном наклоне или опрокидывании: Да; 
        Блок управления: Встроенный; Вид управления: Механическое; 
        Вид установки (крепления): Напольная / Настенная; 
        Высота товара: 22 см; Высота упаковки товара: 24 см; 
        Гарантийный срок: 3 года; Глубина товара: 12 см; 
        Глубина упаковки товара: 13 см; Длина кабеля: 1.2 м; 
        Защита от перегрева: Да; Индикация работы функции "открытое окно": false; 
        Класс пылевлагозащищенности: IP54; Комплект напольной установки: Да; 
        Комплект настенного крепления: Да; Макс. потребляемая мощность: 2 кВт; 
        Масса товара (нетто): 5.9 кг; Масса товара с упаковкой (брутто): 6.4 кг; 
        Материал корпуса: Металл; Напряжение электропитания, В: 220 - 240 В; 
        Область применения: Промышленное; Серия: IP 54; 
        Сетевой кабель: Да (с вилкой); Срок службы: 7 лет; 
        Страна производства: РОССИЯ; Таймер на отключение: Нет; 
        Тип нагревательного элемента: Х-образный монолитный нагревательный элемент; 
        Тип термостата: Электронный; Управление c мобильного приложения по Wi-Fi: Нет; 
        Функция "открытое окно": false; Цвет корпуса: Белый; Цифровой дисплей: Да; 
        Ширина товара: 94 см; Ширина упаковки товара: 97 см; 
        Эффективен для помещ. площадью до: 25 м2""",
        
        # Пример 3: Пустые характеристики
        "",
        
        # Пример 4: С некорректным форматированием
        "Цвет:Красный;Материал:Пластик",
    ]
    
    print("\n3. 🔍 Тестирование парсинга строк...")
    for i, test_str in enumerate(test_characteristics[:2]):
        print(f"\n   📝 Пример {i+1}:")
        print(f"   Длина строки: {len(test_str)} символов")
        
        # Парсинг
        parsed = parser.parse_characteristics_string(test_str)
        print(f"   Парсинг: найдено {len(parsed)} характеристик")
        
        if parsed:
            print(f"   Первые 3 характеристики:")
            for key, value in parsed[:3]:
                print(f"     • {key}: {value}")
    
    print("\n4. 🗂️ Тестирование группировки...")
    test_str = test_characteristics[1]  # Берем сложный пример
    grouped = parser.parse_and_group(test_str)
    
    print(f"   Группировка: {len(grouped)} групп")
    print(f"   Статистика: {parser.get_stats()}")
    
    print(f"\n   📊 Группы характеристик:")
    for group_name, chars in sorted(grouped.items()):
        print(f"     • {group_name}: {len(chars)} характеристик")
        # Показываем первые 2 характеристики в группе
        for char in chars[:2]:
            print(f"       - {char.key}: {char.value}")
    
    print("\n5. 🛒 Тестирование извлечения атрибутов WC...")
    wc_attrs = parser.extract_wc_attributes(test_str)
    
    print(f"   Найдено атрибутов WC: {len(wc_attrs['attributes'])}")
    if wc_attrs['attributes']:
        print(f"   Атрибуты WooCommerce:")
        for slug, value in wc_attrs['attributes'].items():
            print(f"     • {slug}: {value}")
    
    print("\n6. 📋 Тестирование извлечения конкретных полей...")
    extracted = parser.extract_specific_fields(test_str)
    
    print(f"   Извлеченные поля: {len(extracted)}")
    if extracted:
        for field, value in extracted.items():
            print(f"     • {field}: {value}")
    
    print("\n7. 📝 Тестирование форматирования для описания...")
    html_output = parser.format_for_description(test_str)
    
    print(f"   HTML описание: {len(html_output)} символов")
    if html_output:
        # Показываем превью
        preview = html_output[:200] + "..." if len(html_output) > 200 else html_output
        print(f"   Превью:\n{preview}")
        
        # Сохраняем в файл для просмотра
        with open('output/characteristics_sample.html', 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"   💾 Полный HTML сохранен в: output/characteristics_sample.html")
    
    print("\n8. ⚡ Тестирование быстрых функций...")
    
    # Быстрый парсинг
    quick_parsed = parse_characteristics(test_characteristics[0])
    print(f"   Быстрый парсинг: {sum(len(chars) for chars in quick_parsed.values())} характеристик")
    
    # Быстрое получение атрибутов WC
    quick_wc = get_wc_attributes_from_characteristics(test_characteristics[0])
    print(f"   Быстрые атрибуты WC: {len(quick_wc['attributes'])}")
    
    # Быстрое форматирование
    quick_html = format_characteristics_for_description(test_characteristics[0])
    print(f"   Быстрое HTML: {len(quick_html)} символов")
    
    print("\n9. 🔬 Тестирование на реальных данных из XLSX...")
    try:
        from data_processors.xlsx_parser import parse_xlsx_file
        from config import settings
        
        input_file = settings.INPUT_FILE
        if os.path.exists(input_file):
            print(f"   📁 Чтение реального файла: {input_file}")
            
            # Парсим только первые 3 товара для теста
            data, stats = parse_xlsx_file(input_file)
            
            if data and len(data) > 0:
                print(f"   📊 Обработано товаров: {len(data)}")
                
                # Берем первый товар с характеристиками
                test_product = None
                for product in data:
                    if product.get('characteristics_raw'):
                        test_product = product
                        break
                
                if test_product:
                    print(f"   🔍 Тестируем товар: {test_product.get('name', '')[:50]}...")
                    print(f"   📏 Характеристик: {len(test_product.get('characteristics_raw', ''))} символов")
                    
                    # Парсим характеристики
                    real_characteristics = test_product.get('characteristics_raw', '')
                    real_grouped = parser.parse_and_group(real_characteristics)
                    
                    print(f"   🗂️  Группировка реальных данных:")
                    print(f"     • Всего групп: {len(real_grouped)}")
                    print(f"     • Всего характеристик: {parser.get_stats()['grouped_characteristics']}")
                    
                    # Атрибуты WC
                    real_wc = parser.extract_wc_attributes(real_characteristics)
                    print(f"     • Атрибутов WC: {len(real_wc['attributes'])}")
                    
                    if real_wc['attributes']:
                        print(f"     📋 Список атрибутов:")
                        for slug, value in real_wc['attributes'].items():
                            print(f"       - {slug}: {value}")
                    
                    # Сохраняем HTML
                    real_html = parser.format_for_description(real_characteristics)
                    with open('output/real_characteristics_sample.html', 'w', encoding='utf-8') as f:
                        f.write(real_html)
                    print(f"     💾 HTML сохранен в: output/real_characteristics_sample.html")
                    
                else:
                    print("   ⚠️  Не найдено товаров с характеристиками")
            else:
                print("   ⚠️  Нет данных для тестирования")
        else:
            print(f"   ⚠️  Файл не найден: {input_file}")
            
    except Exception as e:
        print(f"   ⚠️  Ошибка теста реальных данных: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТИРОВАНИЕ ПАРСЕРА ХАРАКТЕРИСТИК ЗАВЕРШЕНО УСПЕШНО!")
    
    print("\n📋 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   • Поддерживаемых групп: {len(parser.characteristic_groups)}")
    print(f"   • Атрибутов WC: {len(parser.wc_attributes)}")
    print(f"   • Тестовых файлов сохранено в output/")
    print(f"\n🚀 Парсер характеристик готов к работе!")
    
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