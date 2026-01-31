"""
Тестирование моделей данных.
"""
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / "src"))

from v2.models import RawProduct, WooProduct, ProcessingStats


def test_raw_product():
    """Тестирование создания RawProduct из CSV строки."""
    print("=== Тест RawProduct ===")
    
    # Тестовая строка CSV
    csv_row = {
        "Наименование": "Пластиковый контейнер 10л",
        "Артикул": "PC-10",
        "НС-код": "NS001",
        "Бренд": "PlasticPro",
        "Название категории": "Тара - Контейнеры",
        "Характеристики": "Масса товара (нетто): 0.5 кг",
        "Изображение": "https://example.com/image.jpg",
        "Цена": "14990 руб."
    }
    
    # Создаем продукт
    product = RawProduct.from_csv_row(csv_row, row_number=1)
    
    print(f"Наименование: {product.Наименование}")
    print(f"Артикул: {product.Артикул}")
    print(f"НС_код: {product.НС_код}")
    print(f"Бренд: {product.Бренд}")
    print(f"Название_категории: {product.Название_категории}")
    print(f"row_number: {product.row_number}")
    
    # Проверяем преобразование в словарь
    print(f"\nИсходные данные: {product.raw_data}")
    
    return product


def test_woo_product():
    """Тестирование создания WooProduct."""
    print("\n=== Тест WooProduct ===")
    
    # Создаем продукт WooCommerce
    woo_product = WooProduct(
        post_title="Тестовый товар",
        post_name="testovyy-tovar",
        sku="TEST001",
        regular_price="1000",
        stock_status="instock",
        tax_product_type="simple",
        tax_product_cat="Категория 1 > Подкатегория"
    )
    
    # Добавляем атрибуты
    woo_product.attributes["attribute:pa_tsvet"] = "Красный"
    woo_product.attributes["attribute:pa_razmer"] = "L"
    
    # Добавляем мета-поля
    woo_product.meta_fields["meta:_global_unique_id"] = "123456789"
    woo_product.meta_fields["meta:артикул"] = "ART-001"
    
    # Преобразуем в словарь для CSV
    csv_dict = woo_product.to_woocommerce_dict()
    
    print("Поля WooProduct:")
    for key, value in csv_dict.items():
        print(f"  {key}: {value}")
    
    print(f"\nЗаголовок CSV: {woo_product.get_csv_header()}")
    
    return woo_product


def test_processing_stats():
    """Тестирование статистики."""
    print("\n=== Тест ProcessingStats ===")
    
    stats = ProcessingStats(
        total_rows=100,
        processed=95,
        skipped=3,
        errors=2
    )
    
    stats.start()
    # Имитируем задержку
    import time
    time.sleep(0.1)
    stats.finish()
    
    print(f"Статистика: {stats.to_dict()}")
    print(f"Длительность: {stats.get_duration():.2f} секунд")
    
    return stats


def main():
    """Запуск всех тестов."""
    print("Тестирование моделей данных B2B-WC Converter v2.0\n")
    
    try:
        raw_product = test_raw_product()
        woo_product = test_woo_product()
        stats = test_processing_stats()
        
        print("\n✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()