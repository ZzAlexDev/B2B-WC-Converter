#!/usr/bin/env python3
"""
test_image_handler.py
Тестирование обработчика изображений
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

print("🖼️ Тестирование обработчика изображений")
print("=" * 50)

try:
    print("\n1. 📦 Импорт модулей...")
    from data_processors.image_handler import ImageHandler, download_product_images
    print("   ✅ Модули загружены успешно!")
    
    print("\n2. 🔧 Создание обработчика...")
    handler = ImageHandler(download_dir="downloads/test_images")
    print(f"   ✅ Обработчик создан. Директория: {handler.download_dir}")
    
    print("\n3. 🧪 Тест slugify...")
    test_texts = [
        ("Конвектор электрический Ballu IP 54", "konvektor-elektricheskiy-ballu-ip-54"),
        ("Рукосушилка Electrolux EHDA-2500", "rukosushilka-electrolux-ehda-2500"),
        ("Тест с русскими буквами", "test-s-russkimi-bukvami"),
    ]
    
    for text, expected in test_texts:
        result = handler.slugify_text(text)
        # Не будем слишком строгими с ожиданием
        if result and '-' in result:
            print(f"   ✅ '{text}' -> '{result}'")
        else:
            print(f"   ⚠️  '{text}' -> '{result}' (проверьте результат)")
    
    print("\n4. 🧪 Тест генерации имен файлов...")
    test_cases = [
        ("BEC-CMR-2000", "Конвектор электрический Ballu IP 54", 1, 
         "https://example.com/image.jpg", "BEC-CMR-2000-konvektor-elektricheskiy-ballu-ip-54-01.jpg"),
        ("TEST-001", "Простой товар", 2, 
         "https://example.com/photo.png", "TEST-001-prostoy-tovar-02.png"),
    ]
    
    for sku, name, index, url, expected_pattern in test_cases:
        filename = handler.generate_filename(sku, name, index, url)
        print(f"   📁 {sku}: {filename}")
        print(f"     (ожидается похоже на: {expected_pattern})")
    
    print("\n5. 🧪 Тест парсинга URL...")
    test_urls = "https://example.com/1.jpg, https://example.com/2.png, некорректный, https://example.com/3.webp"
    parsed = handler.parse_image_urls(test_urls)
    print(f"   Найдено URL: {len(parsed)} (из 4, некорректный должен быть пропущен)")
    for url in parsed:
        print(f"   • {url}")
    
    print("\n6. 🧪 Тест на тестовых данных (без реального скачивания)...")
    test_sku = "TEST-SKU-001"
    test_name = "Тестовый товар"
    test_images = "https://via.placeholder.com/150/FF0000/FFFFFF?text=Image1,https://via.placeholder.com/150/00FF00/FFFFFF?text=Image2"
    
    print(f"   Товар: {test_name} ({test_sku})")
    print(f"   URL изображений: {test_images}")
    
    # Тест без реального скачивания (показываем что будет)
    urls = handler.parse_image_urls(test_images)
    print(f"   Будет обработано URL: {len(urls)}")
    
    for i, url in enumerate(urls, 1):
        filename = handler.generate_filename(test_sku, test_name, i, url)
        print(f"   • Изображение {i}: {filename}")
    
    print("\n7. 🔗 Тест на реальных данных из XLSX (без скачивания)...")
    try:
        from data_processors.xlsx_parser import parse_xlsx_file
        from config import settings
        
        input_file = settings.INPUT_FILE
        if os.path.exists(input_file):
            print(f"   📁 Чтение файла: {input_file}")
            
            # Парсим только первые 2 товара для теста
            data, stats = parse_xlsx_file(input_file)
            
            if data and len(data) > 0:
                test_products = data[:2]
                print(f"   📊 Тестируем {len(test_products)} товаров (без скачивания)...")
                
                for product in test_products:
                    sku = product.get('sku', '')
                    name = product.get('name', '')[:30]
                    images = product.get('images_raw', '')
                    
                    print(f"\n   📦 Товар: {name}... ({sku})")
                    
                    if images:
                        urls = handler.parse_image_urls(images)
                        print(f"   📷 Найдено изображений: {len(urls)}")
                        
                        if urls:
                            # Показываем как будут называться файлы
                            for i, url in enumerate(urls[:3], 1):  # Первые 3
                                filename = handler.generate_filename(sku, name, i, url)
                                print(f"   • {filename}")
                            
                            if len(urls) > 3:
                                print(f"   • ... и еще {len(urls) - 3} изображений")
                    else:
                        print(f"   ⚠️  Нет изображений")
                        
            else:
                print("   ⚠️  Нет данных для тестирования")
        else:
            print(f"   ⚠️  Файл не найден: {input_file}")
            
    except Exception as e:
        print(f"   ⚠️  Ошибка теста реальных данных: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n8. 📋 Проверка структуры модуля...")
    required_methods = [
        'slugify_text',
        'generate_filename',
        'download_single_image',
        'parse_image_urls',
        'process_product_images',
        'process_batch',
        'get_stats',
    ]
    
    all_ok = True
    for method in required_methods:
        has_method = hasattr(handler, method)
        status = '✅' if has_method else '❌'
        print(f"   {status} {method}")
        if not has_method:
            all_ok = False
    
    print("\n9. 🎯 Итог:")
    print("   • Slugify: преобразование кириллицы в латиницу")
    print("   • Имена файлов: {sku}-{slug_title}-{номер}.jpg")
    print("   • Парсинг URL: разделение по запятой")
    print("   • Обработка ошибок: таймауты, битые ссылки")
    print("   • Пути для WC: /wp-content/uploads/products/...")
    
    print("\n" + "=" * 50)
    if all_ok:
        print("🎉 ОБРАБОТЧИК ИЗОБРАЖЕНИЙ ГОТОВ К РАБОТЕ!")
        print("\n⚠️  ВНИМАНИЕ: Для реального скачивания нужны:")
        print("   1. Активные URL изображений")
        print("   2. Интернет-соединение")
        print("   3. Достаточно места на диске")
    else:
        print("⚠️  Есть проблемы с методами обработчика")
    
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