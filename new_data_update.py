import os
import time
from pathlib import Path

# Путь к вашей папке
folder_path = Path(r'\data\downloads\converted')

# Текущее время
current_time = time.time()

# Обновляем дату для всех файлов в папке
for file_path in folder_path.glob('*'):
    if file_path.is_file():
        os.utime(file_path, (current_time, current_time))
        print(f"✅ Обновлена дата: {file_path.name}")

print(f"\n✅ Все файлы в {folder_path} обновлены")