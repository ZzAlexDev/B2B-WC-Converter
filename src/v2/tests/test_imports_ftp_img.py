# test_imports.py - проверьте что все импорты работают
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from utils.image_processor import ImageProcessor
    print("✅ ImageProcessor импортирован успешно")
    
    from utils.ftp_uploader import FTPUploader
    print("✅ FTPUploader импортирован успешно")
    
    from utils.status_tracker import ImageStatusTracker
    print("✅ ImageStatusTracker импортирован успешно")
    
    # Проверка .env
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    print(f"\nПроверка .env переменных:")
    print(f"  FTP_ENABLED: {os.getenv('FTP_ENABLED')}")
    print(f"  FTP_HOST: {os.getenv('FTP_HOST')}")
    print(f"  FTP_USERNAME: {os.getenv('FTP_USERNAME')}")
    print(f"  FTP_PASSWORD: {'*' * len(os.getenv('FTP_PASSWORD', ''))}")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\nУбедитесь что файлы находятся в папке utils/:")
    print(f"  image_processor.py: {Path('utils/image_processor.py').exists()}")
    print(f"  ftp_uploader.py: {Path('utils/ftp_uploader.py').exists()}")
    print(f"  status_tracker.py: {Path('utils/status_tracker.py').exists()}")
except Exception as e:
    print(f"❌ Другая ошибка: {e}")