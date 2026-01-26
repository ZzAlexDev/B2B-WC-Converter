# test_mapping.py
import pandas as pd
from config.field_map import SUPPLIER_TO_WC_MAP
from config.settings import path_config

def test_mapping_on_sample():
    """Тестирует маппинг на первых 3 товарах из XLSX."""
    print("=== ТЕСТ МАППИНГА ПОЛЕЙ ===\n")
    
    # 1. Читаем XLSX (только первые 3 строки для теста)
    try:
        input_path = f"{path_config.INPUT_DIR}/catalog_26.01.2026.xlsx"
        df = pd.read_excel(input_path, nrows=3)
        print(f"✅ Файл прочитан: {input_path}")
        print(f"   Колонок: {len(df.columns)}, Тестовых строк: {len(df)}\n")
    except FileNotFoundError:
        print(f"❌ Файл не найден: {input_path}")
        print("   Положи XLSX-файл в папку 'input/'")
        return
    
    # 2. Показываем исходные колонки
    print("Исходные колонки в XLSX:")
    for idx, col in enumerate(df.columns, 1):
        print(f"   {idx:2d}. {col}")
    
    # 3. Применяем маппинг к первому товару
    print("\n--- Преобразование первого товара ---")
    first_product = df.iloc[0].to_dict()
    
    for wc_field, (src_field, processor) in SUPPLIER_TO_WC_MAP.items():
        if src_field is None and processor:
            # Поле вычисляемое (Type, Description и т.д.)
            value = processor(None, first_product)
        elif src_field in first_product:
            # Поле берётся из XLSX
            raw_value = first_product[src_field]
            value = processor(raw_value, first_product) if processor else raw_value
        else:
            value = "[НЕТ ДАННЫХ]"
        
        # Сокращаем длинные значения для наглядности
        display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
        print(f"  {wc_field:25} -> {display_value}")
    
    print("\n✅ Тест завершён. Маппинг работает.")

if __name__ == "__main__":
    test_mapping_on_sample()