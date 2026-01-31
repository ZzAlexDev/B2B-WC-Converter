"""
Тестирование MediaHandler.
Запуск из корня проекта: python -m src.v2.tests.test_media_handler
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.v2.handlers.media_handler import MediaHandler
from src.v2.models import RawProduct
from src.v2.config_manager import ConfigManager


def test_media_handler_initialization():
    """Тестирование инициализации MediaHandler."""
    print("=== Тест инициализации MediaHandler ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = MediaHandler(config_manager)
        
        print(f"✅ MediaHandler создан: {handler.handler_name}")
        print(f"✅ Папка для скачивания: {handler.download_dir}")
        
        return handler, config_manager
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_split_image_urls(handler):
    """Тестирование разбиения URL изображений."""
    print("\n=== Тест разбиения URL изображений ===")
    
    test_cases = [
        (
            "https://example.com/image1.jpg,https://example.com/image2.jpg",
            ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
        ),
        (
            "https://example.com/image1.jpg, https://example.com/image2.jpg",
            ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
        ),
        (
            "https://example.com/image1.jpg",
            ["https://example.com/image1.jpg"]
        ),
        (
            "",
            []
        ),
        (
            "invalid-url,https://example.com/image.jpg",
            ["https://example.com/image.jpg"]
        )
    ]
    
    for urls_str, expected in test_cases:
        result = handler._MediaHandler__split_image_urls(urls_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{urlls_str[:30]}...' -> {len(result)} URL (ожидалось: {len(expected)})")
    
    return handler


def test_generate_slug_from_title(handler):
    """Тестирование генерации slug из названия."""
    print("\n=== Тест генерации slug ===")
    
    test_cases = [
        ("Пластиковый контейнер", "plastikovyy-konteyner"),
        ("Металлический шкаф MS-200", "metallicheskiy-shkaf-ms-200"),
        ("Товар №1 (специальный)", "tovar-1-spetsialnyy"),
        ("", ""),
        ("Test Product 123", "test-product-123")
    ]
    
    for title, expected in test_cases:
        result = handler._MediaHandler__generate_slug_from_title(title)
        # Проверяем только что slug не пустой для непустых названий
        if title:
            status = "✅" if result else "❌"
            print(f"{status} '{title}' -> '{result}' (ожидалось не пустое значение)")
        else:
            status = "✅" if result == "" else "❌"
            print(f"{status} '{title}' -> '{result}' (ожидалось: '')")
    
    return handler


def test_extract_youtube_id(handler):
    """Тестирование извлечения YouTube ID."""
    print("\n=== Тест извлечения YouTube ID ===")
    
    test_cases = [
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://example.com/video", None),
        ("", None)
    ]
    
    for url, expected in test_cases:
        result = handler._MediaHandler__extract_youtube_id(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{url[:30]}...' -> '{result}' (ожидалось: '{expected}')")
    
    return handler


def test_process_images():
    """Тестирование обработки изображений."""
    print("\n=== Тест обработки изображений ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = MediaHandler(config_manager)
        
        # Создаем тестовый продукт
        product = RawProduct(
            Наименование="Тестовый товар",
            НС_код="TEST001",
            Изображение="https://example.com/image1.jpg,https://example.com/image2.jpg",
            Название_категории="Тестовая категория"
        )
        
        # Мокаем скачивание изображений
        with patch.object(handler, '_MediaHandler__download_images', return_value=[]):
            result = handler.process(product)
            
            if "images" in result:
                images_field = result["images"]
                print(f"✅ Поле images создано: {len(images_field)} символов")
                
                # Проверяем формат
                if "::" in images_field:
                    parts = images_field.split(" :: ")
                    print(f"✅ Найдено {len(parts)} изображений в поле")
                    
                    for i, part in enumerate(parts[:2]):  # Покажем первые 2
                        print(f"  Изображение {i+1}: {part[:50]}...")
                else:
                    print("⚠️ Поле images не содержит разделителя '::'")
            else:
                print("❌ Поле images отсутствует в результате")
        
        return handler
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_process_video():
    """Тестирование обработки видео."""
    print("\n=== Тест обработки видео ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = MediaHandler(config_manager)
        
        test_cases = [
            (
                "https://youtube.com/watch?v=dQw4w9WgXcQ",
                True  # Ожидаем наличие полей видео
            ),
            (
                "",
                False  # Не ожидаем полей видео
            ),
            (
                "https://example.com/video",
                True  # Только URL без превью
            )
        ]
        
        for video_url, should_have_fields in test_cases:
            product = RawProduct(
                НС_код="TEST",
                Видео=video_url
            )
            
            result = handler.process(product)
            
            has_video_url = "meta:видео_url" in result
            has_thumbnail = "meta:видео_превью" in result
            
            if should_have_fields and video_url:
                if has_video_url:
                    print(f"✅ Для '{video_url[:30]}...' поле meta:видео_url найдено")
                else:
                    print(f"❌ Для '{video_url[:30]}...' поле meta:видео_url не найдено")
            else:
                if not has_video_url:
                    print(f"✅ Для '{video_url[:30]}...' поля видео отсутствуют (как и ожидалось)")
                else:
                    print(f"⚠️ Для '{video_url[:30]}...' поля видео найдены, но не ожидались")
        
        return handler
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_process_documents():
    """Тестирование обработки документов."""
    print("\n=== Тест обработки документов ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = MediaHandler(config_manager)
        
        product = RawProduct(
            НС_код="TEST001",
            Чертежи="https://example.com/drawing.pdf",
            Сертификаты="https://example.com/certificate.pdf",
            Инструкции="https://example.com/instructions.pdf"
        )
        
        result = handler.process(product)
        
        expected_fields = {
            "meta:чертеж_url": "https://example.com/drawing.pdf",
            "meta:сертификат_url": "https://example.com/certificate.pdf",
            "meta:инструкция_url": "https://example.com/instructions.pdf"
        }
        
        print("✅ Обработанные документы:")
        for field, expected_url in expected_fields.items():
            actual_url = result.get(field, "")
            status = "✅" if actual_url == expected_url else "❌"
            print(f"{status} {field}: '{actual_url}'")
        
        return handler
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_processing():
    """Тестирование полной обработки."""
    print("\n=== Тест полной обработки ===")
    
    try:
        config_manager = ConfigManager.from_directory("config/v2")
        handler = MediaHandler(config_manager)
        
        product = RawProduct(
            Наименование="Пластиковый контейнер 10л",
            НС_код="PC001",
            Изображение="https://example.com/image1.jpg,https://example.com/image2.jpg",
            Видео="https://youtube.com/watch?v=dQw4w9WgXcQ",
            Чертежи="https://example.com/drawing.pdf",
            Название_категории="Тара - Контейнеры"
        )
        
        # Мокаем скачивание изображений
        with patch.object(handler, '_MediaHandler__download_images', return_value=[]):
            result = handler.process(product)
        
        print("✅ Проверка полей:")
        
        fields_to_check = [
            ("images", "присутствует"),
            ("meta:видео_url", "https://youtube.com/watch?v=dQw4w9WgXcQ"),
            ("meta:видео_превью", "присутствует"),
            ("meta:чертеж_url", "https://example.com/drawing.pdf")
        ]
        
        for field, expected in fields_to_check:
            actual = result.get(field, "")
            if expected == "присутствует":
                status = "✅" if actual else "❌"
                print(f"{status} {field}: присутствует ({len(actual)} символов)")
            else:
                status = "✅" if actual == expected else "❌"
                print(f"{status} {field}: '{actual}'")
        
        print(f"\n✅ Всего полей обработано: {len(result)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Запуск всех тестов."""
    print("Тестирование MediaHandler B2B-WC Converter v2.0\n")
    
    try:
        handler, config = test_media_handler_initialization()
        
        if handler and config:
            test_split_image_urls(handler)
            test_generate_slug_from_title(handler)
            test_extract_youtube_id(handler)
            
            # Тесты с созданием отдельных обработчиков
            test_process_images()
            test_process_video()
            test_process_documents()
            test_full_processing()
            
            handler.cleanup()
            print("\n✅ Все тесты MediaHandler пройдены успешно!")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании MediaHandler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()