#!/usr/bin/env python3
"""
Скрипт для извлечения артикулов (НС-код) и цен из CSV файла
С правильной обработкой сдвинутых колонок
"""

import argparse
import sys
import re
from pathlib import Path
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
DATA_INPUT = PROJECT_ROOT / "data" / "input"
DATA_OUTPUT = PROJECT_ROOT / "data" / "output"


def extract_articles_prices(input_file, output_file=None, show_stats=True):
    """
    Извлекает колонки "НС-код" (артикул) и "Цена" из CSV файла
    """
    # Определяем полный путь к входному файлу
    input_path = Path(input_file)
    
    if not input_path.exists():
        test_path = DATA_INPUT / input_path.name
        if test_path.exists():
            input_path = test_path
            if show_stats:
                print(f"🔍 Файл найден в: {input_path}")
        else:
            raise FileNotFoundError(f"Файл не найден: {input_file}")
    
    # Читаем файл вручную, обрабатывая возможные проблемы
    print(f"\n📖 Чтение файла: {input_path.name}")
    
    # Пробуем разные способы чтения
    df = None
    
    # Способ 1: с обработкой ошибок и указанием правильных колонок
    try:
        # Явно указываем имена колонок
        column_names = [
            'Наименование', 'Артикул', 'Бренд', 'Название категории', 
            'Характеристики', 'Изображение', 'Видео', 'Сопут.товар', 
            'Аналоги', 'Статья', 'Чертежи', 'Сертификаты', 
            'Промоматериалы', 'Инструкции', 'Штрих код', 'Цена', 
            'НС-код', 'Эксклюзив'
        ]
        
        # Читаем с engine='python' для лучшей обработки ошибок
        df = pd.read_csv(
            input_path, 
            sep=';', 
            encoding='utf-8-sig',
            names=column_names,
            header=0,  # первая строка - заголовок
            on_bad_lines='skip',  # пропускаем проблемные строки
            engine='python'
        )
        
        if show_stats:
            print(f"✅ Файл прочитан успешно")
            print(f"   Строк: {len(df):,}")
            print(f"   Колонок: {len(df.columns)}")
            
    except Exception as e:
        print(f"⚠️ Ошибка при чтении: {e}")
        print(f"Пробуем альтернативный способ...")
        
        # Способ 2: читаем построчно
        data_rows = []
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        headers = lines[0].strip().split(';')
        print(f"   Заголовков: {len(headers)}")
        
        for line_num, line in enumerate(lines[1:], 2):
            # Разбиваем, но сохраняем все части
            parts = line.strip().split(';')
            
            # Если частей больше чем заголовков, объединяем последние
            if len(parts) > len(headers):
                # Объединяем лишние части в последнюю колонку
                extra = len(parts) - len(headers)
                parts = parts[:-(extra)] + [';'.join(parts[-(extra):])]
            elif len(parts) < len(headers):
                # Добавляем пустые значения
                parts.extend([''] * (len(headers) - len(parts)))
            
            data_rows.append(parts)
        
        df = pd.DataFrame(data_rows, columns=headers)
        if show_stats:
            print(f"✅ Файл прочитан (построчно)")
            print(f"   Строк: {len(df):,}")
            print(f"   Колонок: {len(df.columns)}")
    
    if df is None or len(df) == 0:
        raise Exception("Не удалось прочитать файл")
    
    # Проверяем наличие нужных колонок
    if show_stats:
        print(f"\n📋 Доступные колонки:")
        for i, col in enumerate(df.columns):
            print(f"   {i}: {col}")
        
        # Показываем первые 2 строки для проверки
        print(f"\n📋 Пример данных (первые 2 строки):")
        for idx in range(min(2, len(df))):
            print(f"\n   Строка {idx + 1}:")
            for col in ['Артикул', 'Цена', 'НС-код', 'Штрих код']:
                if col in df.columns:
                    val = df.iloc[idx][col] if idx < len(df) else 'N/A'
                    print(f"      {col}: {val}")
    
    # Определяем правильные колонки
    # Из диагностики видно, что Цена на самом деле в колонке 'Штрих код'
    # А НС-код в колонке 'Цена'
    sku_column = None
    price_column = None
    
    # Ищем SKU: должно быть в колонке 'НС-код' или 'Цена'
    if 'НС-код' in df.columns:
        # Проверяем, что в НС-код действительно коды (начинаются с НС-)
        sample = df['НС-код'].iloc[0] if len(df) > 0 else ''
        if str(sample).startswith('НС-'):
            sku_column = 'НС-код'
        elif 'Цена' in df.columns:
            sample = df['Цена'].iloc[0] if len(df) > 0 else ''
            if str(sample).startswith('НС-'):
                sku_column = 'Цена'
    
    # Если не нашли, пробуем 'Артикул'
    if not sku_column and 'Артикул' in df.columns:
        sku_column = 'Артикул'
    
    # Ищем цену: должна быть в колонке 'Штрих код' (содержит число и руб.)
    if 'Штрих код' in df.columns:
        sample = df['Штрих код'].iloc[0] if len(df) > 0 else ''
        if 'руб' in str(sample) or str(sample).isdigit():
            price_column = 'Штрих код'
    elif 'Цена' in df.columns and not price_column:
        price_column = 'Цена'
    
    if not sku_column or not price_column:
        raise ValueError(
            f"Не удалось определить колонки.\n"
            f"SKU найдено в: {sku_column}\n"
            f"Цена найдена в: {price_column}\n"
            f"Доступные колонки: {list(df.columns)}"
        )
    
    if show_stats:
        print(f"\n✅ Используемые колонки:")
        print(f"   SKU (артикул): '{sku_column}'")
        print(f"   Цена: '{price_column}'")
    
    # Создаем результат
    result_data = []
    
    for idx, row in df.iterrows():
        sku = str(row[sku_column]).strip() if pd.notna(row[sku_column]) else ''
        
        # Очищаем цену
        price_raw = str(row[price_column]).strip() if pd.notna(row[price_column]) else ''
        price_clean = None
        
        if price_raw:
            # Извлекаем число из строки (удаляем "руб." и всё кроме цифр)
            price_match = re.search(r'(\d+[\s\d]*)\s*руб', price_raw, re.IGNORECASE)
            if price_match:
                price_str = price_match.group(1).replace(' ', '')
                price_clean = int(price_str)
            else:
                # Пробуем просто все цифры
                digits = re.sub(r'[^\d]', '', price_raw)
                if digits:
                    price_clean = int(digits)
        
        if sku and price_clean is not None and sku != 'nan' and sku != '':
            # Пропускаем строки с 'Эксклюзив' в SKU
            if 'Эксклюзив' not in sku:
                result_data.append({
                    'sku': sku,
                    'price': price_clean
                })
    
    result_df = pd.DataFrame(result_data)
    
    if show_stats:
        print(f"\n🔧 Примеры обработки (первые 10):")
        for i, row in enumerate(result_df.head(10).iterrows(), 1):
            idx, data = row
            print(f"   {i}. SKU: {data['sku']} -> Цена: {data['price']}")
    
    if show_stats and len(result_df) > 0:
        print(f"\n📊 Статистика:")
        print(f"   Всего строк: {len(result_df):,}")
        print(f"   Уникальных SKU: {result_df['sku'].nunique():,}")
        print(f"\n   Цены:")
        print(f"   Минимальная: {result_df['price'].min():,}")
        print(f"   Максимальная: {result_df['price'].max():,}")
        print(f"   Средняя: {result_df['price'].mean():,.0f}")
    
    # Определяем выходной файл
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = input_path.stem
        output_file = f"{base_name}_sku_prices_{timestamp}.csv"
    
    output_path = Path(output_file)
    if output_path.parent == Path('.'):
        DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
        output_path = DATA_OUTPUT / output_path.name
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем результат
    if len(result_df) > 0:
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
        print(f"\n💾 Сохранён файл: {output_path}")
        print(f"\n📋 Пример первых 10 записей:")
        print(result_df.head(10).to_string(index=False))
    else:
        print(f"\n⚠️ Нет данных для сохранения!")
    
    return {
        'success': len(result_df) > 0,
        'output_file': str(output_path) if len(result_df) > 0 else None,
        'rows': len(result_df),
        'unique_skus': result_df['sku'].nunique() if len(result_df) > 0 else 0
    }


def main():
    parser = argparse.ArgumentParser(
        description="Извлечение SKU и Цена из CSV файла для WooCommerce"
    )
    
    parser.add_argument('--input', '-i', required=True, 
                       help='Имя CSV файла (ищет в data/input) или полный путь')
    parser.add_argument('--output', '-o', 
                       help='Имя выходного файла (сохраняется в data/output)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Минимум вывода')
    
    args = parser.parse_args()
    
    try:
        result = extract_articles_prices(
            input_file=args.input,
            output_file=args.output,
            show_stats=not args.quiet
        )
        
        if args.quiet and result['output_file']:
            print(result['output_file'])
        elif not args.quiet:
            if result['success']:
                print(f"\n✅ Готово! Файл сохранён: {result['output_file']}")
                print(f"   Обработано товаров: {result['rows']}")
                print(f"   Уникальных SKU: {result['unique_skus']}")
            else:
                print(f"\n❌ Не удалось извлечь данные")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()