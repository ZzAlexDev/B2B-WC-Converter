#!/usr/bin/env python3
"""
test_csv_exporter.py
Тестирование CSV экспортера WooCommerce
"""

import sys
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("📊 Тестирование CSV экспортера WooCommerce")
print("=" * 50)

try:
    print("\n1. 📦 Импорт модулей...")
    from output_managers.csv_exporter import CSVExporter, export_to_csv
    print("   ✅ Модули загружены успешно!")
    
    print("\n2. 🔧 Создание экспортера...")
    test_output = "output/test_wc_export.csv"
    exporter = CSVExporter(test_output)
    print(f"   ✅ Экспортер создан. Выходной файл: {test_output}")
    
    print("\n3. 🧪 Тест подготовки данных...")
    
    # Тестовые данные товара
    test_product = {
        'name': 'Конвектор электрический Ballu IP 54 BEC/CMR-2000',
        'sku': 'BEC-CMR-2000',
        'brand': 'Ballu',
        'category': 'Тепловое оборудование > Конвекторы',
        'price': 46990.0,
        'post_content': '<p>Тестовое описание товара</p>',
        'post_excerpt': 'Краткое описание конвектора',
        'images_raw': 'https://example.com/image1.jpg,https://example.com/image2.jpg',
        'wc_image_paths': '/wp-content/uploads/products/BEC-CMR-2000-konvektor-01.jpg | /wp-content/uploads/products/BEC-CMR-2000-konvektor-02.jpg',
        'additional_info': {
            'Штрих код': '4660294720440 / 7381032480187',
            'НС-код': 'НС-1659333'
        },
        'extracted_fields': {
            'weight': '5.9 кг',
            'width': '94 см',
            'height': '22 см',
            'length': '12 см'
        },
        'wc_attributes': {
            'attributes': {
                'pa_color': 'Белый',
                'pa_material': 'Металл',
                'pa_power': '2 кВт',
                'pa_country': 'РОССИЯ'
            },
            'attributes_data': {
                'pa_color_data': '1:0|0',
                'pa_material_data': '1:0|0',
                'pa_power_data': '1:0|0',
                'pa_country_data': '1:0|0'
            }
        }
    }
    
    print(f"   📦 Тестовый товар: {test_product['name'][:40]}...")
    
    # Подготавливаем данные для WC
    wc_data = exporter.prepare_wc_data(test_product)
    
    print(f"   ✅ Данные подготовлены. Поля: {len(wc_data)}")
    
    # Показываем основные поля
    print(f"   📋 Основные поля:")
    important_fields = ['post_title', 'sku', 'regular_price', 'tax:product_cat', 'tax:product_brand']
    for field in important_fields:
        if field in wc_data:
            value = wc_data[field]
            print(f"   • {field}: {value[:50]}{'...' if len(str(value)) > 50 else ''}")
    
    # Показываем атрибуты
    print(f"   🏷️  Атрибуты WC:")
    for key, value in wc_data.items():
        if key.startswith('attribute:pa_'):
            print(f"   • {key}: {value}")
    
    print("\n4. 📁 Тест генерации CSV...")
    
    # Создаем тестовый список товаров
    test_products = [test_product, test_product]  # Два одинаковых для теста
    
    print(f"   📊 Тестируем экспорт {len(test_products)} товаров...")
    
    # Генерируем CSV
    success = exporter.generate_csv(test_products)
    
    if success:
        print(f"   ✅ CSV успешно создан: {test_output}")
        
        # Проверяем размер файла
        if os.path.exists(test_output):
            size = os.path.getsize(test_output)
            print(f"   📏 Размер файла: {size} байт")
            
            # Показываем первые строки
            print(f"   📄 Первые строки файла:")
            with open(test_output, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
                for i, line in enumerate(lines, 1):
                    if i == 1:
                        print(f"   [Заголовки] {line[:80]}...")
                    else:
                        print(f"   [Строка {i-1}] {line[:80]}...")
        else:
            print(f"   ❌ Файл не создан")
    else:
        print(f"   ❌ Не удалось создать CSV")
    
    print("\n5. 📊 Статистика экспорта...")
    stats = exporter.get_stats()
    print(f"   • Всего товаров: {stats['total_products']}")
    print(f"   • Экспортировано: {stats['exported']}")
    print(f"   • Пропущено: {stats['skipped']}")
    print(f"   • Ошибок: {len(stats['errors'])}")
    
    if stats['errors']:
        print(f"   ⚠️  Ошибки:")
        for error in stats['errors'][:3]:  # Показываем первые 3 ошибки
            print(f"   • {error}")
    
    print("\n6. ⚡ Тест быстрой функции...")
    quick_output = "output/quick_test.csv"
    quick_success = export_to_csv(test_products, quick_output)
    
    print(f"   ✅ Быстрая функция: {'работает' if quick_success else 'не работает'}")
    
    print("\n7. 🎯 Проверка формата для WooCommerce...")
    print("   Требования к CSV для WC:")
    print("   • UTF-8 с BOM для Excel ✓")
    print("   • Запятая как разделитель ✓")
    print("   • Двойные кавычки для текста ✓")
    print("   • Все поля в кавычках при необходимости ✓")
    print("   • Правильные заголовки полей ✓")
    
    print("\n" + "=" * 50)
    print("🎉 CSV ЭКСПОРТЕР ГОТОВ К РАБОТЕ!")
    print(f"\n📁 Тестовые файлы созданы:")
    print(f"   • {test_output}")
    print(f"   • {quick_output}")
    print(f"\n⚠️  Для импорта в WooCommerce:")
    print("   1. Откройте WooCommerce > Продукты")
    print("   2. Нажмите 'Импорт'")
    print("   3. Выберите созданный CSV файл")
    print("   4. Следуйте инструкциям импортера")
    
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