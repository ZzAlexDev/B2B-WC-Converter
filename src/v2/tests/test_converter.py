"""
Тестирование ConverterV2.
Запуск из корня проекта: python -m src.v2.tests.test_converter
"""
import sys
from pathlib import Path
import csv
import tempfile

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.v2.converter import ConverterV2


def create_test_csv() -> Path:
    """Создает тестовый CSV файл."""
    test_data = """Наименование;Артикул;НС-код;Бренд;Название категории;Характеристики;Изображение;Видео;Статья;Чертежи;Сертификаты;Промоматериалы;Инструкции;Штрих код;Цена;Эксклюзив
Пластиковый контейнер 10л;PC-10;NS001;PlasticPro;Тара - Контейнеры;Масса товара (нетто): 0.5 кг / Высота товара: 30 см / Ширина товара: 20 см / Глубина товара: 15 см / Область применения: Хранение / Цвет корпуса: Белый / Страна производства: Россия;https://example.com/image1.jpg,https://example.com/image2.jpg;https://youtube.com/watch?v=dQw4w9WgXcQ;<p>Отличный контейнер для хранения</p>;https://example.com/drawing.pdf;https://example.com/certificate.pdf;;https://example.com/instructions.pdf;1234567890123/2345678901234;"14990 руб.";"Эксклюзив - Нет"
Металлический шкаф;MS-200;NS002;MetalWorks;Мебель - Шкафы - Офисные;Масса товара (нетто): 15 кг / Высота товара: 180 см / Ширина товара: 60 см / Глубина товара: 40 см / Область применения: Офис / Цвет корпуса: Серый / Гарантийный срок: 2 года;https://example.com/cabinet.jpg;;<p>Прочный металлический шкаф</p>;;;;;9876543210987;"24500 руб.";"Эксклюзив - Да"
Товар без обязательных полей;;NS003;Brand;;Характеристики;;;;;;;;"1000 руб.";"Эксклюзив - Нет"
"""
    
    # Создаем временный файл
    temp_dir = tempfile.mkdtemp()
    csv_path = Path(temp_dir) / "test_products.csv"
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(test_data)
    
    print(f"✅ Тестовый CSV создан: {csv_path}")
    return csv_path


def test_converter_initialization():
    """Тестирование инициализации ConverterV2."""
    print("=== Тест инициализации ConverterV2 ===")
    
    try:
        converter = ConverterV2(config_path="config/v2")
        
        print(f"✅ ConverterV2 создан")
        print(f"✅ ConfigManager загружен: {converter.config_manager is not None}")
        print(f"✅ Aggregator инициализирован: {converter.aggregator is not None}")
        
        return converter
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_validate_raw_product(converter):
    """Тестирование валидации сырого продукта."""
    print("\n=== Тест валидации продукта ===")
    
    from src.v2.models import RawProduct
    
    # Тестовые продукты
    test_cases = [
        {
            "product": RawProduct(Наименование="Товар", НС_код="TEST001"),
            "expected": True,
            "description": "Есть все обязательные поля"
        },
        {
            "product": RawProduct(Наименование="", НС_код="TEST002"),
            "expected": False,
            "description": "Нет названия"
        },
        {
            "product": RawProduct(Наименование="Товар", НС_код=""),
            "expected": False,
            "description": "Нет НС-кода"
        },
        {
            "product": RawProduct(),
            "expected": False,
            "description": "Пустой продукт"
        }
    ]
    
    for test in test_cases:
        # ИСПРАВЛЕНО: одно подчеркивание вместо двух
        result = converter._validate_raw_product(test["product"])
        status = "✅" if result == test["expected"] else "❌"
        print(f"{status} {test['description']}: {result} (ожидалось: {test['expected']})")
    
    return converter


