"""
Простой тестовый скрипт для проверки базового функционала.
"""
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Теперь можем импортировать
from v2.handlers.base_handler import BaseHandler, HandlerError
from v2.models import RawProduct
from unittest.mock import Mock
from v2.config_manager import ConfigManager


class SimpleTestHandler(BaseHandler):
    def process(self, raw_product):
        return {"result": "success", "sku": raw_product.НС_код}


def main():
    print("=== Простой тест BaseHandler ===")
    
    # Mock конфиг
    mock_config = Mock(spec=ConfigManager)
    mock_config.get_setting.return_value = True
    
    # Создаем обработчик
    handler = SimpleTestHandler(mock_config)
    
    # Создаем продукт
    product = RawProduct(НС_код="TEST123", Наименование="Тест")
    
    # Обрабатываем
    result = handler.handle(product)
    
    print(f"✅ Результат: {result}")
    print(f"✅ Имя обработчика: {handler.handler_name}")
    
    # Тест HandlerError
    try:
        raise HandlerError("Тест ошибки", "TEST456", "SimpleTestHandler")
    except HandlerError as e:
        print(f"✅ HandlerError работает: {e}")
    
    print("\n✅ Все простые тесты пройдены!")


if __name__ == "__main__":
    main()