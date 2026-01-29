#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузчика XLSX
"""

import sys
import os

# Добавляем src в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.loaders.xlsx_loader import XLSXLoader, load_and_validate_xlsx
from src.utils.logger import setup_logger


def main():
    """Основная функция тестирования"""
    
    # Настраиваем логгер
    logger = setup_logger(log_level="DEBUG", console_output=True)
    
    # Путь к тестовому файлу
    test_file = r"data\input\test-in-03.xlsx"
    
    print("=" * 60)
    print("ТЕСТ ЗАГРУЗЧИКА XLSX")
    print("=" * 60)
    
    # Проверяем существование файла
    if not os.path.exists(test_file):
        print(f"❌ Файл не найден: {test_file}")
        print(f"   Убедитесь что файл существует по указанному пути")
        return
    
    print(f"📁 Тестовый файл: {test_file}")
    print()
    
    # Тест 1: Быстрая загрузка
    print("1. Тестируем быструю загрузку...")
    result = load_and_validate_xlsx(test_file)
    
    if result is None:
        print("❌ Ошибка при загрузке файла")
        return
    
    print(f"✅ Файл загружен успешно!")
    print(f"   Товаров: {result['total_products']}")
    print(f"   Пачек: {result['analysis']['batches_count']}")
    print()
    
    # Тест 2: Детальный анализ
    print("2. Детальный анализ данных...")
    loader = XLSXLoader()
    df = loader.load_file(test_file)
    
    if df is not None:
        is_valid, messages = loader.validate_structure(df)
        
        print(f"✅ Структура файла: {'ВАЛИДНА' if is_valid else 'НЕВАЛИДНА'}")
        
        if messages:
            print("   Сообщения:")
            for msg in messages:
                print(f"   - {msg}")
        
        print()
        
        # Показываем первые 3 строки для проверки
        print("3. Пример данных (первые 10 строки):")
        print("-" * 40)
        
        # Выбираем ключевые колонки для показа
        key_columns = ["Наименование", "Артикул", "Цена", "НС-код", "Бренд"]
        available_columns = [col for col in key_columns if col in df.columns]
        
        if available_columns:
            sample = df[available_columns].head(10)
            
            # Красиво выводим
            for idx, row in sample.iterrows():
                print(f"Строка {idx + 1}:")
                for col in available_columns:
                    value = str(row[col])[:50]  # Обрезаем длинные значения
                    if len(str(row[col])) > 50:
                        value += "..."
                    print(f"  {col}: {value}")
                print("-" * 30)
        else:
            print("   Нет ключевых колонок для отображения")
        
        print()
        
        # Анализ данных
        print("4. Статистика по колонкам:")
        print("-" * 40)
        
        analysis = loader.analyze_data(df)
        
        for col, info in analysis["columns_info"].items():
            if col in ["Наименование", "Артикул", "Цена", "НС-код", "Бренд", "Характеристики"]:
                percent = info["null_percent"]
                status = "✅" if percent == 0 else f"⚠️ {percent:.1f}% пустых"
                print(f"  {col}: {status} (пример: {info['sample_values'][:1]})")
        
        print()
        print("=" * 60)
        print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        print("=" * 60)
        
    else:
        print("❌ Не удалось загрузить DataFrame")


if __name__ == "__main__":
    main()