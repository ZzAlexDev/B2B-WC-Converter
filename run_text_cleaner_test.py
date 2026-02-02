#!/usr/bin/env python3
"""
Простой тест TextCleaner.
Запускать из корня проекта: python run_text_cleaner_test.py
"""
import sys
import os

# Добавляем src/v2 в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src", "v2")
sys.path.insert(0, src_path)

try:
    from src.v2.handlers.text_cleaner import TextCleaner
    print("✅ TextCleaner успешно импортирован!")
    
    # Тестовые данные
    test_cases = [
        ("Текст с&nbsp;пробелами", "Текст с пробелами"),
        ("Текст\xa0с\xa0пробелами", "Текст с пробелами"),
        ("<p>HTML&nbsp;текст</p>", "HTML текст"),
        ("Много    пробелов   здесь", "Много пробелов здесь"),
        ("Текст «с кавычками»", 'Текст "с кавычками"'),
        ("Лишние  \t  табуляции", "Лишние табуляции"),
    ]
    
    cleaner = TextCleaner()
    print("\n🧪 Запускаем тесты TextCleaner...")
    print("-" * 50)
    
    all_passed = True
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = cleaner.clean_text(input_text)
        
        # Для отладки
        print(f"\nТест {i}:")
        print(f"  Вход:      '{input_text}'")
        print(f"  Ожидаем:   '{expected}'")
        print(f"  Получили:  '{result}'")
        
        if result == expected:
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL")
            all_passed = False
    
    print("-" * 50)
    if all_passed:
        print("🎉 Все тесты пройдены!")
    else:
        print("⚠️  Есть проблемы с очисткой текста")
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\nПроверьте структуру папок:")
    print(f"Текущая папка: {current_dir}")
    print(f"Ищем в: {src_path}")
    
    # Проверяем существование файла
    text_cleaner_path = os.path.join(src_path, "handlers", "text_cleaner.py")
    print(f"Файл существует: {os.path.exists(text_cleaner_path)}")
    
    if os.path.exists(text_cleaner_path):
        print("\nСодержимое handlers:")
        handlers_dir = os.path.join(src_path, "handlers")
        if os.path.exists(handlers_dir):
            for file in os.listdir(handlers_dir):
                print(f"  - {file}")
except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")