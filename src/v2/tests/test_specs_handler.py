"""
Тестирование SpecsHandler.
Запуск из корня проекта: python -m src.v2.tests.test_specs_handler
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.v2.handlers.specs_handler import SpecsHandler
from src.v2.models import RawProduct
from src.v2.config_manager import ConfigManager


def test_specs_handler_initialization():
    """Тестирование инициализации SpecsHandler."""
    print("=== Тест инициализации SpecsHandler ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = SpecsHandler(config_manager)
        
        print(f"✅ SpecsHandler создан: {handler.handler_name}")
        
        return handler, config_manager
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_parse_specifications(handler):
    """Тестирование парсинга характеристик."""
    print("\n=== Тест парсинга характеристик ===")
    
    test_cases = [
        (
            "Масса товара (нетто): 0.5 кг / Высота товара: 30 см / Ширина товара: 20 см",
            3,
            ["Масса товара (нетто)", "Высота товара", "Ширина товара"]
        ),
        (
            "Цвет корпуса: Белый; Страна производства: Россия",
            2,
            ["Цвет корпуса", "Страна производства"]
        ),
        (
            "Область применения: Хранение, Гарантийный срок: 2 года",
            2,
            ["Область применения", "Гарантийный срок"]
        ),
        (
            "",
            0,
            []
        ),
        (
            "Нет характеристик",
            0,
            []
        )
    ]
    
    for specs_str, expected_count, expected_keys in test_cases:
        product = RawProduct(НС_код="TEST", Характеристики=specs_str)
        result = handler.process(product)
        
        if expected_count > 0:
            if "meta:все_характеристики" in result:
                all_specs = result["meta:все_характеристики"]
                found_keys = []
                for key in expected_keys:
                    if key.lower() in all_specs.lower():
                        found_keys.append(key)
                
                status = "✅" if len(found_keys) == expected_count else "❌"
                print(f"{status} '{specs_str[:30]}...' -> найдено {len(found_keys)} из {expected_count} характеристик")
            else:
                print(f"❌ '{specs_str[:30]}...' -> поле 'meta:все_характеристики' отсутствует")
        else:
            if "meta:все_характеристики" not in result:
                print(f"✅ '{specs_str[:30]}...' -> характеристики отсутствуют (как и ожидалось)")
            else:
                print(f"⚠️ '{specs_str[:30]}...' -> характеристики найдены, но не ожидались")
    
    return handler


def test_standard_fields_processing(handler):
    """Тестирование обработки стандартных полей."""
    print("\n=== Тест обработки стандартных полей ===")
    
    product = RawProduct(
        НС_код="TEST001",
        Характеристики="Масса товара (нетто): 0.5 кг / Высота товара: 30 см / "
                      "Ширина товара: 20 см / Глубина товара: 15 см / "
                      "Вес брутто: 0.7 кг"
    )
    
    result = handler.process(product)
    
    expected_fields = {
        "weight": "0.5",
        "height": "30",
        "width": "20", 
        "length": "15"
    }
    
    print("✅ Обработанные стандартные поля:")
    for field, expected_value in expected_fields.items():
        actual_value = result.get(field, "")
        status = "✅" if str(actual_value) == str(expected_value) else "❌"
        print(f"{status} {field}: '{actual_value}' (ожидалось: '{expected_value}')")
    
    return handler


def test_woocommerce_attributes(handler):
    """Тестирование обработки атрибутов WooCommerce."""
    print("\n=== Тест обработки атрибутов WooCommerce ===")
    
    product = RawProduct(
        НС_код="TEST002",
        Характеристики="Область применения: Хранение / Цвет корпуса: Белый / "
                      "Страна производства: Россия / Гарантийный срок: 2 года"
    )
    
    result = handler.process(product)
    
    expected_attributes = {
        "attribute:pa_oblast-primeneniya": "Хранение",
        "attribute:pa_tsvet-korpusa": "Белый",
        "attribute:pa_strana-proizvodstva": "Россия",
        "attribute:pa_garantiynyy-srok": "2 года"
    }
    
    print("✅ Обработанные атрибуты WooCommerce:")
    for attr, expected_value in expected_attributes.items():
        actual_value = result.get(attr, "")
        status = "✅" if str(actual_value) == str(expected_value) else "❌"
        print(f"{status} {attr}: '{actual_value}' (ожидалось: '{expected_value}')")
    
    return handler


def test_numeric_extraction(config_manager):
    """Тестирование извлечения числовых значений через ConfigManager."""
    print("\n=== Тест извлечения числовых значений ===")
    
    test_cases = [
        ("10 кг", ("10", "kg")),
        ("5.5 см", ("5.5", "cm")),
        ("1000 мм", ("1000", "mm")),
        ("2,5 л", ("2,5", "l")),
        ("15.7", ("15.7", "")),
        ("Без числа", ("Без числа", "")),
        ("", ("", ""))
    ]
    
    for value_str, expected in test_cases:
        result = config_manager.extract_unit(value_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{value_str}' -> ('{result[0]}', '{result[1]}') "
              f"(ожидалось: ('{expected[0]}', '{expected[1]}'))")


def test_full_processing(handler):
    """Тестирование полной обработки."""
    print("\n=== Тест полной обработки ===")
    
    product = RawProduct(
        НС_код="NS001",
        Характеристики="Масса товара (нетто): 0.5 кг / Высота товара: 30 см / "
                      "Ширина товара: 20 см / Глубина товара: 15 см / "
                      "Область применения: Хранение / Цвет корпуса: Белый / "
                      "Страна производства: Россия / Гарантийный срок: 2 года"
    )
    
    result = handler.process(product)
    
    print("✅ Проверка полей:")
    
    standard_fields = {
        "weight": "0.5",
        "height": "30",
        "width": "20",
        "length": "15"
    }
    
    for field, expected in standard_fields.items():
        actual = result.get(field, "")
        status = "✅" if str(actual) == str(expected) else "❌"
        print(f"{status} {field}: '{actual}'")
    
    attributes = {
        "attribute:pa_oblast-primeneniya": "Хранение",
        "attribute:pa_tsvet-korpusa": "Белый",
        "attribute:pa_strana-proizvodstva": "Россия",
        "attribute:pa_garantiynyy-srok": "2 года"
    }
    
    for attr, expected in attributes.items():
        actual = result.get(attr, "")
        status = "✅" if str(actual) == str(expected) else "❌"
        print(f"{status} {attr}: '{actual}'")
    
    if "meta:все_характеристики" in result:
        print(f"✅ meta:все_характеристики: присутствует ({len(result['meta:все_характеристики'])} символов)")
    
    print(f"\n✅ Всего полей обработано: {len(result)}")
    
    return result


def main():
    """Запуск всех тестов."""
    print("Тестирование SpecsHandler B2B-WC Converter v2.0\n")
    
    try:
        handler, config = test_specs_handler_initialization()
        
        if handler and config:
            test_parse_specifications(handler)
            test_standard_fields_processing(handler)
            test_woocommerce_attributes(handler)
            test_numeric_extraction(config)
            test_full_processing(handler)
            
            handler.cleanup()
            print("\n✅ Все тесты SpecsHandler пройдены успешно!")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании SpecsHandler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()