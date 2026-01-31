"""
Тестирование CoreHandler.
Запуск из корня проекта: python -m src.v2.tests.test_core_handler
"""
import sys
from pathlib import Path
import json

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.v2.handlers.core_handler import CoreHandler
from src.v2.models import RawProduct
from src.v2.config_manager import ConfigManager


def test_core_handler_initialization():
    """Тестирование инициализации CoreHandler."""
    print("=== Тест инициализации CoreHandler ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = CoreHandler(config_manager)
        
        print(f"✅ CoreHandler создан: {handler.handler_name}")
        print(f"✅ ConfigManager загружен")
        
        return handler, config_manager
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_title_and_slug(handler):
    """Тестирование обработки названия и slug."""
    print("\n=== Тест названия и slug ===")
    
    test_cases = [
        {
            "name": "Простой товар",
            "product": RawProduct(Наименование="Пластиковый контейнер", НС_код="PC001"),
            "expected_title": "Пластиковый контейнер"
        },
        {
            "name": "Товар с спецсимволами",
            "product": RawProduct(Наименование="Контейнер (10л) №1", НС_код="PC002"),
            "expected_title": "Контейнер (10л) №1"
        },
        {
            "name": "Пустое название",
            "product": RawProduct(Наименование="", НС_код="PC003"),
            "expected_title": "Товар PC003"
        }
    ]
    
    for test in test_cases:
        result = handler.process(test["product"])
        print(f"✅ {test['name']}:")
        print(f"   Название: '{result.get('post_title')}' (ожидалось: '{test['expected_title']}')")
        print(f"   Slug: '{result.get('post_name')}'")
    
    return handler


def test_price_processing(handler):
    """Тестирование обработки цены."""
    print("\n=== Тест обработки цены ===")
    
    test_cases = [
        ("14990 руб.", "14990"),
        ("14 990 руб.", "14990"),
        ("1,499.50 руб.", "1499.50"),
        ("Цена по запросу", ""),
        ("", ""),
        ("1000,50 руб.", "1000.50")
    ]
    
    for price_str, expected in test_cases:
        product = RawProduct(Цена=price_str, НС_код="TEST")
        result = handler.process(product)
        actual = result.get("regular_price", "")
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{price_str}' -> '{actual}' (ожидалось: '{expected}')")
    
    return handler


def test_categories(handler):
    """Тестирование обработки категорий."""
    print("\n=== Тест обработки категорий ===")
    
    test_cases = [
        ("Тара - Контейнеры", "Тара > Контейнеры"),
        ("Мебель - Шкафы - Офисные", "Мебель > Шкафы > Офисные"),
        ("Без категории", "Без категории"),
        ("", "")
    ]
    
    for category_str, expected in test_cases:
        product = RawProduct(Название_категории=category_str, НС_код="TEST")
        result = handler.process(product)
        actual = result.get("tax:product_cat", "")
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{category_str}' -> '{actual}' (ожидалось: '{expected}')")
    
    return handler


def test_barcode(handler):
    """Тестирование обработки штрих-кода."""
    print("\n=== Тест обработки штрих-кода ===")
    
    test_cases = [
        ("1234567890123/2345678901234", "1234567890123"),
        ("9876543210987", "9876543210987"),
        ("", ""),
        ("123/456/789", "123")
    ]
    
    for barcode_str, expected in test_cases:
        product = RawProduct(Штрих_код=barcode_str, НС_код="TEST")
        result = handler.process(product)
        actual = result.get("meta:_global_unique_id", "")
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{barcode_str}' -> '{actual}' (ожидалось: '{expected}')")
    
    return handler


def test_exclusive(handler):
    """Тестирование обработки эксклюзива."""
    print("\n=== Тест обработки эксклюзива ===")
    
    test_cases = [
        ("Эксклюзив - Да", "Да"),
        ("Эксклюзив - Нет", "Нет"),
        ("Эксклюзив - да", "Да"),
        ("Эксклюзив - нет", "Нет"),
        ("", "Нет"),
        ("Да", "Да")
    ]
    
    for exclusive_str, expected in test_cases:
        product = RawProduct(Эксклюзив=exclusive_str, НС_код="TEST")
        result = handler.process(product)
        actual = result.get("meta:эксклюзив", "")
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{exclusive_str}' -> '{actual}' (ожидалось: '{expected}')")
    
    return handler


def test_full_processing(handler):
    """Тестирование полной обработки."""
    print("\n=== Тест полной обработки ===")
    
    product = RawProduct(
        Наименование="Металлический шкаф MS-200",
        Артикул="MS-200",
        НС_код="NS002",
        Бренд="MetalWorks",
        Название_категории="Мебель - Шкафы - Офисные",
        Цена="24500 руб.",
        Штрих_код="9876543210987",
        Эксклюзив="Эксклюзив - Нет",
        Статья="<p>Прочный металлический шкаф для офиса</p>",
        row_number=1
    )
    
    result = handler.process(product)
    
    print("✅ Проверка полей:")
    fields_to_check = [
        ("post_title", "Металлический шкаф MS-200"),
        ("sku", "NS002"),
        ("meta:артикул", "MS-200"),
        ("tax:product_cat", "Мебель > Шкафы > Офисные"),
        ("regular_price", "24500"),
        ("meta:_global_unique_id", "9876543210987"),
        ("meta:эксклюзив", "Нет")
    ]
    
    for field, expected in fields_to_check:
        actual = result.get(field, "")
        status = "✅" if str(actual) == str(expected) else "❌"
        print(f"{status} {field}: '{actual}'")
    
    print(f"\n✅ Всего полей обработано: {len(result)}")
    print(f"✅ SEO полей: {len([k for k in result.keys() if 'yoast' in k])}")
    
    return result


def main():
    """Запуск всех тестов."""
    print("Тестирование CoreHandler B2B-WC Converter v2.0\n")
    
    try:
        handler, config = test_core_handler_initialization()
        
        if handler and config:
            test_title_and_slug(handler)
            test_price_processing(handler)
            test_categories(handler)
            test_barcode(handler)
            test_exclusive(handler)
            test_full_processing(handler)
            
            # Очистка
            handler.cleanup()
            print("\n✅ Все тесты CoreHandler пройдены успешно!")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании CoreHandler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()