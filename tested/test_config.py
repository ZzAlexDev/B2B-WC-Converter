#!/usr/bin/env python3
"""
test_config.py
Тестирование конфигурации проекта
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import settings
    from config import field_map
    
    print("✅ Конфигурация загружена успешно!")
    print(f"\n📁 Пути:")
    print(f"   Входной файл: {settings.INPUT_FILE}")
    print(f"   Выходной файл: {settings.OUTPUT_FILE}")
    print(f"   Директория изображений: {settings.IMAGES_DOWNLOAD_DIR}")
    
    print(f"\n⚙️ Настройки обработки:")
    print(f"   Макс. изображений: {settings.MAX_IMAGES_PER_PRODUCT}")
    print(f"   Очистка SKU: {settings.SKU_CLEAN_REPLACE}")
    print(f"   Групп характеристик: {len(settings.CHARACTERISTIC_GROUPS)}")
    
    print(f"\n🛒 Настройки WooCommerce:")
    print(f"   Статус по умолчанию: {settings.DEFAULT_STATUS}")
    print(f"   Тип товара: {settings.DEFAULT_TYPE}")
    print(f"   Атрибуты WC: {len(settings.WC_ATTRIBUTES)}")
    
    print(f"\n📊 Поля:")
    print(f"   Прямые маппинги: {len(field_map.DIRECT_MAPPINGS)}")
    print(f"   Выходные поля: {len(field_map.get_wc_output_fields_with_attributes())}")
    
    # Проверяем существование директорий
    print(f"\n📂 Проверка директорий:")
    for dir_path in [settings.IMAGES_DOWNLOAD_DIR, 
                     settings.DOCS_DOWNLOAD_DIR,
                     settings.LOG_DIR,
                     os.path.dirname(settings.OUTPUT_FILE)]:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} (не существует)")
    
    print("\n🎯 Конфигурация готова к работе!")
    
except Exception as e:
    print(f"❌ Ошибка загрузки конфигурации: {e}")
    sys.exit(1)