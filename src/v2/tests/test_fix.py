# test_fix.py
from src.v2.models import RawProduct

# Тест с None значениями
test_row = {
    'Наименование': 'Тест товар',
    'НС-код': None,  # Имитация пустой ячейки
    'Цена': '1000 руб.',
    'Характеристики': None
}

try:
    product = RawProduct.from_csv_row(test_row, row_number=1)
    print("✅ RawProduct создан успешно!")
    print(f"НС_код: '{product.НС_код}' (тип: {type(product.НС_код)})")
    print(f"Характеристики: '{product.Характеристики}'")
    
    # Пробуем вызвать .strip() на атрибутах
    print(f"НС_код.strip(): '{product.НС_код.strip()}'")
    print(f"Характеристики.strip(): '{product.Характеристики.strip()}'")
    
except Exception as e:
    print(f"❌ Ошибка: {type(e).__name__}: {e}")