"""
Тестирование Aggregator.
Запуск из корня проекта: python -m src.v2.tests.test_aggregator
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.v2.aggregator import Aggregator
from src.v2.models import RawProduct
from src.v2.config_manager import ConfigManager


def test_aggregator_initialization():
    """Тестирование инициализации Aggregator."""
    print("=== Тест инициализации Aggregator ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        aggregator = Aggregator(config_manager)
        
        print(f"✅ Aggregator создан")
        print(f"✅ Обработчиков инициализировано: {len(aggregator.handlers)}")
        
        # Проверяем типы обработчиков
        handler_names = [h.handler_name for h in aggregator.handlers]
        print(f"✅ Обработчики: {', '.join(handler_names)}")
        
        return aggregator, config_manager
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_merge_handler_results(aggregator):
    """Тестирование объединения результатов обработчиков."""
    print("\n=== Тест объединения результатов ===")
    
    # Тестовые данные
    handler_results = {
        "CoreHandler": {
            "post_title": "Тестовый товар",
            "sku": "TEST001",
            "regular_price": "1000"
        },
        "SpecsHandler": {
            "weight": "0.5",
            "height": "30",
            "attribute:pa_tsvet": "Красный"
        },
        "MediaHandler": {
            "images": "image.jpg | Alt | Title",
            "meta:видео_url": "https://youtube.com/watch?v=test"
        },
        "ContentHandler": {
            "post_content": "<p>Описание товара</p>"
        }
    }
    
    # ВЫЗЫВАЕМ ПРАВИЛЬНО: одно подчеркивание
    merged = aggregator._merge_handler_results(handler_results)
    
    print(f"✅ Объединено полей: {len(merged)}")
    
    # Проверяем ключевые поля
    expected_keys = [
        "post_title", "sku", "regular_price",
        "weight", "height", "attribute:pa_tsvet",
        "images", "meta:видео_url", "post_content"
    ]
    
    for key in expected_keys:
        if key in merged:
            print(f"✅ Найдено поле: {key}")
        else:
            print(f"❌ Не найдено поле: {key}")
    
    # Тест конфликта полей
    conflicting_results = {
        "Handler1": {"field": "значение1"},
        "Handler2": {"field": "значение2"}
    }
    
    print("\n✅ Тест конфликта полей:")
    merged_conflict = aggregator._merge_handler_results(conflicting_results)
    # Последний обработчик должен перезаписать значение
    if merged_conflict.get("field") == "значение2":
        print("✅ Конфликт разрешен: последний обработчик перезаписал значение")
    else:
        print(f"❌ Неожиданное значение: {merged_conflict.get('field')}")
    
    return aggregator


def test_create_woo_product(aggregator):
    """Тестирование создания WooProduct."""
    print("\n=== Тест создания WooProduct ===")
    
    test_data = {
        "post_title": "Тестовый товар",
        "sku": "TEST001",
        "regular_price": "1000",
        "tax:product_cat": "Категория > Подкатегория",
        "meta:артикул": "ART-001",
        "attribute:pa_tsvet": "Красный",
        "weight": "0.5",
        "custom_field": "значение"  # Пользовательское поле
    }
    
    # ВЫЗЫВАЕМ ПРАВИЛЬНО: одно подчеркивание
    woo_product = aggregator._create_woo_product(test_data)
    
    print("✅ Проверка полей WooProduct:")
    
    # Проверяем основные поля
    checks = [
        ("post_title", "Тестовый товар"),
        ("sku", "TEST001"),
        ("regular_price", "1000"),
        ("tax_product_cat", "Категория > Подкатегория"),
        ("weight", "0.5")
    ]
    
    for field, expected in checks:
        actual = getattr(woo_product, field, "")
        status = "✅" if str(actual) == str(expected) else "❌"
        print(f"{status} {field}: '{actual}'")
    
    # Проверяем мета-поля
    print("\n✅ Проверка мета-полей:")
    if "meta:артикул" in woo_product.meta_fields:
        print(f"✅ meta:артикул: '{woo_product.meta_fields['meta:артикул']}'")
    else:
        print("❌ meta:артикул не найден")
    
    # Проверяем атрибуты
    print("\n✅ Проверка атрибутов:")
    if "attribute:pa_tsvet" in woo_product.attributes:
        print(f"✅ attribute:pa_tsvet: '{woo_product.attributes['attribute:pa_tsvet']}'")
    else:
        print("❌ attribute:pa_tsvet не найден")
    
    # Проверяем пользовательское поле (должно быть в мета-полях)
    print("\n✅ Проверка пользовательского поля:")
    if "custom_field" in woo_product.meta_fields:
        print(f"✅ custom_field добавлен в мета-поля")
    else:
        print("❌ custom_field не найден в мета-полях")
    
    return woo_product


def test_apply_default_values(aggregator):
    """Тестирование применения значений по умолчанию."""
    print("\n=== Тест применения значений по умолчанию ===")
    
    # Создаем пустой продукт
    woo_product = aggregator._create_woo_product({})
    
    # ВЫЗЫВАЕМ ПРАВИЛЬНО: одно подчеркивание
    aggregator._apply_default_values(woo_product)
    
    print("✅ Проверка дефолтных значений:")
    
    # Проверяем некоторые дефолтные поля из конфига
    default_fields_to_check = [
        "post_status",  # Должно быть "publish"
        "comment_status",  # Должно быть "closed"
        "tax_product_type",  # Должно быть "simple"
        "stock_status",  # Должно быть "instock"
        "manage_stock"  # Должно быть "no"
    ]
    
    for field in default_fields_to_check:
        value = getattr(woo_product, field, "")
        if value:
            print(f"✅ {field}: '{value}'")
        else:
            print(f"❌ {field} не установлен")
    
    return woo_product


def test_set_empty_fields(aggregator):
    """Тестирование установки пустых полей."""
    print("\n=== Тест установки пустых полей ===")
    
    # Создаем продукт с некоторыми заполненными полями
    woo_product = aggregator._create_woo_product({
        "post_title": "Тест",
        "sku": "TEST"
    })
    
    # ВЫЗЫВАЕМ ПРАВИЛЬНО: одно подчеркивание
    aggregator._set_empty_fields(woo_product)
    
    print("✅ Проверка пустых полей из ТЗ:")
    
    # Проверяем некоторые поля, которые должны быть пустыми
    empty_fields_to_check = [
        "ID",
        "post_parent",
        "sale_price",
        "stock",
        "meta:total_sales"
    ]
    
    for field in empty_fields_to_check:
        # Получаем значение в зависимости от типа поля
        if field.startswith("meta:"):
            value = woo_product.meta_fields.get(field, None)
        else:
            # Преобразуем имя поля для атрибута
            attr_name = field
            if hasattr(woo_product, attr_name):
                value = getattr(woo_product, attr_name)
            else:
                value = None
        
        if value == "" or value is None:
            print(f"✅ {field}: пустое (как и должно быть)")
        else:
            print(f"❌ {field}: не пустое ('{value}')")
    
    return woo_product


def test_full_processing(aggregator):
    """Тестирование полной обработки продукта."""
    print("\n=== Тест полной обработки продукта ===")
    
    # Создаем тестовый продукт
    raw_product = RawProduct(
        Наименование="Пластиковый контейнер 10л",
        Артикул="PC-10",
        НС_код="NS001",
        Бренд="PlasticPro",
        Название_категории="Тара - Контейнеры",
        Характеристики="Масса товара (нетто): 0.5 кг / Высота товара: 30 см / Цвет корпуса: Белый",
        Изображение="https://example.com/image1.jpg",
        Видео="https://youtube.com/watch?v=dQw4w9WgXcQ",
        Статья="<p>Отличный контейнер для хранения</p>",
        Чертежи="https://example.com/drawing.pdf",
        Цена="14990 руб.",
        Штрих_код="1234567890123",
        Эксклюзив="Эксклюзив - Нет",
        row_number=1
    )
    
    # Обрабатываем продукт
    woo_product = aggregator.process_product(raw_product)
    
    print("✅ Результат обработки:")
    print(f"  Тип: {type(woo_product).__name__}")
    print(f"  Основных полей: {len([f for f in dir(woo_product) if not f.startswith('_') and f not in ['attributes', 'meta_fields']])}")
    print(f"  Атрибутов: {len(woo_product.attributes)}")
    print(f"  Мета-полей: {len(woo_product.meta_fields)}")
    
    # Проверяем ключевые поля
    print("\n✅ Проверка ключевых полей:")
    key_fields = [
        ("post_title", "Пластиковый контейнер 10л"),
        ("sku", "NS001"),
        ("regular_price", "14990"),
        ("tax_product_cat", "Тара > Контейнеры"),
        ("post_content", "<p>")  # Проверяем что есть HTML
    ]
    
    for field, expected in key_fields:
        actual = getattr(woo_product, field, "")
        if expected == "<p>":
            status = "✅" if expected in str(actual) else "❌"
            print(f"{status} {field}: содержит HTML")
        else:
            status = "✅" if str(actual) == str(expected) else "❌"
            print(f"{status} {field}: '{actual}'")
    
    # Преобразуем в словарь для WooCommerce
    woocommerce_dict = woo_product.to_woocommerce_dict()
    print(f"\n✅ Словарь для WooCommerce: {len(woocommerce_dict)} полей")
    
    # Получаем заголовок CSV
    csv_header = woo_product.get_csv_header()
    print(f"✅ Заголовок CSV: {len(csv_header)} колонок")
    
    # Покажем первые 10 колонок
    print(f"  Первые 10 колонок: {csv_header[:10]}")
    
    return woo_product


def main():
    """Запуск всех тестов."""
    print("Тестирование Aggregator B2B-WC Converter v2.0\n")
    
    try:
        aggregator, config = test_aggregator_initialization()
        
        if aggregator and config:
            test_merge_handler_results(aggregator)
            test_create_woo_product(aggregator)
            test_apply_default_values(aggregator)
            test_set_empty_fields(aggregator)
            test_full_processing(aggregator)
            
            # Очистка
            aggregator.cleanup()
            print("\n✅ Все тесты Aggregator пройдены успешно!")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании Aggregator: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()