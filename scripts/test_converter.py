"""
Тест для главного конвертера
"""

import sys
import os
import json
import tempfile
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.converter import B2BWCConverter, convert_xlsx_to_wc
from src.core.models.product import Product


def create_test_xlsx_file() -> str:
    """Создание тестового XLSX файла"""
    import pandas as pd
    import numpy as np
    
    # Создаем тестовые данные
    test_data = {
        "Наименование": ["Товар 1", "Товар 2", "Товар 3"],
        "Артикул": ["ART001", "ART002", "ART003"],
        "Бренд": ["Ballu", "Royal Thermo", "Timberk"],
        "Название категории": ["Категория 1", "Категория 1 > Подкатегория", "Категория 2"],
        "Характеристики": [
            "Цвет: Черный; Вес: 10 кг",
            "Цвет: Белый; Вес: 5 кг", 
            "Цвет: Серый; Вес: 8 кг"
        ],
        "Изображение": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            ""
        ],
        "Статья": [
            "<p>Описание товара 1</p>",
            "<p>Описание товара 2</p>",
            "<p>Описание товара 3</p>"
        ],
        "Штрих код": ["1234567890123", "2345678901234", "3456789012345"],
        "Цена": ["1000 руб.", "2000 руб.", "1500 руб."],
        "НС-код": ["NS-001", "NS-002", "NS-003"],
        "Эксклюзив": ["Нет", "Да", "Нет"]
    }
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
        test_file = tmp.name
    
    # Сохраняем в XLSX
    df = pd.DataFrame(test_data)
    df.to_excel(test_file, index=False)
    
    return test_file


def test_converter():
    """Тестирование главного конвертера"""
    print("🧪 Тестирование B2BWCConverter...")
    
    # Создаем временный XLSX файл
    test_xlsx = create_test_xlsx_file()
    output_dir = tempfile.mkdtemp()
    
    try:
        # Тест 1: Конвертация файла
        print("\n1. Конвертация тестового XLSX файла:")
        converter = B2BWCConverter()
        
        result = converter.convert_file(
            input_file=test_xlsx,
            output_dir=output_dir,
            skip_images_download=True,
            save_json_debug=True
        )
        
        print(f"   Успех: {'✅' if result.get('success') else '❌'}")
        print(f"   Обработано товаров: {result.get('products_processed', 0)}")
        print(f"   Успешных: {result.get('products_successful', 0)}")
        print(f"   Выходные файлы: {len(result.get('output_files', []))}")
        
        # Проверяем созданные файлы
        for file_path in result.get('output_files', []):
            if Path(file_path).exists():
                print(f"   📄 {Path(file_path).name} - существует")
            else:
                print(f"   ❌ {Path(file_path).name} - не найден")
        
        # Тест 2: Быстрая функция конвертации
        print("\n2. Тест быстрой функции convert_xlsx_to_wc:")
        test_csv = os.path.join(output_dir, "quick_test.csv")
        
        # Создаем несколько тестовых товаров для быстрой функции
        success = convert_xlsx_to_wc(
            input_file=test_xlsx,
            output_dir=output_dir,
            config_path="config/settings.json"
        )
        
        print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
        
        # Тест 3: Статистика
        print("\n3. Статистика работы конвертера:")
        stats = converter.get_stats()
        
        print(f"   Всего файлов: {stats.get('total_files', 0)}")
        print(f"   Всего товаров: {stats.get('total_products', 0)}")
        print(f"   Успешных товаров: {stats.get('successful_products', 0)}")
        print(f"   Успешность: {stats.get('success_rate', 0):.1f}%")
        
        # Тест 4: Проверка CSV файла
        print("\n4. Проверка созданного CSV файла:")
        csv_files = list(Path(output_dir).glob("*.csv"))
        
        if csv_files:
            csv_file = csv_files[0]
            
            # Читаем CSV
            import csv
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                print(f"   Файл: {csv_file.name}")
                print(f"   Строк: {len(rows)}")
                print(f"   Колонок: {len(reader.fieldnames) if reader.fieldnames else 0}")
                
                if rows:
                    print(f"   Первый товар: {rows[0].get('post_title', 'N/A')}")
        
        # Тест 5: Проверка JSON отчета
        print("\n5. Проверка JSON отчета:")
        json_files = list(Path(output_dir).glob("*.json"))
        
        if json_files:
            for json_file in json_files[:2]:  # Проверяем первые 2 JSON файла
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    
                    if 'conversion_report' in report:
                        print(f"   📋 {json_file.name}: {report['conversion_report'].get('success', False)}")
                    elif 'summary_report' in report:
                        print(f"   📊 {json_file.name}: сводный отчет")
                except:
                    print(f"   ❌ {json_file.name}: ошибка чтения")
        
        print("\n✅ Все тесты B2BWCConverter завершены!")
        return result.get('success', False)
        
    finally:
        # Очистка временных файлов
        try:
            if Path(test_xlsx).exists():
                Path(test_xlsx).unlink()
                print(f"\n🗑️  Удален временный XLSX файл")
            
            # Удаляем временную директорию
            import shutil
            if Path(output_dir).exists():
                shutil.rmtree(output_dir)
                print(f"🗑️  Удалена временная директория: {output_dir}")
                
        except Exception as e:
            print(f"⚠️  Ошибка при очистке: {e}")


if __name__ == "__main__":
    success = test_converter()
    sys.exit(0 if success else 1)