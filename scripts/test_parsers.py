#!/usr/bin/env python3
"""
Тестовый скрипт для проверки парсеров
"""

import sys
import os

# Добавляем src в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.name_parser import NameParser
from src.parsers.sku_parser import SKUParser
from src.parsers.brand_parser import BrandParser
from src.parsers.category_parser import CategoryParser
from src.utils.logger import setup_logger


def test_name_parser():
    """Тестирование парсера наименования"""
    print("=" * 60)
    print("ТЕСТ ПАРСЕРА НАИМЕНОВАНИЯ")
    print("=" * 60)
    
    parser = NameParser()
    
    test_cases = [
        "Мини-тепловентилятор Ballu BFH/S-03N",
        "Конвектор электрический Ballu IP 54 BEC/CMR-2000",
        "Завеса воздушная Ballu BHC-U15A-PS",
        "Камин уличный газовый инфракрасный Ballu BOGH-15E",
        "Тестовый товар <script>alert('xss')</script>",
        "",
        "   Товар   с   лишними   пробелами   "
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nТест {i}: '{test_case}'")
        result = parser.parse(test_case)
        
        if result.success:
            print(f"  ✅ Успех!")
            print(f"     Название: {result.data['name']}")
            print(f"     Slug: {result.data['slug']}")
            print(f"     Ключевые слова: {result.data['keywords'][:5]}")
            
            if result.warnings:
                print(f"     ⚠️ Предупреждения: {result.warnings}")
        else:
            print(f"  ❌ Ошибки: {result.errors}")
        
        parser.log_parse_result(result, row_index=i)


def test_sku_parser():
    """Тестирование парсера SKU"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПАРСЕРА SKU")
    print("=" * 60)
    
    parser = SKUParser(use_ns_code_as_sku=True)
    
    test_cases = [
        ("BFH/S-03N", "НС-1132314"),
        ("BEC/CMR-2000", "НС-1659333"),
        ("BHC-U15A-PS", "НС-1183726"),
        ("", "НС-1119542"),  # Нет артикула
        ("ART-001", ""),     # Нет НС-кода
        ("", ""),           # Пусто
        ("Спец/символы!", "НС-123"),
    ]
    
    for i, (article, ns_code) in enumerate(test_cases, 1):
        print(f"\nТест {i}: Артикул='{article}', НС-код='{ns_code}'")
        result = parser.parse(article, ns_code)
        
        if result.success:
            print(f"  ✅ Успех!")
            print(f"     SKU: {result.data['sku']}")
            print(f"     Артикул: {result.data['article']}")
            print(f"     НС-код: {result.data['ns_code']}")
            print(f"     Основной: {'НС-код' if result.data['is_ns_code_primary'] else 'Артикул'}")
            
            if result.warnings:
                print(f"     ⚠️ Предупреждения: {result.warnings}")
        else:
            print(f"  ❌ Ошибки: {result.errors}")
        
        parser.log_parse_result(result, row_index=i)


def test_brand_parser():
    """Тестирование парсера бренда"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПАРСЕРА БРЕНДА")
    print("=" * 60)
    
    parser = BrandParser()
    
    test_cases = [
        ("Ballu", "Мини-тепловентилятор Ballu BFH/S-03N"),
        ("ballu", "Конвектор электрический"),
        ("SHUFT", "Радиатор SHUFT Aluminium 500"),  # ← НОВЫЙ ТЕСТ
        ("shuft", "Радиатор алюминиевый"),  # ← НОВЫЙ ТЕСТ
        ("Royal Thermo", "Радиатор Royal Thermo BiLiner 500"),  # ← НОВЫЙ ТЕСТ
        ("royal thermo", "Радиатор билинер"),  # ← НОВЫЙ ТЕСТ
        ("", "Тепловентилятор Timberk TOR 2.0"),  # Бренд из названия
        ("БАЛУ", "Тестовый товар"),  # Нормализация
        ("", "Товар без бренда"),  # Без бренда
        ("VeryLongBrandNameThatIsTooLongForNormalUse", "Тест"),
    ]

    
    for i, (brand, product_name) in enumerate(test_cases, 1):
        print(f"\nТест {i}: Бренд='{brand}', Товар='{product_name}'")
        result = parser.parse(brand, product_name)
        
        if result.success:
            print(f"  ✅ Успех!")
            print(f"     Бренд: {result.data['brand']}")
            print(f"     Оригинал: {result.data['original_brand']}")
            print(f"     Из названия: {result.data['extracted_from_name']}")
            print(f"     Slug: {result.data['slug']}")
            
            if result.warnings:
                print(f"     ⚠️ Предупреждения: {result.warnings}")
        else:
            print(f"  ❌ Ошибки: {result.errors}")
        
        parser.log_parse_result(result, row_index=i)



def test_category_parser():
    """Тестирование парсера категории"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПАРСЕРА КАТЕГОРИИ")
    print("=" * 60)
    
    parser = CategoryParser()
    
    test_cases = [
        "Тепловое оборудование - Бытовые электрические обогреватели - Тепловентиляторы",
        "Тепловое оборудование – Бытовые – Тепловентиляторы",  # Другой дефис
        "Тепловое > Промышленные > Конвекторы",  # Разделитель >
        "Тепловое  -  Бытовые  -  Тепловентиляторы",  # Лишние пробелы
        "Категория - Категория - Подкатегория",  # Дубли
        "",  # Пусто
        "Только одна категория",
        "Очень - глубокая - вложенность - категорий - тест",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nТест {i}: '{test_case}'")
        result = parser.parse(test_case)
        
        if result.success:
            print(f"  ✅ Успех!")
            print(f"     Иерархия: {result.data['hierarchy']}")
            print(f"     WC формат: {result.data['wc_format']}")
            print(f"     Уровней: {result.data['level']}")
            print(f"     Основная: {result.data['main_category']}")
            
            if result.warnings:
                print(f"     ⚠️ Предупреждения: {result.warnings}")
            
            # Показываем объекты Category
            if result.data['categories']:
                print(f"     Объекты Category:")
                for cat in result.data['categories']:
                    print(f"       - {cat.name} (уровень {cat.level})")
        else:
            print(f"  ❌ Ошибки: {result.errors}")
        
        parser.log_parse_result(result, row_index=i)


def main():
    """Основная функция тестирования"""
    
    # Настраиваем логгер
    setup_logger(log_level="INFO", console_output=True)
    
    print("НАЧАЛО ТЕСТИРОВАНИЯ ПАРСЕРОВ")
    print()
    
    # Запускаем тесты
    test_name_parser()
    test_sku_parser()
    test_brand_parser()
    test_category_parser()
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)


if __name__ == "__main__":
    main()