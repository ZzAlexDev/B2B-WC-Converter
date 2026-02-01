import sys
from pathlib import Path
from utils.validators import parse_specifications

# Тест из твоего CSV
test_str = "HEPA (фильтр тонкой очистки): Нет / Pre Filter (фильтр предварительной очистки): Нет / Напряжение электропитания, В: 220 - 240 В"

result = parse_specifications(test_str)
print("Результат парсинга:")
for key, value in result.items():
    print(f"  {key}: {value}")

# Проверяем критичные поля
print(f"\nНапряжение: {result.get('Напряжение электропитания, В', 'НЕ НАЙДЕНО')}")
print(f"Масса товара (нетто): {result.get('Масса товара (нетто)', 'НЕ НАЙДЕНО')}")