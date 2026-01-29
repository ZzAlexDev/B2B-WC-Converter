#!/usr/bin/env python3
"""
test_real_images_from_xlsx.py
Тест скачивания реальных изображений из XLSX (только первые 2 товара)
"""

import sys
import os
import logging

# Умеренное логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🖼️ Тест реальных изображений из XLSX (первые 2 товара)")
print("=" * 50)

try:
    print("\n1. 📦 Загрузка модулей...")
    from data_processors.image_handler import ImageHandler
    from data_processors.xlsx_parser import parse_xlsx_file
    from config import settings
    print("   ✅ Модули загружены")
    
    # Создаем директорию
    real_test_dir = "downloads/real_xlsx_test"
    os.makedirs(real_test_dir, exist_ok=True)
    
    handler = ImageHandler(download_dir=real_test_dir)
    
    print(f"\n2. 📁 Чтение XLSX файла...")
    input_file = settings.INPUT_FILE
    
    if not os.path.exists(input_file):
        print(f"   ❌ Файл не найден: {input_file}")
        sys.exit(1)
    
    # Парсим только первые 2 товара
    data, stats = parse_xlsx_file(input_file)
    
    if not data or len(data) < 2:
        print(f"   ❌ Недостаточно данных в файле")
        sys.exit(1)
    
    print(f"   ✅ Прочитано товаров: {len(data)}")
    
    # Берем первые 2 товара
    test_products = data[:2]
    
    print(f"\n3. 🚀 Начинаем скачивание для {len(test_products)} товаров...")
    print("   ⚠️  Это займет время и потребует интернет-соединения")
    
    downloaded_count = 0
    
    for i, product in enumerate(test_products, 1):
        sku = product.get('sku', f'unknown_{i}')
        name = product.get('name', 'Без названия')[:40]
        images = product.get('images_raw', '')
        
        print(f"\n   [{i}/{len(test_products)}] 📦 {name}... ({sku})")
        
        if not images:
            print(f"   ⚠️  Нет изображений, пропускаем")
            continue
        
        # Скачиваем только первые 2 изображения для теста
        result = handler.process_product_images(sku, name, images, max_images=2)
        
        if result['success']:
            downloaded_count += result['downloaded_count']
            print(f"   ✅ Скачано: {result['downloaded_count']} изображений")
            
            if result['filenames']:
                print(f"   📁 Файлы:")
                for filename in result['filenames']:
                    filepath = os.path.join(real_test_dir, filename)
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        print(f"     • {filename} ({size // 1024} KB)")
        else:
            print(f"   ❌ Не удалось скачать изображения")
            
            if result['errors']:
                for error in result['errors'][:2]:  # Показываем первые 2 ошибки
                    print(f"     • {error}")
    
    print(f"\n4. 📊 Итоги скачивания...")
    stats = handler.get_stats()
    print(f"   • Всего обработано: {stats['total_images']}")
    print(f"   • Успешно скачано: {stats['downloaded']}")
    print(f"   • С ошибками: {stats['failed']}")
    print(f"   • Общий размер: {stats.get('total_size_mb', 0):.2f} MB")
    
    if 'duration_seconds' in stats:
        print(f"   • Затраченное время: {stats['duration_seconds']:.1f} сек")
    
    print(f"\n📁 Все файлы сохранены в: {os.path.abspath(real_test_dir)}")
    
    print("\n" + "=" * 50)
    if downloaded_count > 0:
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print(f"   Скачано {downloaded_count} изображений из реального XLSX")
    else:
        print("⚠️  Не удалось скачать изображения")
        print("   Возможные причины:")
        print("   1. Нет интернет-соединения")
        print("   2. URL изображений недоступны")
        print("   3. Проблемы с доступом к серверу")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()