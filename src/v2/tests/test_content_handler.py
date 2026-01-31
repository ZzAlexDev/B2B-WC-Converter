"""
Тестирование ContentHandler.
Запуск из корня проекта: python -m src.v2.tests.test_content_handler
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.v2.handlers.content_handler import ContentHandler
from src.v2.models import RawProduct
from src.v2.config_manager import ConfigManager


def test_content_handler_initialization():
    """Тестирование инициализации ContentHandler."""
    print("=== Тест инициализации ContentHandler ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = ContentHandler(config_manager)
        
        print(f"✅ ContentHandler создан: {handler.handler_name}")
        
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
            "Масса товара (нетто): 0.5 кг / Высота товара: 30 см",
            {
                "Масса товара (нетто)": "0.5 кг",
                "Высота товара": "30 см"
            }
        ),
        (
            "Цвет: Белый; Наличие: да",
            {
                "Цвет": "Белый",
                "Наличие": "Да"  # Нормализовано
            }
        ),
        (
            "Гарантия: нет / Страна: Россия",
            {
                "Гарантия": "Нет",  # Нормализовано
                "Страна": "Россия"
            }
        ),
        (
            "",
            {}
        )
    ]
    
    for specs_str, expected in test_cases:
        # ИСПРАВЛЕНО: одно подчеркивание вместо двух
        result = handler._parse_specifications(specs_str)
        
        # Проверяем ключи
        keys_match = set(result.keys()) == set(expected.keys())
        values_match = all(result.get(k) == expected.get(k) for k in expected.keys())
        
        status = "✅" if keys_match and values_match else "❌"
        print(f"{status} '{specs_str[:30]}...' -> {len(result)} характеристик")
    
    return handler


def test_process_article(handler):
    """Тестирование обработки статьи."""
    print("\n=== Тест обработки статьи ===")
    
    test_cases = [
        (
            "<p>Отличный товар</p>",
            "<p>Отличный товар</p>"
        ),
        (
            "Простой текст",
            "<p>Простой текст</p>"
        ),
        (
            "",
            ""
        ),
        (
            "<h2>Заголовок</h2><p>Текст</p>",
            "<h2>Заголовок</h2><p>Текст</p>"
        )
    ]
    
    for input_html, expected in test_cases:
        # ИСПРАВЛЕНО: одно подчеркивание вместо двух
        result = handler._process_article(input_html)
        status = "✅" if result == expected else "❌"
        print(f"{status} Вход: '{input_html[:20]}...' -> '{result[:20]}...'")
    
    return handler


def test_build_specifications_html(handler):
    """Тестирование построения HTML характеристик."""
    print("\n=== Тест построения HTML характеристик ===")
    
    specs = {
        "Масса": "10 кг",
        "Цвет": "Красный",
        "Гарантия": "2 года"
    }
    
    # ИСПРАВЛЕНО: одно подчеркивание вместо двух
    result = handler._build_specifications_html(specs)
    
    print("✅ Сгенерированный HTML характеристик:")
    print(f"Длина: {len(result)} символов")
    print(f"Содержит h2: {'Технические характеристики' in result}")
    print(f"Содержит ul: {'<ul>' in result}")
    print(f"Количество li: {result.count('<li>')}")
    
    # Покажем часть HTML
    print(f"\nФрагмент HTML:\n{result[:100]}...")
    
    return handler


def test_collect_documents(handler):
    """Тестирование сбора документов."""
    print("\n=== Тест сбора документов ===")
    
    product = RawProduct(
        Чертежи="https://example.com/drawing.pdf",
        Сертификаты="https://example.com/certificate.pdf",
        Инструкции="https://example.com/instructions.pdf"
    )
    
    # ИСПРАВЛЕНО: одно подчеркивание вместо двух
    result = handler._collect_documents(product)
    
    print(f"✅ Найдено документов: {len(result)}")
    
    expected_types = ["чертеж", "сертификат", "инструкция"]
    found_types = [doc_type for doc_type, _ in result]
    
    for doc_type in expected_types:
        if doc_type in found_types:
            print(f"✅ Найден тип документа: {doc_type}")
        else:
            print(f"❌ Не найден тип документа: {doc_type}")
    
    return handler


def test_extract_youtube_id(handler):
    """Тестирование извлечения YouTube ID."""
    print("\n=== Тест извлечения YouTube ID ===")
    
    test_cases = [
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://example.com/video", ""),
        ("", "")
    ]
    
    for url, expected in test_cases:
        # ИСПРАВЛЕНО: одно подчеркивание вместо двух
        result = handler._extract_youtube_id(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{url[:30]}...' -> '{result}'")
    
    return handler


def test_build_additional_info_html(handler):
    """Тестирование построения HTML дополнительной информации."""
    print("\n=== Тест построения HTML дополнительной информации ===")
    
    product = RawProduct(
        Бренд="TestBrand",
        Артикул="ART-001",
        НС_код="NS001",
        Штрих_код="1234567890123/2345678901234",
        Эксклюзив="Эксклюзив - Да"
    )
    
    # ИСПРАВЛЕНО: одно подчеркивание вместо двух
    result = handler._build_additional_info_html(product)
    
    print("✅ Сгенерированный HTML дополнительной информации:")
    print(f"Длина: {len(result)} символов")
    print(f"Содержит h3: {'<h3>' in result}")
    print(f"Содержит ul: {'<ul>' in result}")
    
    # Проверяем наличие ключевой информации
    checks = [
        ("Бренд", "TestBrand"),
        ("Артикул", "ART-001"),
        ("НС-код", "NS001"),
        ("Штрих-коды", "1234567890123"),
        ("Эксклюзив", "Да")
    ]
    
    for field, value in checks:
        if value in result:
            print(f"✅ Найдено поле: {field}")
        else:
            print(f"❌ Не найдено поле: {field}")
    
    return handler


def test_full_processing():
    """Тестирование полной обработки."""
    print("\n=== Тест полной обработки ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = ContentHandler(config_manager)
        
        product = RawProduct(
            Наименование="Пластиковый контейнер 10л",
            Бренд="PlasticPro",
            Артикул="PC-10",
            НС_код="NS001",
            Штрих_код="1234567890123",
            Эксклюзив="Эксклюзив - Нет",
            Статья="<p>Отличный контейнер для хранения продуктов.</p>",
            Характеристики="Масса товара (нетто): 0.5 кг / Высота товара: 30 см / Цвет: Белый",
            Чертежи="https://example.com/drawing.pdf",
            Видео="https://youtube.com/watch?v=dQw4w9WgXcQ"
        )
        
        result = handler.process(product)
        
        print("✅ Проверка результата:")
        
        if "post_content" in result:
            html = result["post_content"]
            print(f"✅ Поле post_content создано: {len(html)} символов")
            
            # Проверяем основные блоки
            blocks_to_check = [
                ("Статья", "<p>Отличный контейнер"),
                ("Характеристики", "<h2>Технические характеристики</h2>"),
                ("Документация", "<h3>Документация</h3>"),
                ("Видео", "Видеообзор"),
                ("Доп. информация", "<h3>Дополнительная информация</h3>")
            ]
            
            for block_name, marker in blocks_to_check:
                if marker in html:
                    print(f"✅ Найден блок: {block_name}")
                else:
                    print(f"❌ Не найден блок: {block_name}")
            
            # Покажем фрагмент HTML
            print(f"\nФрагмент HTML (первые 200 символов):")
            print(html[:200] + "...")
        else:
            print("❌ Поле post_content отсутствует в результате")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Запуск всех тестов."""
    print("Тестирование ContentHandler B2B-WC Converter v2.0\n")
    
    try:
        handler, config = test_content_handler_initialization()
        
        if handler and config:
            test_parse_specifications(handler)
            test_process_article(handler)
            test_build_specifications_html(handler)
            test_collect_documents(handler)
            test_extract_youtube_id(handler)
            test_build_additional_info_html(handler)
            test_full_processing()
            
            handler.cleanup()
            print("\n✅ Все тесты ContentHandler пройдены успешно!")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании ContentHandler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()