# test_import.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import path_config, SUPPLIER_TO_WC_MAP
    print("✅ УСПЕХ: Модуль 'config' импортирован.")
    print(f"   Путь к данным: {path_config.INPUT_DIR}")
    print(f"   Правил маппинга: {len(SUPPLIER_TO_WC_MAP)}")
except ImportError as e:
    print(f"❌ ОШИБКА: {e}")
    print("\nПроверь:")
    print("1. Файл config/__init__.py существует?")
    print("2. Файл config/field_map.py существует?")