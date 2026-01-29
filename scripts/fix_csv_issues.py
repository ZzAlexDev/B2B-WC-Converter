"""
Скрипт для исправления проблем с CSV
"""

import csv
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def fix_csv_file(input_csv: str, output_csv: str):
    """Исправление CSV файла"""
    print(f"🔧 Исправление CSV: {input_csv} -> {output_csv}")
    
    with open(input_csv, 'r', encoding='utf-8-sig') as f_in, \
         open(output_csv, 'w', newline='', encoding='utf-8-sig') as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        for row_idx, row in enumerate(reader):
            fixed_row = []
            for col_idx, cell in enumerate(row):
                # Исправляем двойные кавычки
                if '""""' in cell:
                    cell = cell.replace('""""', '""')
                
                # Исправляем HTML символы
                replacements = {
                    '&nbsp;': ' ',
                    '&nbsp': ' ',
                    '&plusmn;': '±',
                    '&plusmn': '±',
                    '&deg;': '°',
                    '&deg': '°',
                    '\t': ' '
                }
                
                for old, new in replacements.items():
                    cell = cell.replace(old, new)
                
                fixed_row.append(cell)
            
            writer.writerow(fixed_row)
            
            if row_idx % 10 == 0:
                print(f"  Обработано строк: {row_idx + 1}")
    
    print(f"✅ CSV исправлен: {output_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python fix_csv_issues.py входной.csv выходной.csv")
        sys.exit(1)
    
    fix_csv_file(sys.argv[1], sys.argv[2])