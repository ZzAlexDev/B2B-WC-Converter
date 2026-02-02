#!/usr/bin/env python3
"""Тестирование TextCleaner прямо в папке handlers."""
import sys
import os

# Для запуска из папки handlers
if __name__ == "__main__":
    # Добавляем родительскую папку в путь
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.v2.handlers.text_cleaner import TextCleaner
    
    # Тестовые данные
    test_cases = [
        ("Текст с&nbsp;пробелами", "Текст с пробелами"),
        ("Текст\xa0с\xa0пробелами", "Текст с пробелами"),
        ("<p>HTML&nbsp;текст</p>", "HTML текст"),
    ]
    
    cleaner = TextCleaner()
    print("🧪 Тестируем TextCleaner...")
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = cleaner.clean_text(input_text)
        if result == expected:
            print(f"✅ Тест {i}: OK")
        else:
            print(f"❌ Тест {i}: FAIL")
            print(f"   Вход: '{input_text}'")
            print(f"   Результат: '{result}'")
            print(f"   Ожидалось: '{expected}'")