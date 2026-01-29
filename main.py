#!/usr/bin/env python3
"""
Главная точка входа B2B-WC Converter
Консольная утилита для конвертации каталогов товаров из XLSX в WooCommerce CSV
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Главная функция"""
    try:
        # Импортируем CLI приложение
        from interfaces.cli.cli_app import main as cli_main
        
        # Запускаем CLI
        cli_main()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(130)
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Проверьте установлены ли все зависимости:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()