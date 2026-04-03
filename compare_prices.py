#!/usr/bin/env python3
"""
Скрипт для сравнения двух файлов с SKU и ценами
Находит новые, удаленные товары и изменения цен

Использование:
    python compare_prices.py --old old_prices.csv --new new_prices.csv
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
DATA_INPUT = PROJECT_ROOT / "data" / "input"
DATA_OUTPUT = PROJECT_ROOT / "data" / "output"


def load_price_file(file_path, show_stats=True):
    """
    Загружает файл с SKU и ценами
    Ожидает формат: sku;price
    """
    file_path = Path(file_path)
    
    # Если файл не найден, ищем в data/output или data/input
    if not file_path.exists():
        test_paths = [
            DATA_OUTPUT / file_path.name,
            DATA_INPUT / file_path.name
        ]
        for test_path in test_paths:
            if test_path.exists():
                file_path = test_path
                if show_stats:
                    print(f"🔍 Файл найден в: {file_path}")
                break
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    # Читаем файл
    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
        
        # Проверяем наличие нужных колонок
        required_cols = ['sku', 'price']
        for col in required_cols:
            if col not in df.columns:
                # Пробуем найти похожие колонки
                possible_cols = [c for c in df.columns if c.lower() in ['sku', 'article', 'артикул', 'код']]
                if possible_cols:
                    df.rename(columns={possible_cols[0]: 'sku'}, inplace=True)
                else:
                    raise ValueError(f"Колонка '{col}' не найдена. Доступны: {list(df.columns)}")
        
        if show_stats:
            print(f"📖 Загружен файл: {file_path.name}")
            print(f"   Строк: {len(df):,}")
            print(f"   Уникальных SKU: {df['sku'].nunique():,}")
            print(f"   Диапазон цен: {df['price'].min():,} - {df['price'].max():,}")
        
        return df
        
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла {file_path}: {e}")


def compare_prices(old_file, new_file, output_prefix=None, show_stats=True):
    """
    Сравнивает два файла с ценами
    """
    if show_stats:
        print(f"\n{'='*60}")
        print(f"СРАВНЕНИЕ ФАЙЛОВ")
        print(f"{'='*60}")
    
    # Загружаем файлы
    old_df = load_price_file(old_file, show_stats)
    new_df = load_price_file(new_file, show_stats)
    
    if show_stats:
        print(f"\n{'='*60}")
        print(f"АНАЛИЗ РАЗЛИЧИЙ")
        print(f"{'='*60}")
    
    # Создаем словари для быстрого доступа
    old_prices = dict(zip(old_df['sku'], old_df['price']))
    new_prices = dict(zip(new_df['sku'], new_df['price']))
    
    old_skus = set(old_prices.keys())
    new_skus = set(new_prices.keys())
    
    # Находим различия
    new_products = new_skus - old_skus
    removed_products = old_skus - new_skus
    common_skus = old_skus & new_skus
    
    # Анализируем изменения цен
    price_changes = []
    for sku in common_skus:
        old_price = old_prices[sku]
        new_price = new_prices[sku]
        
        if old_price != new_price:
            change = {
                'sku': sku,
                'old_price': old_price,
                'new_price': new_price,
                'difference': new_price - old_price,
                'change_percent': round((new_price - old_price) / old_price * 100, 2)
            }
            price_changes.append(change)
    
    # Разделяем на увеличение и уменьшение
    price_increased = [c for c in price_changes if c['difference'] > 0]
    price_decreased = [c for c in price_changes if c['difference'] < 0]
    
    # Статистика
    if show_stats:
        print(f"\n📊 Статистика:")
        print(f"   Всего товаров в старом файле: {len(old_skus):,}")
        print(f"   Всего товаров в новом файле: {len(new_skus):,}")
        print(f"\n   🆕 Новых товаров: {len(new_products):,}")
        print(f"   ❌ Удаленных товаров: {len(removed_products):,}")
        print(f"   📊 С общим SKU: {len(common_skus):,}")
        print(f"   📈 Изменение цен: {len(price_changes):,}")
        print(f"      - Увеличение: {len(price_increased):,}")
        print(f"      - Уменьшение: {len(price_decreased):,}")
        
        if price_changes:
            max_increase = max(price_increased, key=lambda x: x['difference']) if price_increased else None
            max_decrease = min(price_decreased, key=lambda x: x['difference']) if price_decreased else None
            
            if max_increase:
                print(f"\n   📈 Максимальное увеличение цены:")
                print(f"      {max_increase['sku']}: {max_increase['old_price']:,} → {max_increase['new_price']:,} (+{max_increase['difference']:,})")
            
            if max_decrease:
                print(f"\n   📉 Максимальное уменьшение цены:")
                print(f"      {max_decrease['sku']}: {max_decrease['old_price']:,} → {max_decrease['new_price']:,} ({max_decrease['difference']:,})")
    
    # Создаем DataFrame для результатов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_prefix is None:
        output_prefix = f"comparison_{timestamp}"
    
    results = {}
    
    # 1. Новые товары
    if new_products:
        new_products_data = []
        for sku in new_products:
            new_products_data.append({
                'sku': sku,
                'price': new_prices[sku]
            })
        new_products_df = pd.DataFrame(new_products_data)
        new_file_path = DATA_OUTPUT / f"{output_prefix}_new_products.csv"
        new_products_df.to_csv(new_file_path, index=False, encoding='utf-8-sig', sep=';')
        results['new_products'] = str(new_file_path)
        if show_stats:
            print(f"\n💾 Новые товары сохранены: {new_file_path}")
    
    # 2. Удаленные товары
    if removed_products:
        removed_products_data = []
        for sku in removed_products:
            removed_products_data.append({
                'sku': sku,
                'old_price': old_prices[sku]
            })
        removed_products_df = pd.DataFrame(removed_products_data)
        removed_file_path = DATA_OUTPUT / f"{output_prefix}_removed_products.csv"
        removed_products_df.to_csv(removed_file_path, index=False, encoding='utf-8-sig', sep=';')
        results['removed_products'] = str(removed_file_path)
        if show_stats:
            print(f"💾 Удаленные товары сохранены: {removed_file_path}")
    
    # 3. Изменения цен (полный список)
    if price_changes:
        price_changes_df = pd.DataFrame(price_changes)
        changes_file_path = DATA_OUTPUT / f"{output_prefix}_price_changes.csv"
        price_changes_df.to_csv(changes_file_path, index=False, encoding='utf-8-sig', sep=';')
        results['price_changes'] = str(changes_file_path)
        if show_stats:
            print(f"💾 Изменения цен сохранены: {changes_file_path}")
    
    # 4. Увеличение цен
    if price_increased:
        price_increased_df = pd.DataFrame(price_increased)
        increased_file_path = DATA_OUTPUT / f"{output_prefix}_price_increased.csv"
        price_increased_df.to_csv(increased_file_path, index=False, encoding='utf-8-sig', sep=';')
        results['price_increased'] = str(increased_file_path)
        if show_stats:
            print(f"💾 Увеличение цен сохранены: {increased_file_path}")
    
    # 5. Уменьшение цен
    if price_decreased:
        price_decreased_df = pd.DataFrame(price_decreased)
        decreased_file_path = DATA_OUTPUT / f"{output_prefix}_price_decreased.csv"
        price_decreased_df.to_csv(decreased_file_path, index=False, encoding='utf-8-sig', sep=';')
        results['price_decreased'] = str(decreased_file_path)
        if show_stats:
            print(f"💾 Уменьшение цен сохранены: {decreased_file_path}")
    
    # 6. Сводный отчет
    summary_data = {
        'Показатель': [
            'Товаров в старом файле',
            'Товаров в новом файле',
            'Новых товаров',
            'Удаленных товаров',
            'С общим SKU',
            'Изменений цен',
            'Увеличений',
            'Уменьшений'
        ],
        'Значение': [
            len(old_skus),
            len(new_skus),
            len(new_products),
            len(removed_products),
            len(common_skus),
            len(price_changes),
            len(price_increased),
            len(price_decreased)
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_file_path = DATA_OUTPUT / f"{output_prefix}_summary.csv"
    summary_df.to_csv(summary_file_path, index=False, encoding='utf-8-sig', sep=';')
    results['summary'] = str(summary_file_path)
    
    if show_stats:
        print(f"💾 Сводный отчет сохранен: {summary_file_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Сравнение двух файлов с SKU и ценами",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Примеры использования:
  # Сравнить два файла
  python compare_prices.py --old old_prices.csv --new new_prices.csv
  
  # С указанием префикса для выходных файлов
  python compare_prices.py -o old.csv -n new.csv --prefix april_2026

Форматы файлов:
  Ожидается CSV с разделителем ; и колонками: sku;price
  Например:
    sku;price
    НС-0028148;14990
    НС-1057060;39990

Результаты:
  - *_new_products.csv - новые товары
  - *_removed_products.csv - удаленные товары
  - *_price_changes.csv - все изменения цен
  - *_price_increased.csv - только увеличения
  - *_price_decreased.csv - только уменьшения
  - *_summary.csv - сводный отчет
        """
    )
    
    parser.add_argument('--old', '-o', required=True, 
                       help='Путь к старому файлу с ценами')
    parser.add_argument('--new', '-n', required=True, 
                       help='Путь к новому файлу с ценами')
    parser.add_argument('--prefix', '-p', 
                       help='Префикс для выходных файлов (по умолчанию: comparison_дата)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Минимум вывода')
    
    args = parser.parse_args()
    
    try:
        results = compare_prices(
            old_file=args.old,
            new_file=args.new,
            output_prefix=args.prefix,
            show_stats=not args.quiet
        )
        
        if not args.quiet:
            print(f"\n{'='*60}")
            print(f"✅ Сравнение завершено!")
            print(f"{'='*60}")
            print(f"\nСоздано файлов: {len(results)}")
            for key, filepath in results.items():
                print(f"   - {key}: {Path(filepath).name}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()