#!/usr/bin/env python3
"""
test_image_download_real.py
Тест реального скачивания изображений
"""

import sys
import os
import logging

# Детальное логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🖼️ Тест реального скачивания изображений")
print("=" * 50)

try:
    print("\n1. 📦 Загрузка модулей...")
    from data_processors.image_handler import ImageHandler
    print("   ✅ Модули загружены")
    
    # Создаем отдельную директорию для теста
    test_dir = "downloads/real_test"
    os.makedirs(test_dir, exist_ok=True)
    
    print(f"\n2. 🔧 Создание обработчика...")
    handler = ImageHandler(download_dir=test_dir)
    print(f"   ✅ Директория: {os.path.abspath(test_dir)}")
    
    print("\n3. 🧪 Тест реального скачивания...")
    
    # Тестовые данные с реальными URL (используем placeholder изображения)
    test_cases = [
        {
            'sku': 'TEST-DOWNLOAD-001',
            'name': 'Тестовый товар для скачивания',
            'images': 'https://via.placeholder.com/300/FF0000/FFFFFF?text=Test+Image+1,https://via.placeholder.com/300/00FF00/FFFFFF?text=Test+Image+2'
        }
    ]
    
    for test_case in test_cases:
        sku = test_case['sku']
        name = test_case['name']
        images = test_case['images']
        
        print(f"\n   📦 Товар: {name} ({sku})")
        print(f"   📷 URL: {images[:50]}...")
        
        # Скачиваем
        result = handler.process_product_images(sku, name, images, max_images=2)
        
        print(f"\n   📊 Результаты:")
        print(f"   • Успешно: {result['success']}")
        print(f"   • Скачано: {result['downloaded_count']}")
        print(f"   • Ошибок: {result['failed_count']}")
        print(f"   • Файлов: {len(result['filenames'])}")
        
        if result['filenames']:
            print(f"   📁 Созданные файлы:")
            for filename in result['filenames']:
                filepath = os.path.join(test_dir, filename)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    print(f"   • {filename} ({size} байт)")
                    
                    # Проверяем расширение
                    if filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        print(f"     ✅ Расширение корректно")
                    else:
                        print(f"     ⚠️  Проверьте расширение: {filename[-10:]}")
                else:
                    print(f"   • {filename} (файл не найден!)")
        
        if result['wc_paths']:
            print(f"\n   🛒 Пути для WooCommerce:")
            for path in result['wc_paths']:
                print(f"   • {path}")
        
        if result['errors']:
            print(f"\n   ⚠️  Ошибки:")
            for error in result['errors']:
                print(f"   • {error}")
    
    print("\n4. 📊 Статистика обработчика...")
    stats = handler.get_stats()
    print(f"   • Всего изображений: {stats['total_images']}")
    print(f"   • Скачано: {stats['downloaded']}")
    print(f"   • Ошибок: {stats['failed']}")
    print(f"   • Пропущено: {stats['skipped']}")
    
    if 'duration_seconds' in stats:
        print(f"   • Время: {stats['duration_seconds']:.1f} сек")
        print(f"   • Скорость: {stats.get('images_per_second', 0):.1f} изображений/сек")
    
    print("\n5. 🔍 Проверка файлов в директории...")
    if os.path.exists(test_dir):
        files = os.listdir(test_dir)
        print(f"   📂 Файлов в {test_dir}: {len(files)}")
        
        if files:
            print(f"   📋 Список файлов:")
            for file in sorted(files)[:5]:  # Показываем первые 5
                filepath = os.path.join(test_dir, file)
                size = os.path.getsize(filepath)
                print(f"   • {file} ({size} байт)")
            
            if len(files) > 5:
                print(f"   • ... и еще {len(files) - 5} файлов")
        else:
            print(f"   ⚠️  Директория пуста")
    else:
        print(f"   ❌ Директория не существует")
    
    print("\n6. 🎯 Проверка расширений файлов...")
    # Специальный тест для проверки расширений
    test_extensions = [
        ("https://example.com/image.jpg", ".jpg"),
        ("https://example.com/photo.png", ".png"),
        ("https://example.com/picture.webp", ".webp"),
        ("https://example.com/graphic.jpeg", ".jpg"),  # .jpeg → .jpg
        ("https://example.com/file", ".jpg"),  # без расширения → .jpg
    ]
    
    print("   Тест определения расширений:")
    for url, expected in test_extensions:
        ext = handler.get_extension_from_url(url)
        status = '✅' if ext == expected else '❌'
        print(f"   {status} {url[:30]}... -> {ext} (ожидалось: {expected})")
    
    print("\n" + "=" * 50)
    print("🎉 ТЕСТ РЕАЛЬНОГО СКАЧИВАНИЯ ЗАВЕРШЕН!")
    
    # Рекомендации
    print("\n📋 РЕКОМЕНДАЦИИ:")
    print("   1. Для продакшена увеличьте таймауты в __init__ (сейчас 30 сек)")
    print("   2. Добавьте обработку редиректов если нужно")
    print("   3. Рассмотрите использование aiohttp для асинхронной загрузки")
    print("   4. Настройте User-Agent под ваш проект")
    
    print(f"\n📁 Файлы сохранены в: {os.path.abspath(test_dir)}")
    
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