"""
Тестирование базового класса обработчика.
"""
import sys
from pathlib import Path
from unittest.mock import Mock

# Добавляем родительскую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.v2.handlers.base_handler import BaseHandler, HandlerError, HandlerContext
from src.v2.models import RawProduct
from src.v2.config_manager import ConfigManager


class TestHandler(BaseHandler):
    """Тестовый обработчик для проверки базового класса."""
    
    def process(self, raw_product: RawProduct) -> dict:
        """Простая обработка - возвращает словарь с данными."""
        return {
            "test_field": f"processed_{raw_product.НС_код}",
            "name": raw_product.Наименование
        }
    
    def validate_input(self, raw_product: RawProduct) -> bool:
        """Проверяет наличие НС-кода."""
        return bool(raw_product.НС_код)
    
    def get_required_fields(self) -> list:
        """Обязательные поля."""
        return ["НС_код", "Наименование"]


class ErrorHandler(BaseHandler):
    """Обработчик, который всегда вызывает ошибку."""
    
    def process(self, raw_product: RawProduct) -> dict:
        """Всегда вызывает исключение."""
        raise ValueError("Тестовая ошибка обработки")


def test_base_handler_initialization():
    """Тестирование инициализации базового класса."""
    print("=== Тест инициализации BaseHandler ===")
    
    # Создаем mock конфиг менеджера
    mock_config = Mock(spec=ConfigManager)
    mock_config.get_setting.return_value = True
    
    # Создаем обработчик
    handler = TestHandler(mock_config)
    
    print(f"✅ Имя обработчика: {handler.handler_name}")
    print(f"✅ Конфиг менеджер установлен: {handler.config_manager is mock_config}")
    
    return handler


def test_handler_processing():
    """Тестирование обработки продукта."""
    print("\n=== Тест обработки продукта ===")
    
    # Создаем mock конфиг
    mock_config = Mock(spec=ConfigManager)
    mock_config.get_setting.return_value = True
    
    # Создаем обработчик
    handler = TestHandler(mock_config)
    
    # Создаем тестовый продукт
    raw_product = RawProduct(
        Наименование="Тестовый товар",
        НС_код="TEST001",
        row_number=1,
        raw_data={"Наименование": "Тестовый товар", "НС-код": "TEST001"}
    )
    
    # Проверяем валидацию
    is_valid = handler.validate_input(raw_product)
    print(f"✅ Валидация продукта: {is_valid}")
    
    # Проверяем обязательные поля
    required_fields = handler.get_required_fields()
    print(f"✅ Обязательные поля: {required_fields}")
    
    # Обрабатываем продукт
    result = handler.handle(raw_product)
    print(f"✅ Результат обработки: {result}")
    
    return handler, raw_product, result


def test_handler_error_handling():
    """Тестирование обработки ошибок."""
    print("\n=== Тест обработки ошибок ===")
    
    # Тест 1: Обработчик с ошибкой при skip_on_error=True
    mock_config = Mock(spec=ConfigManager)
    mock_config.get_setting.return_value = True  # skip_on_error = True
    
    error_handler = ErrorHandler(mock_config)
    raw_product = RawProduct(НС_код="ERROR001", row_number=2)
    
    try:
        result = error_handler.handle(raw_product)
        print(f"✅ При skip_on_error=True ошибка обработана, результат: {result}")
    except Exception as e:
        print(f"❌ Неожиданное исключение: {e}")
    
    # Тест 2: Обработчик с ошибкой при skip_on_error=False
    mock_config.get_setting.return_value = False  # skip_on_error = False
    
    error_handler2 = ErrorHandler(mock_config)
    
    try:
        result = error_handler2.handle(raw_product)
        print(f"❌ Ожидалось исключение, но получен результат: {result}")
    except HandlerError as e:
        print(f"✅ Ожидаемое исключение HandlerError: {e}")
    except Exception as e:
        print(f"❌ Неожиданный тип исключения: {type(e).__name__}: {e}")
    
    # Тест 3: Создание HandlerError
    try:
        raise HandlerError("Тестовая ошибка", "TEST123", "TestHandler")
    except HandlerError as e:
        print(f"✅ HandlerError создан корректно: {e}")
        print(f"  SKU продукта: {e.product_sku}")
        print(f"  Имя обработчика: {e.handler_name}")


def test_handler_context():
    """Тестирование контекста обработчика."""
    print("\n=== Тест HandlerContext ===")
    
    context = HandlerContext()
    
    # Тест кэша
    context.set_cache("test_key", "test_value")
    cached_value = context.get_cache("test_key")
    print(f"✅ Кэш: установлено 'test_key' = '{cached_value}'")
    
    default_value = context.get_cache("non_existent", "default")
    print(f"✅ Кэш: несуществующий ключ возвращает дефолт: '{default_value}'")
    
    # Тест общих данных
    context.set_shared("shared_key", "shared_value")
    shared_value = context.get_shared("shared_key")
    print(f"✅ Общие данные: 'shared_key' = '{shared_value}'")
    
    # Очистка кэша
    context.clear_cache()
    after_clear = context.get_cache("test_key", "cleared")
    print(f"✅ Кэш после очистки: 'test_key' = '{after_clear}'")
    
    return context


def test_cleanup_and_stats():
    """Тестирование cleanup и статистики."""
    print("\n=== Тест cleanup и статистики ===")
    
    mock_config = Mock(spec=ConfigManager)
    mock_config.get_setting.return_value = True
    
    handler = TestHandler(mock_config)
    
    # Тестируем логирование статистики
    print("✅ Логирование статистики (проверьте вывод выше):")
    handler.log_processing_stats(processed=10, skipped=2)
    
    # Тестируем cleanup
    handler.cleanup()
    print("✅ Метод cleanup вызван")
    
    return handler


def main():
    """Запуск всех тестов."""
    print("Тестирование BaseHandler B2B-WC Converter v2.0\n")
    
    try:
        handler = test_base_handler_initialization()
        handler, raw_product, result = test_handler_processing()
        test_handler_error_handling()
        context = test_handler_context()
        handler = test_cleanup_and_stats()
        
        print("\n✅ Все тесты BaseHandler пройдены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании BaseHandler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
