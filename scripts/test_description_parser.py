"""
Тест для DescriptionParser
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.description_parser import DescriptionParser


def test_description_parser():
    """Тестирование парсера описания"""
    print("🧪 Тестирование DescriptionParser...")
    
    # Создаем парсер
    parser = DescriptionParser()
    
    # Тест 1: Только статья
    print("\n1. Тест с HTML статьей:")
    article_html = "<p>Это тестовое описание товара.</p><p>Второй абзац.</p>"
    result = parser.parse(article_html=article_html, product_name="Тестовый товар")
    
    print(f"   Успех: {result.success}")
    print(f"   Длина HTML: {len(result.data['html'])}")
    print(f"   Есть статья: {result.data['has_article']}")
    
    # Тест 2: Статья + характеристики
    print("\n2. Тест со статьей и характеристиками:")
    specs_html = "<h2>Характеристики</h2><ul><li>Цвет: Черный</li></ul>"
    result2 = parser.parse(
        article_html=article_html,
        specs_html=specs_html,
        product_name="Тестовый товар 2"
    )
    
    print(f"   Успех: {result2.success}")
    print(f"   Частей: {result2.data['parts_count']}")
    
    # Тест 3: С видео (YouTube)
    print("\n3. Тест с видео YouTube:")
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result3 = parser.parse(
        article_html=article_html,
        video_url=video_url,
        product_name="Товар с видео"
    )
    
    print(f"   Успех: {result3.success}")
    print(f"   Есть видео: {result3.data['has_video']}")
    
    # Тест 4: Короткое описание
    print("\n4. Тест создания короткого описания:")
    short_desc = parser.create_short_description(article_html, max_length=50)
    print(f"   Короткое описание: '{short_desc}'")
    
    # Тест 5: Извлечение YouTube ID
    print("\n5. Тест извлечения YouTube ID:")
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://example.com/not-youtube"
    ]
    
    for url in test_urls:
        video_id = parser._extract_youtube_id(url)
        print(f"   {url} -> {video_id}")
    
    print("\n✅ Все тесты завершены!")
    return True


if __name__ == "__main__":
    success = test_description_parser()
    sys.exit(0 if success else 1)