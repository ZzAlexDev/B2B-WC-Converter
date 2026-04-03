#!/usr/bin/env python3
"""
Скрипт для обработки изменений цен
Экспорт удаленных товаров: sku;regular_price (regular_price пустой)
"""

import argparse
import sys
import csv
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
DATA_INPUT = PROJECT_ROOT / "data" / "input"
DATA_OUTPUT = PROJECT_ROOT / "data" / "output"


def find_file(filename):
    """Ищет файл в папке input"""
    file_path = Path(filename)
    
    if file_path.exists():
        return file_path
    
    test_path = DATA_INPUT / file_path.name
    if test_path.exists():
        return test_path
    
    raise FileNotFoundError(f"Файл не найден: {filename}")


def read_csv_manual(file_path):
    """Принудительное чтение CSV файла с разделителем ;"""
    rows = []
    headers = None
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        csv_reader = csv.reader(f, delimiter=';', quotechar='"')
        
        for i, row in enumerate(csv_reader):
            if i == 0:
                headers = row
            else:
                if len(row) < len(headers):
                    row.extend([''] * (len(headers) - len(row)))
                elif len(row) > len(headers):
                    row = row[:len(headers)-1] + [' '.join(row[len(headers)-1:])]
                rows.append(row)
    
    data = []
    for row in rows:
        row_dict = {}
        for i, header in enumerate(headers):
            row_dict[header] = row[i] if i < len(row) else ''
        data.append(row_dict)
    
    return headers, data


def process_price_changes(old_file, new_file, output_prefix=None):
    """Основная функция обработки"""
    print(f"\n{'='*60}")
    print(f"ОБРАБОТКА ИЗМЕНЕНИЙ ПРАЙС-ЛИСТОВ")
    print(f"{'='*60}")
    
    # Находим файлы
    old_path = find_file(old_file)
    new_path = find_file(new_file)
    
    print(f"\n📁 Старый файл: {old_path.name}")
    print(f"📁 Новый файл: {new_path.name}")
    
    # Загружаем файлы
    print(f"\n📖 Загрузка файлов...")
    
    print(f"   Чтение старого файла...")
    old_headers, old_data = read_csv_manual(old_path)
    print(f"   Прочитано строк: {len(old_data)}")
    
    print(f"   Чтение нового файла...")
    new_headers, new_data = read_csv_manual(new_path)
    print(f"   Прочитано строк: {len(new_data)}")
    
    # Проверяем наличие поля НС-код
    if 'НС-код' not in old_headers:
        raise ValueError(f"В старом файле нет колонки 'НС-код'. Доступны: {old_headers}")
    
    if 'НС-код' not in new_headers:
        raise ValueError(f"В новом файле нет колонки 'НС-код'. Доступны: {new_headers}")
    
    # Собираем уникальные НС-коды
    old_skus = set()
    for row in old_data:
        sku = row.get('НС-код', '').strip()
        if sku and sku not in ['', 'nan', 'None', 'Эксклюзив - Нет', 'Эксклюзив - Да', 'Эксклюзив']:
            old_skus.add(sku)
    
    new_skus = set()
    new_skus_with_data = {}
    for row in new_data:
        sku = row.get('НС-код', '').strip()
        if sku and sku not in ['', 'nan', 'None', 'Эксклюзив - Нет', 'Эксклюзив - Да', 'Эксклюзив']:
            new_skus.add(sku)
            new_skus_with_data[sku] = row
    
    print(f"\n📊 Уникальные НС-код:")
    print(f"   Старый: {len(old_skus):,}")
    print(f"   Новый: {len(new_skus):,}")
    
    # Находим новые и удаленные
    new_products_skus = new_skus - old_skus
    removed_products_skus = old_skus - new_skus
    
    print(f"\n📊 Результаты сравнения по НС-код:")
    print(f"   🆕 Новых товаров: {len(new_products_skus):,}")
    print(f"   ❌ Удаленных товаров: {len(removed_products_skus):,}")
    print(f"   🔄 Осталось без изменений: {len(new_skus & old_skus):,}")
    
    # Определяем префикс для файлов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_prefix:
        prefix = output_prefix
    else:
        prefix = f"price_changes_{timestamp}"
    
    # ===== 1. ФАЙЛ С НОВЫМИ ТОВАРАМИ (полный каталог) =====
    if new_products_skus:
        new_rows = []
        for sku in new_products_skus:
            if sku in new_skus_with_data:
                row = new_skus_with_data[sku]
                row_list = [row.get(header, '') for header in new_headers]
                new_rows.append(row_list)
        
        new_output_path = DATA_OUTPUT / f"{prefix}_new_products_full.csv"
        with open(new_output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(new_headers)
            writer.writerows(new_rows)
        
        print(f"\n📄 Файл с НОВЫМИ товарами:")
        print(f"   {new_output_path.name}")
        print(f"   Строк: {len(new_rows):,}, Колонок: {len(new_headers)}")
    else:
        print(f"\n⚠️ Нет новых товаров")
        new_output_path = None
    
    # ===== 2. ФАЙЛ С УДАЛЕННЫМИ ТОВАРАМИ (ТОЛЬКО SKU И ПУСТАЯ ЦЕНА) =====
    if removed_products_skus:
        removed_output_path = DATA_OUTPUT / f"{prefix}_removed_products_empty_price.csv"
        
        # Ручное создание CSV для точного контроля формата
        with open(removed_output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
            writer.writerow(['sku', 'regular_price'])
            for sku in sorted(removed_products_skus):
                writer.writerow([sku, ''])  # Пустое поле - ничего между точками с запятой
        
        print(f"\n📄 Файл с УДАЛЕННЫМИ товарами:")
        print(f"   {removed_output_path.name}")
        print(f"   Строк: {len(removed_products_skus):,}")
        print(f"   Формат: sku;regular_price (regular_price пустой)")
        
        # Показываем пример содержимого
        print(f"\n   Пример содержимого (первые 5 строк):")
        with open(removed_output_path, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f):
                if i < 6:
                    print(f"     {line.strip()}")
                else:
                    break
    else:
        print(f"\n⚠️ Нет удаленных товаров")
        removed_output_path = None
    
    print(f"\n{'='*60}")
    print(f"✅ ГОТОВО!")
    print(f"{'='*60}")
    
    return {
        'new_file': str(new_output_path) if new_output_path else None,
        'removed_file': str(removed_output_path) if removed_output_path else None,
        'new_count': len(new_products_skus),
        'removed_count': len(removed_products_skus)
    }


def main():
    parser = argparse.ArgumentParser(description="Обработка изменений прайс-листов")
    parser.add_argument('--old', '-o', required=True, help='Старый прайс-лист')
    parser.add_argument('--new', '-n', required=True, help='Новый прайс-лист')
    parser.add_argument('--prefix', '-p', help='Префикс для выходных файлов')
    
    args = parser.parse_args()
    
    try:
        results = process_price_changes(
            old_file=args.old,
            new_file=args.new,
            output_prefix=args.prefix
        )
        
        print(f"\n📊 ИТОГИ:")
        print(f"   Новых товаров: {results['new_count']}")
        print(f"   Удаленных товаров: {results['removed_count']}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()