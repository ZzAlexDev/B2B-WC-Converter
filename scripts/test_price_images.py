#!/usr/bin/env python3
"""
Тестовый скрипт для проверки парсеров цены и изображений
"""

import sys
import os

# Добавляем src в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.price_parser import PriceParser
from src.parsers.images_parser import ImagesParser
from src.utils.logger import setup_logger


def test_price_parser():
    """Тестирование парсера цены"""
    print("=" * 60)
    print("ТЕСТ ПАРСЕРА ЦЕНЫ")
    print("=" * 60)
    
    parser = PriceParser(currency="RUB")
    
    test_cases = [
        ("1 190,00", 1190.00),
        ("2 500,00", 2500.00),
        ("46 990,00", 46990.00),
        ("99 990,00", 99990.00),
        ("1190.00", 1190.00),
        ("2500", 2500.00),
        ("0", 0.00),
        ("", 0.00),  # Пусто
        ("бесплатно", 0.00),  # Не число
        ("1 190.50", 1190.50),  # Точка как десятичный разделитель
        ("1,190.00", 1190.00),  # Запятая как разделитель тысяч
        ("1 190 000,50", 1190000.50),  # Большое число
    ]
    
    all_passed = True
    
    for i, (input_price, expected) in enumerate(test_cases, 1):
        print(f"\nТест {i}: '{input_price}' → ожидается: {expected}")
        
        result = parser.parse(input_price)
        
        if result.success:
            actual = result.data["price"]
            status = "✅" if abs(actual - expected) < 0.01 else "❌"
            
            if abs(actual - expected) < 0.01:
                print(f"  {status} Получено: {actual}")
                print(f"     Форматировано: {result.data['price_formatted']}")
                print(f"     Валюта: {result.data['currency']}")
                print(f"     Копейки: {result.data['has_cents']}")
            else:
                print(f"  {status} Ошибка: получено {actual}, ожидалось {expected}")
                all_passed = False
            
            if result.warnings:
                print(f"     ⚠️ Предупреждения: {result.warnings}")
        else:
            print(f"  ❌ Ошибки: {result.errors}")
            # Для пустой строки или нечисловых значений ошибки ожидаемы
            if input_price in ["", "бесплатно"]:
                print(f"     (ожидаемая ошибка для '{input_price}')")
            else:
                all_passed = False
        
        parser.log_parse_result(result, row_index=i)
    
    # Дополнительный тест: извлечение цены из текста
    print(f"\n{'─'*40}")
    print("Тест извлечения цены из текста:")
    
    text_cases = [
        ("Цена: 1 190,00 руб.", 1190.00),
        ("Стоимость 2 500.00", 2500.00),
        ("Всего 46 990,00", 46990.00),
        ("Цена со скидкой 99 990,00", 99990.00),
        ("Бесплатно", None),
        ("Цена не указана", None),
    ]
    
    for text, expected in text_cases:
        actual = parser.extract_price_from_text(text)
        status = "✅" if actual == expected else "❌"
        
        if actual == expected:
            print(f"  {status} '{text}' → {actual}")
        else:
            print(f"  {status} '{text}' → {actual} (ожидалось: {expected})")
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ЦЕНЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ЦЕНЫ НЕ ПРОЙДЕНЫ")
    print("=" * 60)
    
    return all_passed


