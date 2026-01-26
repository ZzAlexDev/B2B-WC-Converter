# test_env.py (обновлённый)
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
import paramiko  # Заменяем pysftp на paramiko
import sys

print(f"✅ Python: {sys.version}")
print(f"✅ Pandas: {pd.__version__}")
print(f"✅ Pillow: {Image.__version__}")
print(f"✅ Paramiko: {paramiko.__version__}")  # Проверяем paramiko
print("✅ Все критические модули импортируются успешно.")
print("\nОкружение готово. Библиотека для SFTP: paramiko.")