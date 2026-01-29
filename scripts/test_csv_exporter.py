"""
Тест для CSVExporter
"""

import sys
import os
import json
import tempfile
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.exporters.csv_exporter import CSVExporter, export_products_to_csv, validate_csv_file
from src.core.models.product import Product
from typing import List

def create_test_products(count: int = 3) -> List[Product]:
    """Создание нескольких тестовых товаров"""
    products = []
    
    for i in range(count):
        product = Product(id=i+1, source_row=i+1)
        
        # Заполняем данные
        product.name = f"Тестовый товар {i+1} Ballu Model-{i+1}"
        product.wc_slug = f"testovyj-tovar-{i+1}-ballu"
        product.sku = f"NS-{1000 + i}"
        product.price = 1000.0 * (i + 1)
        product.category_hierarchy = ["Категория", f"Подкатегория {i+1}"]
        product.brand = "Ballu"
        
        # WC поля
        product.wc_fields = {
            "post_title": product.name,
            "post_name": product.wc_slug,
            "post_content": f"<p>Описание товара {i+1}</p>",
            "post_excerpt": f"Короткое описание {i+1}",
            "sku": product.sku,
            "regular_price": str(product.price),
            "tax:product_type": "simple",
            "tax:product_cat": " > ".join(product.category_hierarchy),
            "tax:product_brand": product.brand.lower(),
            "stock_status": "instock"
        }
        
        # Атрибуты
        product.main_attributes = {
            "Гарантийный срок": f"{i+1} года",
            "Страна производства": ["РОССИЯ", "КНР", "Германия"][i % 3]
        }
        
        products.append(product)
    
    return products


def test_csv_exporter():
    """Тестирование CSV экспортера"""
    print("🧪 Тестирование CSVExporter...")
    
    # Загружаем конфиг
    config = {}
    try:
        with open("config/settings.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except:
        print("⚠️  Не удалось загрузить конфиг")
    
    # Создаем тестовые товары
    products = create_test_products(3)
    
    # Создаем временный файл для тестов
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        test_csv_path = tmp.name
    
    try:
        # Создаем экспортер
        exporter = CSVExporter(config)
        
        # Тест 1: Экспорт товаров
        print("\n1. Экспорт товаров в CSV:")
        result = exporter.export_products(products, test_csv_path)
        
        print(f"   Успешно: {result['exported']}/{result['total_products']}")
        print(f"   Файл: {test_csv_path}")
        print(f"   Размер: {result['file_size']} байт")
        
        # Проверяем что файл создан
        if Path(test_csv_path).exists():
            print("   ✅ Файл успешно создан")
        else:
            print("   ❌ Файл не создан")
            return False
        
        # Тест 2: Валидация CSV
        print("\n2. Валидация CSV файла:")
        validation = exporter.validate_csv(test_csv_path)
        
        print(f"   Валиден: {'✅' if validation['is_valid'] else '❌'}")
        print(f"   Строк: {validation['row_count']}")
        
        if validation['errors']:
            print(f"   Ошибки: {validation['errors']}")
        else:
            print("   ✅ Ошибок нет")
        
        # Показываем пример данных
        if validation['sample_data']:
            print(f"   Заголовки: {len(validation['sample_data']['headers'])} полей")
            print(f"   Пример строки: {json.dumps(validation['sample_data']['first_row'], ensure_ascii=False)}")
        
        # Тест 3: Быстрая функция экспорта
        print("\n3. Тест быстрой функции экспорта:")
        test_csv_path2 = test_csv_path.replace('.csv', '_quick.csv')
        success = export_products_to_csv(products, test_csv_path2, config)
        
        print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
        if Path(test_csv_path2).exists():
            print(f"   Файл создан: {test_csv_path2}")
        
        # Тест 4: Быстрая функция валидации
        print("\n4. Тест быстрой функции валидации:")
        quick_validation = validate_csv_file(test_csv_path)
        
        print(f"   Валиден: {'✅' if quick_validation['is_valid'] else '❌'}")
        print(f"   Строк: {quick_validation['row_count']}")
        
        # Тест 5: Чтение CSV для проверки содержимого
        print("\n5. Проверка содержимого CSV:")
        with open(test_csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            print(f"   Всего строк в файле: {len(lines)}")
            
            if len(lines) > 1:
                print(f"   Первая строка данных: {lines[1][:100]}...")
        
        print("\n✅ Все тесты CSVExporter завершены!")
        return result['exported'] == result['total_products']
        
    finally:
        # Удаляем временные файлы
        try:
            if Path(test_csv_path).exists():
                Path(test_csv_path).unlink()
                print(f"\n🗑️  Удален временный файл: {test_csv_path}")
            
            test_csv_path2 = test_csv_path.replace('.csv', '_quick.csv')
            if Path(test_csv_path2).exists():
                Path(test_csv_path2).unlink()
                
        except:
            pass


if __name__ == "__main__":
    # Импортируем List
    from typing import List
    success = test_csv_exporter()
    sys.exit(0 if success else 1)