def test_csv_processing(converter):
    """Тестирование обработки CSV файла."""
    print("\n=== Тест обработки CSV ===")
    
    # Создаем тестовый CSV
    csv_path = create_test_csv()
    
    try:
        # Обрабатываем CSV
        result = converter.convert(
            input_path=str(csv_path),
            output_path="data/output/test_output.csv",
            skip_errors=True
        )
        
        print("✅ Результат конвертации:")
        print(f"  Обработано: {result['processed']}")
        print(f"  Пропущено: {result['skipped']}")
        print(f"  Ошибок: {result['errors']}")
        print(f"  Выходной файл: {result['output_path']}")
        print(f"  Длительность: {result['duration']:.2f} секунд")
        
        # Проверяем выходной файл
        output_file = Path(result['output_path'])
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                print(f"  Строк в выходном файле: {len(rows)}")
                
                if rows:
                    print(f"  Колонок в CSV: {len(rows[0])}")
                    print(f"  Первые 5 колонок: {list(rows[0].keys())[:5]}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при обработке CSV: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_export_to_csv(converter):
    """Тестирование экспорта в CSV."""
    print("\n=== Тест экспорта в CSV ===")
    
    from src.v2.models import WooProduct
    import tempfile
    
    # Создаем тестовые продукты
    woo_products = []
    
    for i in range(3):
        product = WooProduct(
            post_title=f"Тестовый товар {i+1}",
            sku=f"TEST{i+1}",
            regular_price=str((i+1) * 1000),
            tax_product_type="simple",
            stock_status="instock"
        )
        
        # Добавляем разные мета-поля
        product.meta_fields[f"meta:поле_{i+1}"] = f"значение_{i+1}"
        
        # Добавляем разные атрибуты
        if i == 0:
            product.attributes["attribute:pa_tsvet"] = "Красный"
        elif i == 1:
            product.attributes["attribute:pa_razmer"] = "L"
        
        woo_products.append(product)
    
    # Создаем временный файл
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
    temp_file.close()
    output_path = Path(temp_file.name)
    
    try:
        # ИСПРАВЛЕНО: одно подчеркивание вместо двух
        converter._export_to_csv(woo_products, output_path)
        
        # Проверяем результат
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            
            print(f"✅ Экспортировано строк: {len(rows)}")
            print(f"✅ Колонок в CSV: {len(rows[0]) if rows else 0}")
            
            if rows:
                # Проверяем наличие ключевых полей
                expected_fields = ['post_title', 'sku', 'regular_price', 'tax:product_type']
                for field in expected_fields:
                    if field in rows[0]:
                        print(f"✅ Найдено поле: {field}")
                    else:
                        print(f"❌ Не найдено поле: {field}")
                
                # Проверяем разные продукты
                print(f"\n✅ Проверка данных:")
                for i, row in enumerate(rows[:2]):  # Покажем первые 2
                    print(f"  Товар {i+1}: {row.get('post_title', '')}, цена: {row.get('regular_price', '')}")
    
    finally:
        # Удаляем временный файл
        if output_path.exists():
            output_path.unlink()
    
    return woo_products


def test_full_conversion():
    """Тестирование полной конвертации."""
    print("\n=== Тест полной конвертации ===")
    
    try:
        converter = ConverterV2(config_path="config/v2")
        
        # Создаем тестовый CSV
        csv_path = create_test_csv()
        
        # Выполняем конвертацию
        print("🚀 Запуск полной конвертации...")
        result = converter.convert(
            input_path=str(csv_path),
            output_path="data/output/full_test_output.csv",
            skip_errors=True
        )
        
        print("\n📊 Результаты конвертации:")
        print(f"  ✅ Обработано товаров: {result['processed']}")
        print(f"  ⚠️  Пропущено товаров: {result['skipped']}")
        print(f"  ❌ Ошибок: {result['errors']}")
        print(f"  📁 Выходной файл: {result['output_path']}")
        print(f"  ⏱️  Время выполнения: {result['duration']:.2f} секунд")
        
        # Проверяем выходной файл
        output_file = Path(result['output_path'])
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                
                print(f"\n📄 Выходной CSV:")
                print(f"  Строк: {len(rows)}")
                print(f"  Колонок: {len(rows[0]) if rows else 0}")
                
                if rows:
                    # Покажем первые 2 строки
                    print(f"\nПервая строка (первые 5 полей):")
                    for i, (key, value) in enumerate(list(rows[0].items())[:5]):
                        print(f"  {key}: {value}")
        
        # Очистка
        converter.cleanup()
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при полной конвертации: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Запуск всех тестов."""
    print("Тестирование ConverterV2 B2B-WC Converter v2.0\n")
    
    try:
        converter = test_converter_initialization()
        
        if converter:
            test_validate_raw_product(converter)
            test_csv_processing(converter)
            test_export_to_csv(converter)
            test_full_conversion()
            
            print("\n✅ Все тесты ConverterV2 пройдены успешно!")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании ConverterV2: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()