def test_images_parser():
    """Тестирование парсера изображений"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПАРСЕРА ИЗОБРАЖЕНИЙ")
    print("=" * 60)
    
    # Тестируем без скачивания (skip_download=True)
    parser = ImagesParser(
        download_path="data/downloads/images/test",
        max_images=3,
        skip_download=True  # Не скачиваем, только обрабатываем URL
    )
    
    test_cases = [
        # (URLs, SKU, Slug, Category, Product Name)
        (
            "https://example.com/image1.jpg,https://example.com/image2.jpg,https://example.com/image3.jpg",
            "НС-1132314",
            "mini-teploventilyator-ballu-bfh-s-03n",
            ["Тепловое", "Бытовые", "Тепловентиляторы"],
            "Мини-тепловентилятор Ballu BFH/S-03N"
        ),
        (
            "https://rkcdn.ru/products/fce51254-8106-11ed-b732-005056013a69/src.jpg,https://rkcdn.ru/products/57136c02-d7d0-11ea-9da0-ac162d7b6f40/src.jpg",
            "НС-1659333",
            "konvektor-elektricheskiy-ballu-ip-54-bec-cmr-2000",
            ["Тепловое", "Промышленные", "Конвекторы"],
            "Конвектор электрический Ballu IP 54 BEC/CMR-2000"
        ),
        (
            "",  # Пустые изображения
            "НС-999999",
            "test-product",
            ["Тест", "Категория"],
            "Тестовый товар"
        ),
        (
            "not-a-url,http://invalid.com/image.txt",  # Невалидные URL
            "НС-888888",
            "invalid-product",
            ["Тест"],
            "Товар с невалидными изображениями"
        ),
    ]
    
    all_passed = True
    
    for i, (urls, sku, slug, category, product_name) in enumerate(test_cases, 1):
        print(f"\nТест {i}:")
        print(f"  SKU: {sku}, Товар: {product_name}")
        print(f"  URL: {urls[:50]}..." if len(urls) > 50 else f"  URL: {urls}")
        
        result = parser.parse(urls, sku, slug, category, product_name)
        
        if result.success or (not urls and result.warnings):  # Пустые URL - это warning, не error
            print(f"  ✅ Успешно обработано")
            data = result.data
            
            print(f"     Найдено URL: {len(data['urls'])}")
            print(f"     Успешно: {data['success_count']}")
            print(f"     Ошибок: {data['failed_count']}")
            
            if data['success_count'] > 0:
                print(f"     Главное изображение: {data['main_image']}")
                print(f"     Галерея: {len(data['gallery_images'])} изображений")
                
                # Показываем сгенерированные имена файлов
                if data['local_paths']:
                    print(f"     Имена файлов:")
                    for path in data['local_paths'][:2]:  # Первые 2
                        filename = os.path.basename(path)
                        print(f"       - {filename}")
                    if len(data['local_paths']) > 2:
                        print(f"       ... и еще {len(data['local_paths']) - 2}")
            
            print(f"     Путь категории: {data['category_path']}")
            
            if result.warnings:
                print(f"     ⚠️ Предупреждения: {result.warnings}")
            
            # Проверяем формат WC
            if data['wc_format']:
                print(f"     Формат WC (первые 100 символов): {data['wc_format'][:100]}...")
            
        else:
            print(f"  ❌ Ошибки: {result.errors}")
            # Для невалидных URL ошибки ожидаемы
            if "not-a-url" in urls:
                print(f"     (ожидаемая ошибка для невалидных URL)")
            else:
                all_passed = False
        
        parser.log_parse_result(result, row_index=i)
    
    # Тест генерации имени файла
    print(f"\n{'─'*40}")
    print("Тест генерации имен файлов:")
    
    filename_tests = [
        ("НС-1132314", "mini-teploventilyator", 1, ".jpg", "нс-1132314-mini-teploventilyator-1.jpg"),
        ("ART/001", "product-name", 2, ".png", "art_001-product-name-2.png"),
        ("LONG-SKU-1234567890", "very-long-product-name-with-many-words", 3, ".jpeg", "long-sku-1234567890-very-long-product-name-with-many-words-3.jpeg"),
    ]
    
    for sku, slug, index, ext, expected in filename_tests:
        actual = parser._generate_filename(sku, slug, index, ext)
        status = "✅" if actual == expected else "❌"
        
        if actual == expected:
            print(f"  {status} {sku}, {slug} → {actual}")
        else:
            print(f"  {status} {sku}, {slug} → {actual} (ожидалось: {expected})")
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ИЗОБРАЖЕНИЙ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ИЗОБРАЖЕНИЙ НЕ ПРОЙДЕНЫ")
    print("=" * 60)
    
    return all_passed


def main():
    """Основная функция тестирования"""
    
    # Настраиваем логгер
    setup_logger(log_level="INFO", console_output=True)
    
    print("НАЧАЛО ТЕСТИРОВАНИЯ ПАРСЕРОВ ЦЕНЫ И ИЗОБРАЖЕНИЙ")
    print()
    
    # Запускаем тесты
    price_passed = test_price_parser()
    images_passed = test_images_parser()
    
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 60)
    print(f"✅ Парсер цены: {'ПРОЙДЕН' if price_passed else 'НЕ ПРОЙДЕН'}")
    print(f"✅ Парсер изображений: {'ПРОЙДЕН' if images_passed else 'НЕ ПРОЙДЕН'}")
    
    all_passed = price_passed and images_passed
    
    if all_passed:
        print(f"\n🎉 ВСЕ ТЕСТЫ ЭТАПА 6 ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    
    print("=" * 60)


if __name__ == "__main__":
    main()