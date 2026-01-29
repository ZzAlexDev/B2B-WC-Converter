"""
test_fixes_simple.py
Упрощенный тест для проверки исправлений
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processors.attribute_parser import AttributeParser
from data_processors.description_builder import DescriptionBuilder

# Отключаем логирование для чистого вывода
import logging
logging.getLogger().setLevel(logging.ERROR)


def test_attribute_normalization():
    """Тест нормализации значений атрибутов"""
    print("\n=== ТЕСТ: Нормализация значений атрибутов ===")
    
    parser = AttributeParser()
    
    test_cases = [
        ("3 года", "3"),
        ("0.1 кВт", "0.1"),
        ("0.29 кг", "0.29"),
        ("14.8 см", "14.8"),
        ("8.6 см", "8.6"),
        ("9.1 см", "9.1"),
        ("10 лет", "10"),
        ("Да", "yes"),
        ("Нет", "no"),
        ("IP24", "IP24"),
        ("Механический", "Механический"),
        ("КНР", "КНР"),
    ]
    
    passed = 0
    for input_val, expected in test_cases:
        result = parser.normalize_value_for_wc(input_val)
        if str(result) == str(expected):
            print(f"✓ '{input_val}' -> '{result}'")
            passed += 1
        else:
            print(f"✗ '{input_val}' -> '{result}' (ожидалось: '{expected}')")
    
    print(f"\nУспешно: {passed}/{len(test_cases)}")


def test_html_anchors():
    """Тест добавления якорей в HTML"""
    print("\n=== ТЕСТ: Якоря в HTML описании ===")
    
    builder = DescriptionBuilder()
    
    # Тестовые данные
    test_product = {
        'name': 'Тестовый товар',
        'characteristics_raw': 'Цвет: Белый; Мощность: 2 кВт',
        'description_raw': '<p>Описание товара</p>',
        'documents': {},
        'additional_info': {}
    }
    
    result = builder.build_full_description(test_product)
    html = result.get('post_content', '')
    excerpt = result.get('post_excerpt', '')
    
    checks = [
        ('Якорь характеристик', 'id="product-characteristics"', html),
        ('Ссылка в excerpt', '#product-characteristics', excerpt),
        ('Класс WC атрибутов', 'class="wc-attribute"', html),
        ('Заголовок характеристик', '<h3>Технические характеристики</h3>', html),
    ]
    
    passed = 0
    for name, search_text, content in checks:
        if search_text in content:
            print(f"✓ {name} найден")
            passed += 1
        else:
            print(f"✗ {name} не найден")
            print(f"  Искали: '{search_text}'")
            print(f"  В контенте: ...{content[100:200]}..." if len(content) > 200 else f"  Контент: {content}")
    
    print(f"\nУспешно: {passed}/{len(checks)}")


def main():
    """Основной тест"""
    print("ПРОВЕРКА ИСПРАВЛЕНИЙ")
    print("=" * 50)
    
    test_attribute_normalization()
    test_html_anchors()
    
    print("\n" + "=" * 50)
    print("Запустите полный тест после исправлений:")
    print("python test_full_pipeline_real_data.py")


if __name__ == "__main__":
    main()