"""
Тест для DocsParser
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.docs_parser import DocsParser


def test_docs_parser():
    """Тестирование парсера документов"""
    print("🧪 Тестирование DocsParser...")
    
    # Создаем парсер
    parser = DocsParser()
    
    # Тестовые данные
    test_certificates = "https://rkcdn.ru/products/f270e725-92dc-11f0-b8e1-00505601218a/src.pdf,https://rkcdn.ru/products/99538d8d-92dd-11f0-b8e1-00505601218a/src.pdf"
    test_manuals = "https://rkcdn.ru/products/2d72fa9c-129d-11ef-b8d8-00505601218a/src.pdf"
    test_video = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    product_name = "Обогреватель инфракрасный Ballu BIH-GSW-1.0"
    product_type = "Тепловое оборудование"
    
    # Тест 1: Все документы
    print("\n1. Тест обработки всех документов:")
    result = parser.parse_all_documents(
        certificates=test_certificates,
        manuals=test_manuals,
        videos=test_video,
        product_name=product_name,
        product_type=product_type
    )
    
    print(f"   Успех: {result.success}")
    print(f"   Всего ссылок: {result.data['total_links']}")
    print(f"   Есть документы: {result.data['has_documents']}")
    
    # Сохраняем HTML для просмотра
    with open("test_docs_output.html", "w", encoding="utf-8") as f:
        f.write(result.data['full_html'])
    print("   HTML сохранен в test_docs_output.html")
    
    # Тест 2: Одна колонка (сертификаты)
    print("\n2. Тест одной колонки (Сертификаты):")
    result2 = parser.parse_single_column(
        doc_string=test_certificates,
        column_name="Сертификаты",
        product_name=product_name,
        product_type=product_type
    )
    
    print(f"   Успех: {result2.success}")
    print(f"   Найдено URL: {len(result2.data['urls'])}")
    print(f"   Тип документа: {result2.data['doc_type']}")
    
    # Тест 3: Извлечение YouTube ID
    print("\n3. Тест извлечения YouTube ID:")
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://example.com/not-youtube"
    ]
    
    for url in test_urls:
        video_id = parser._extract_youtube_id(url)
        print(f"   {url} -> {video_id}")
    
    # Тест 4: Пустые документы
    print("\n4. Тест с пустыми документами:")
    result3 = parser.parse_all_documents(
        product_name=product_name,
        product_type=product_type
    )
    
    print(f"   Успех: {result3.success}")
    print(f"   Есть документы: {result3.data['has_documents']}")
    print(f"   Предупреждения: {result3.warnings}")
    
    print("\n✅ Все тесты завершены!")
    return True


if __name__ == "__main__":
    success = test_docs_parser()
    sys.exit(0 if success else 1)