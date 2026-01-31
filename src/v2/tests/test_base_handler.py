"""
Тестирование базового класса обработчика.
Внимание: Этот файл должен запускаться из корня проекта командой:
python -m src.v2.tests.test_base_handler
"""
import sys
from pathlib import Path
from unittest.mock import Mock

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Теперь импортируем
try:
    from src.v2.handlers.base_handler import BaseHandler, HandlerError, HandlerContext
    from src.v2.models import RawProduct
    from src.v2.config_manager import ConfigManager
    print("✅ Импорты загружены успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Запустите из корня проекта: python -m src.v2.tests.test_base_handler")
    sys.exit(1)


class TestHandler(BaseHandler):
    """Тестовый обработчик."""
    
    def process(self, raw_product: RawProduct) -> dict:
        return {"test": raw_product.НС_код}


def main():
    print("=== Тест BaseHandler ===")
    
    # Mock конфиг
    mock_config = Mock(spec=ConfigManager)
    mock_config.get_setting.return_value = True
    
    # Создаем обработчик
    handler = TestHandler(mock_config)
    
    # Создаем продукт
    product = RawProduct(НС_код="TEST123")
    
    # Обрабатываем
    result = handler.handle(product)
    
    print(f"✅ Результат: {result}")
    print(f"✅ Имя обработчика: {handler.handler_name}")
    
    print("\n✅ Тест пройден!")


if __name__ == "__main__":
    main()