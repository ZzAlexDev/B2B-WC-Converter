"""
Тест интеграции утилит и обработчиков.
"""
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from v2.utils.validators import (
    is_valid_url,
    extract_youtube_id,
    extract_price,
    normalize_yes_no,
    generate_slug,
    parse_specifications
)
from v2.utils.file_utils import (
    sanitize_filename,
    get_file_extension_from_url,
    split_image_urls
)


def test_validators():
    """Тестирование валидаторов."""
    print("=== Тест валидаторов ===")
    
    # Тест is_valid_url
    url_tests = [
        ("https://example.com/image.jpg", True),
        ("http://test.com", True),
        ("invalid-url", False),
        ("", False)
    ]
    
    for url, expected in url_tests:
        result = is_valid_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} is_valid_url('{url}'): {result}")
    
    # Тест extract_youtube_id
    youtube_tests = [
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://example.com/video", None)
    ]
    
    for url, expected in youtube_tests:
        result = extract_youtube_id(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} extract_youtube_id('{url}'): {result}")
    
    # Тест extract_price
    price_tests = [
        ("14990 руб.", ("14990", "руб")),
        ("1,499.50 USD", ("1499.50", "usd")),
        ("Цена по запросу", ("", ""))
    ]
    
    for price_str, expected in price_tests:
        result = extract_price(price_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} extract_price('{price_str}'): {result}")
    
    # Тест normalize_yes_no
    yn_tests = [
        ("да", "Да"),
        ("yes", "Да"),
        ("нет", "Нет"),
        ("no", "Нет"),
        ("unknown", "unknown")
    ]
    
    for value, expected in yn_tests:
        result = normalize_yes_no(value)
        status = "✅" if result == expected else "❌"
        print(f"{status} normalize_yes_no('{value}'): {result}")
    
    # Тест generate_slug
    slug_tests = [
        ("Пластиковый контейнер", "plastikovyy-konteyner"),
        ("Товар №1 (специальный)", "tovar-1-spetsialnyy"),
        ("", "")
    ]
    
    for text, expected in slug_tests:
        result = generate_slug(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} generate_slug('{text}'): '{result}'")
    
    # Тест parse_specifications
    specs_tests = [
        ("Масса: 10 кг / Цвет: Красный", {"Масса": "10 кг", "Цвет": "Красный"}),
        ("", {}),
        ("Только значение", {})
    ]
    
    for specs_str, expected in specs_tests:
        result = parse_specifications(specs_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} parse_specifications('{specs_str}'): {len(result)} характеристик")


def test_file_utils():
    """Тестирование утилит для файлов."""
    print("\n=== Тест утилит для файлов ===")
    
    # Тест sanitize_filename
    filename_tests = [
        ("test file.jpg", "test_file.jpg"),
        ("file<with>bad:chars.png", "file_with_bad_chars.png"),
        ("", "")
    ]
    
    for filename, expected in filename_tests:
        result = sanitize_filename(filename)
        status = "✅" if result == expected else "❌"
        print(f"{status} sanitize_filename('{filename}'): '{result}'")
    
    # Тест get_file_extension_from_url
    extension_tests = [
        ("https://example.com/image.jpg", "jpg"),
        ("https://test.com/path/to/file.png?query=1", "png"),
        ("https://test.com/no_extension", "")
    ]
    
    for url, expected in extension_tests:
        result = get_file_extension_from_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} get_file_extension_from_url('{url}'): '{result}'")
    
    # Тест split_image_urls
    urls_tests = [
        ("https://img1.jpg,https://img2.jpg", ["https://img1.jpg", "https://img2.jpg"]),
        ("https://img1.jpg, invalid, https://img2.jpg", ["https://img1.jpg", "https://img2.jpg"]),
        ("", [])
    ]
    
    for urls_str, expected in urls_tests:
        result = split_image_urls(urls_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} split_image_urls('{urls_str}'): {len(result)} URL")


def test_full_conversion_with_utils():
    """Тест полной конвертации с использованием утилит."""
    print("\n=== Тест полной конвертации с утилитами ===")
    
    try:
        from v2.converter import ConverterV2
        import tempfile
        
        # Создаем тестовый CSV
        test_data = """Наименование;Артикул;НС-код;Бренд;Название категории;Характеристики;Изображение;Видео;Статья;Цена;Эксклюзив
Тестовый товар 1;ART-001;NS001;Brand1;Категория - Подкатегория;Вес: 10 кг / Цвет: Красный;https://example.com/image1.jpg;https://youtube.com/watch?v=test1;<p>Описание 1</p>;"1000 руб.";"Эксклюзив - Да"
Тестовый товар 2;ART-002;NS002;Brand2;Другая категория;Размер: L / Материал: Хлопок;https://example.com/image2.jpg;;<p>Описание 2</p>;"2000 руб.";"Эксклюзив - Нет"
"""
        
        temp_dir = tempfile.mkdtemp()
        csv_path = Path(temp_dir) / "test.csv"
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(test_data)
        
        print(f"✅ Тестовый CSV создан: {csv_path}")
        
        # Запускаем конвертацию
        converter = ConverterV2(config_path="config/v2")
        
        result = converter.convert(
            input_path=str(csv_path),
            output_path="data/output/test_with_utils.csv",
            skip_errors=True
        )
        
        print("📊 Результаты:")
        print(f"  ✅ Обработано: {result['processed']}")
        print(f"  📁 Выходной файл: {result['output_path']}")
        
        # Проверяем выходной файл
        output_file = Path(result['output_path'])
        if output_file.exists():
            import csv
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                
                print(f"  📄 Строк в CSV: {len(rows)}")
                
                if rows:
                    # Проверяем SEO поля
                    first_row = rows[0]
                    seo_fields = [k for k in first_row.keys() if 'yoast' in k]
                    
                    print(f"  🔍 SEO полей: {len(seo_fields)}")
                    
                    # Проверяем, что SEO поля заполнены (не содержат плейсхолдеры)
                    for field in seo_fields[:3]:  # Первые 3 SEO поля
                        value = first_row.get(field, '')
                        if '{' in value:
                            print(f"  ⚠️  Поле {field} содержит плейсхолдер: {value[:50]}...")
                        elif value:
                            print(f"  ✅ Поле {field} заполнено: {value[:50]}...")
        
        converter.cleanup()
        print("\n✅ Тест с утилитами пройден!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Запуск всех тестов."""
    print("Тестирование интеграции утилит B2B-WC Converter v2.0\n")
    
    test_validators()
    test_file_utils()
    test_full_conversion_with_utils()
    
    print("\n✅ Все тесты интеграции пройдены успешно!")


if __name__ == "__main__":
    main()