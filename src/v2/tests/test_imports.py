"""
Простой тест импортов для проверки структуры проекта.
"""
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=== Тест импортов ===")

try:
    print("1. Импорт моделей...")
    from v2.models import RawProduct, WooProduct
    print("✅ Модели импортированы")
    
    print("2. Импорт config_manager...")
    from v2.config_manager import ConfigManager
    print("✅ ConfigManager импортирован")
    
    print("3. Импорт обработчиков...")
    from v2.handlers import CoreHandler, SpecsHandler, MediaHandler, ContentHandler
    print("✅ Обработчики импортированы")
    
    print("4. Импорт aggregator...")
    from v2.aggregator import Aggregator
    print("✅ Aggregator импортирован")
    
    print("5. Импорт converter...")
    from v2.converter import ConverterV2
    print("✅ ConverterV2 импортирован")
    
    print("\n✅ Все импорты работают корректно!")
    
except ImportError as e:
    print(f"\n❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()