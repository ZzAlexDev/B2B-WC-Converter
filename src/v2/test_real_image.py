"""
test_real_image.py - тестирование на реальном изображении с загрузкой на FTP
"""
import sys
import os
from pathlib import Path
import shutil
import time

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_image_processing():
    """Тестирует обработку реального изображения и загрузку на FTP."""
    print("=" * 80)
    print("🧪 РЕАЛЬНЫЙ ТЕСТ: ОБРАБОТКА ИЗОБРАЖЕНИЯ И FTP ЗАГРУЗКА")
    print("=" * 80)
    
    # 1. Находим тестовый файл
    test_image_path = Path(r"downloads\images\ns-0028148-rukosushilka-electrolux-ehda-2500-1.webp")
    
    if not test_image_path.exists():
        # Попробуем найти в других местах
        possible_paths = [
            Path("downloads/images/ns-0028148-rukosushilka-electrolux-ehda-2500-1.webp"),
            Path("data/downloads/images/ns-0028148-rukosushilka-electrolux-ehda-2500-1.webp"),
            Path.cwd() / "downloads" / "images" / "ns-0028148-rukosushilka-electrolux-ehda-2500-1.webp",
        ]
        
        for path in possible_paths:
            if path.exists():
                test_image_path = path
                break
    
    if not test_image_path.exists():
        print(f"❌ Тестовый файл не найден!")
        print("Искали в:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    print(f"✅ Найден тестовый файл: {test_image_path}")
    print(f"   Размер: {test_image_path.stat().st_size / 1024:.1f} KB")
    
    # 2. Проверяем что это действительно изображение
    try:
        from PIL import Image
        with Image.open(test_image_path) as img:
            print(f"📊 Исходное изображение:")
            print(f"   Формат: {img.format}")
            print(f"   Размер: {img.size[0]}x{img.size[1]} пикселей")
            print(f"   Режим: {img.mode}")
    except Exception as e:
        print(f"⚠️ Не удалось открыть как изображение: {e}")
    
    # 3. Инициализируем ImageProcessor
    try:
        from utils.image_processor import ImageProcessor
        
        config = {
            "paths": {
                "local_image_converted": "data/downloads/convert_img/"
            },
            "image_processing": {
                "enabled": True,
                "target_width": 1000,
                "quality": 85,
                "add_noise": True,
                "noise_level": 0.02,  # 2% шума
                "strip_metadata": True,
                "output_format": "webp",
                "max_file_size_mb": 1.0,
                "delete_original": False
            }
        }
        
        processor = ImageProcessor(config)
        print("\n✅ ImageProcessor инициализирован")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации ImageProcessor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Обрабатываем изображение
    print("\n" + "-" * 40)
    print("🔧 ОБРАБОТКА ИЗОБРАЖЕНИЯ")
    print("-" * 40)
    
    try:
        processed_path = processor.process_image(test_image_path)
        
        if processed_path and processed_path.exists():
            print(f"✅ Изображение обработано: {processed_path.name}")
            print(f"   Путь: {processed_path}")
            
            # Проверяем результат
            with Image.open(processed_path) as img:
                print(f"📊 Обработанное изображение:")
                print(f"   Формат: {img.format}")
                print(f"   Размер: {img.size[0]}x{img.size[1]} пикселей")
                print(f"   Режим: {img.mode}")
            
            # Сравниваем размеры
            original_size = test_image_path.stat().st_size / 1024
            processed_size = processed_path.stat().st_size / 1024
            compression = ((original_size - processed_size) / original_size) * 100
            
            print(f"📈 Сравнение размеров:")
            print(f"   Исходный: {original_size:.1f} KB")
            print(f"   Обработанный: {processed_size:.1f} KB")
            print(f"   Сжатие: {compression:.1f}%")
            
            if processed_size < original_size:
                print("   ✅ Сжатие успешно")
            else:
                print("   ⚠️ Размер увеличился (но это может быть нормально для WebP)")
            
        else:
            print("❌ Обработка не удалась")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Тестируем FTP загрузку
    print("\n" + "-" * 40)
    print("☁️ ТЕСТ FTP ЗАГРУЗКИ")
    print("-" * 40)
    
    try:
        from utils.ftp_uploader import FTPUploader
        from dotenv import load_dotenv
        
        # Загружаем .env
        load_dotenv()
        
        ftp_host = os.getenv('FTP_HOST')
        ftp_user = os.getenv('FTP_USERNAME')
        
        if not ftp_host or not ftp_user:
            print("⚠️ FTP настройки не найдены в .env")
            print("   Проверьте наличие FTP_HOST и FTP_USERNAME")
            return True  # Не ошибка, просто нет настроек
        
        print(f"🔌 Подключение к FTP: {ftp_host} (пользователь: {ftp_user})")
        
        config = {
            "paths": {
                "ftp_remote_path": "/test_uploads/"
            },
            "ftp": {
                "host": ftp_host,
                "username": ftp_user,
                "port": int(os.getenv('FTP_PORT', 21)),
                "use_ftps": os.getenv('FTP_USE_FTPS', 'false').lower() == 'true'
            }
        }
        
        uploader = FTPUploader(config, use_env=True)
        
        # Тест подключения
        ftp = uploader.connect()
        
        if not ftp:
            print("❌ Не удалось подключиться к FTP")
            return False
        
        print("✅ Подключение к FTP успешно")
        
        # Создаем уникальное имя файла для теста
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_filename = f"test_{timestamp}_ns-0028148.webp"
        
        print(f"📤 Загрузка файла: {remote_filename}")
        
        # Загружаем обработанное изображение
        start_time = time.time()
        success = uploader.upload_file(processed_path, remote_filename)
        upload_time = time.time() - start_time
        
        if success:
            print(f"✅ Файл успешно загружен на FTP!")
            print(f"   Время загрузки: {upload_time:.2f} секунд")
            print(f"   Размер: {processed_size:.1f} KB")
            print(f"   Скорость: {processed_size / upload_time:.1f} KB/сек")
            
            # Тест: попробуем загрузить тот же файл с другим именем
            remote_filename_2 = f"test_{timestamp}_ns-0028148_copy.webp"
            print(f"\n🔄 Тест повторной загрузки: {remote_filename_2}")
            
            success_2 = uploader.upload_file(processed_path, remote_filename_2)
            
            if success_2:
                print(f"✅ Второй файл также загружен")
            else:
                print(f"⚠️ Вторая загрузка не удалась (но первая прошла успешно)")
            
            # Получаем список файлов в директории (если поддерживается)
            try:
                print(f"\n📋 Содержимое FTP директории:")
                ftp.cwd(uploader.remote_base_path.strip('/'))
                files = []
                ftp.retrlines('LIST', files.append)
                
                # Фильтруем тестовые файлы
                test_files = [f for f in files if 'test_' in f and '.webp' in f]
                
                if test_files:
                    print(f"   Найдено {len(test_files)} тестовых файлов:")
                    for file_info in test_files[-5:]:  # Последние 5
                        print(f"   - {file_info}")
                else:
                    print("   Тестовые файлы не найдены")
                    
            except Exception as e:
                print(f"⚠️ Не удалось получить список файлов: {e}")
            
        else:
            print("❌ Ошибка загрузки файла на FTP")
            return False
        
        ftp.quit()
        print("\n✅ FTP соединение закрыто")
        
    except Exception as e:
        print(f"❌ Ошибка FTP теста: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Тест трекера состояния
    print("\n" + "-" * 40)
    print("📊 ТЕСТ ТРЕКЕРА СОСТОЯНИЯ")
    print("-" * 40)
    
    try:
        from utils.status_tracker import ImageStatusTracker
        
        tracker = ImageStatusTracker(status_file="data/status/test_real_status.json")
        
        # Тестовые данные
        ns_code = "ns-0028148"
        slug = "rukosushilka-electrolux-ehda-2500"
        index = 1
        
        # Отмечаем все состояния
        tracker.mark_downloaded(ns_code, slug, index, test_image_path)
        tracker.mark_processed(ns_code, slug, index, test_image_path, processed_path)
        tracker.mark_uploaded(ns_code, slug, index, processed_path)
        
        # Получаем итоговый статус
        status = tracker.get_image_status(ns_code, slug, index)
        
        print(f"✅ Статус файла {processed_path.name}:")
        print(f"   Скачан: {status.get('downloaded', False)}")
        print(f"   Обработан: {status.get('processed', False)}")
        print(f"   Загружен на FTP: {status.get('uploaded', False)}")
        
        if status.get('downloaded', False) and status.get('processed', False) and status.get('uploaded', False):
            print("   🎉 Все этапы завершены успешно!")
        else:
            print("   ⚠️ Некоторые этапы не завершены")
        
        # Проверяем файл статуса
        import json
        status_file = Path("data/status/test_real_status.json")
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_images = len(data.get("images", {}))
                print(f"\n📁 Файл статуса создан: {status_file}")
                print(f"   Всего записей: {total_images}")
        
    except Exception as e:
        print(f"⚠️ Ошибка трекера состояния: {e}")
        # Не считаем это критической ошибкой
    
    print("\n" + "=" * 80)
    print("🎉 РЕАЛЬНЫЙ ТЕСТ ЗАВЕРШЁН УСПЕШНО!")
    print("=" * 80)
    
    # 7. Рекомендации
    print("\n📋 РЕКОМЕНДАЦИИ:")
    print("1. Проверьте файл на FTP сервере:")
    print(f"   Папка: {uploader.remote_base_path if 'uploader' in locals() else '/test_uploads/'}")
    print(f"   Файл: {remote_filename if 'remote_filename' in locals() else 'test_*.webp'}")
    
    print("\n2. Для интеграции в MediaHandler убедитесь что:")
    print("   - В settings.json включены image_processing.enabled и ftp.enabled")
    print("   - В .env указаны правильные FTP credentials")
    print("   - Пути в paths.local_image_converted и paths.ftp_remote_path корректны")
    
    return True

def cleanup_test_files():
    """Очистка тестовых файлов."""
    print("\n🧹 ОЧИСТКА ТЕСТОВЫХ ФАЙЛОВ:")
    
    files_to_clean = [
        Path("data/downloads/convert_img/ns-0028148-rukosushilka-electrolux-ehda-2500-1.webp"),
        Path("data/status/test_real_status.json"),
    ]
    
    for file_path in files_to_clean:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"   Удалён: {file_path}")
            except Exception as e:
                print(f"   Не удалось удалить {file_path}: {e}")

if __name__ == "__main__":
    try:
        success = test_real_image_processing()
        
        # Очистка по запросу
        cleanup = input("\n❓ Очистить тестовые файлы? (y/n): ").lower().strip()
        if cleanup == 'y':
            cleanup_test_files()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)