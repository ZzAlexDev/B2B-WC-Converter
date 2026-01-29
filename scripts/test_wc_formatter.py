"""
Тест для WCFormatter
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.processors.wc_formatter import WCFormatter
from src.core.models.product import Product


def create_test_product() -> Product:
    """Создание тестового товара"""
    product = Product(id=1, source_row=1)
    
    # Заполняем данные
    product.name = "Тестовый товар Ballu BHC-U15A-PS"
    product.wc_slug = "testovyi-tovar-ballu-bhc-u15a-ps"
    product.sku = "НС-1183726"
    product.article = "BHC-U15A-PS"
    product.brand = "Ballu"
    product.price = 99990.0
    product.category_hierarchy = ["Тепловое оборудование", "Воздушные завесы", "Промышленные"]
    product.exclusive = False
    
    # Характеристики
    product.specs_dict = {
        "Гарантийный срок": "2 года",
        "Страна производства": "РОССИЯ",
        "Макс. потребляемая мощность": "0.77 кВт",
        "Масса товара (нетто)": "45.3 кг"
    }
    product.main_attributes = {
        "Гарантийный срок": "2 года",
        "Страна производства": "РОССИЯ",
        "Макс. потребляемая мощность": "0.77 кВт"
    }
    
    # Описание
    product.description_final = "<p>Тестовое описание товара.</p>"
    
    # WC поля
    product.wc_fields = {
        "post_title": product.name,
        "post_name": product.wc_slug,
        "post_content": product.description_final,
        "post_excerpt": "Тестовое короткое описание",
        "sku": product.sku,
        "regular_price": "99990.00",
        "tax:product_type": "simple",
        "tax:product_cat": "Тепловое оборудование > Воздушные завесы > Промышленные",
        "tax:product_brand": "ballu",
        "images": "https://example.com/image1.jpg ! alt: Тестовый товар",
        "stock_status": "instock"
    }
    
    # Штрихкод
    product.barcode_clean = "4680551012514"
    
    return product


def test_wc_formatter():
    """Тестирование форматтера WC"""
    print("🧪 Тестирование WCFormatter...")
    
    # Загружаем конфиг
    config = {}
    try:
        with open("config/settings.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except:
        print("⚠️  Не удалось загрузить конфиг")
    
    # Создаем форматтер
    formatter = WCFormatter(config)
    
    # Создаем тестовый товар
    product = create_test_product()
    
    # Тест 1: Форматирование одного товара
    print("\n1. Форматирование товара для WC CSV:")
    csv_row = formatter.format_product(product)
    
    print(f"   ✅ Успешно отформатировано полей: {len(csv_row)}")
    
    # Проверяем обязательные поля
    required_fields = ["post_title", "post_name", "post_content", "sku", "regular_price"]
    for field in required_fields:
        value = csv_row.get(field, "НЕТ")
        print(f"   {field}: {'✅' if value != 'НЕТ' else '❌'} {value[:50] if value else ''}")
    
    # Тест 2: Атрибуты
    print("\n2. Проверка атрибутов:")
    attribute_fields = [f for f in csv_row.keys() if f.startswith("attribute:pa_")]
    print(f"   Найдено атрибутов: {len(attribute_fields)}")
    for attr in attribute_fields[:3]:  # Показываем первые 3
        print(f"   {attr}: {csv_row[attr][:30]}")
    
    # Тест 3: Заголовки CSV
    print("\n3. Генерация заголовков CSV:")
    headers = formatter.get_csv_headers([product])
    print(f"   Всего заголовков: {len(headers)}")
    print(f"   Примеры: {headers[:10]}")
    
    # Тест 4: Slugify атрибутов
    print("\n4. Генерация slug для атрибутов:")
    test_attributes = ["Цвет корпуса", "Страна производства", "Гарантийный срок"]
    for attr in test_attributes:
        slug = formatter._slugify_attribute(attr)
        print(f"   '{attr}' -> '{slug}'")
    
    # Тест 5: Форматирование значения
    print("\n5. Форматирование значений для CSV:")
    test_values = [
        ("Просто текст", "Просто текст"),
        ('Текст с "кавычками"', '"Текст с ""кавычками"""'),
        ("Текст с, запятой", '"Текст с, запятой"')
    ]
    
    for original, expected in test_values:
        formatted = formatter._format_value(original)
        print(f"   '{original}' -> '{formatted}'")
    
    print("\n✅ Все тесты WCFormatter завершены!")
    return True


if __name__ == "__main__":
    success = test_wc_formatter()
    sys.exit(0 if success else 1)