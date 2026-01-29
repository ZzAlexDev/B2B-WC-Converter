"""
Тест для ProductBuilder
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.processors.product_builder import ProductBuilder


def test_product_builder():
    """Тестирование сборщика товара"""
    print("🧪 Тестирование ProductBuilder...")
    
    # Загружаем конфиг
    config = {}
    try:
        with open("config/settings.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except:
        print("⚠️  Не удалось загрузить конфиг, используем пустой")
    
    # Создаем сборщик
    builder = ProductBuilder(config)
    
    # Тестовые данные (как из XLSX)
    test_row = {
        "Наименование": "Завеса воздушная Ballu BHC-U15A-PS",
        "Артикул": "BHC-U15A-PS",
        "Бренд": "Ballu",
        "Название категории": "Тепловое оборудование - Воздушные и тепловые завесы - Промышленные",
        "Характеристики": "Вариант размещения: Универсальное; Гарантийный срок: 2 года; Страна производства: РОССИЯ; Макс. потребляемая мощность: 0.77 кВт",
        "Изображение": "https://rkcdn.ru/products/d6c82432-5174-11ee-b737-005056941658/src.jpg,https://rkcdn.ru/products/f27bf0f0-5174-11ee-b737-005056941658/src.jpg",
        "Видео": "",
        "Статья": "<p>Пылевлагозащищенная завеса BALLU BHC-U15A-PS c максимальной производительностью 4700 м3/ч.</p>",
        "Чертежи": "",
        "Сертификаты": "https://rkcdn.ru/products/8569dc4e-7ad7-11eb-b72a-005056010604/src.pdf",
        "Промоматериалы": "",
        "Инструкции": "https://rkcdn.ru/products/2d72fa9c-129d-11ef-b8d8-00505601218a/src.pdf",
        "Штрих код": "4680551012514",
        "Цена": "99990 руб.",
        "НС-код": "НС-1183726",
        "Эксклюзив": "Нет"
    }
    
    # Тест 1: Сборка товара
    print("\n1. Сборка товара из тестовой строки:")
    product = builder.build_from_row(test_row, 1)
    
    if product:
        print(f"   ✅ Успешно создан товар:")
        print(f"   Название: {product.name}")
        print(f"   SKU: {product.sku}")
        print(f"   Цена: {product.price}")
        print(f"   Категория: {' > '.join(product.category_hierarchy)}")
        print(f"   Бренд: {product.brand}")
        print(f"   Изображения: {len(product.images_local)}")
        print(f"   Документы: {len(product.documents)} типов")
        print(f"   Длина описания: {len(product.description_final)} символов")
        print(f"   WC полей: {len(product.wc_fields)}")
    else:
        print("   ❌ Не удалось создать товар")
    
    # Тест 2: Статистика
    print("\n2. Статистика обработки:")
    stats = builder.get_stats()
    print(f"   Обработано: {stats['total_processed']}")
    print(f"   Успешно: {stats['successful']}")
    print(f"   Ошибок: {stats['failed']}")
    print(f"   Успешность: {stats['success_rate']:.1f}%")
    
    # Тест 3: Проверка WC полей
    if product:
        print("\n3. Проверка WC полей:")
        required_wc_fields = ["post_title", "post_name", "post_content", "sku", "regular_price"]
        for field in required_wc_fields:
            value = product.get_wc_field(field, "НЕТ")
            print(f"   {field}: {'✅' if value != 'НЕТ' else '❌'} {value[:50] if value else ''}")
    
    # Тест 4: Экспорт в словарь
    if product:
        print("\n4. Экспорт товара в словарь:")
        product_dict = product.to_dict()
        print(f"   Ключи: {list(product_dict.keys())}")
        print(f"   Значения: {json.dumps(product_dict, ensure_ascii=False, indent=2)[:200]}...")
    
    print("\n✅ Все тесты завершены!")
    return product is not None


if __name__ == "__main__":
    success = test_product_builder()
    sys.exit(0 if success else 1)