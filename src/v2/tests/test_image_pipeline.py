"""
test_image_pipeline.py - тестирование полного пайплайна обработки изображений
"""
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestImagePipeline:
    """Тестирует полный пайплайн обработки изображений."""
    
    def __init__(self):
        self.test_dir = None
        self.original_config = None
    
    def setup(self):
        """Подготовка тестового окружения."""
        print("=" * 60)
        print("🧪 НАСТРОЙКА ТЕСТОВОГО ОКРУЖЕНИЯ")
        print("=" * 60)
        
        # Создаем временную директорию для тестов
        self.test_dir = Path(tempfile.mkdtemp(prefix="image_test_"))
        print(f"📁 Тестовая директория: {self.test_dir}")
        
        # Копируем .env если есть
        env_src = project_root / ".env"
        if env_src.exists():
            shutil.copy(env_src, self.test_dir / ".env")
            print("✅ .env скопирован")
        
        # Создаем тестовую структуру
        (self.test_dir / "downloads/images").mkdir(parents=True, exist_ok=True)
        (self.test_dir / "downloads/convert_img").mkdir(parents=True, exist_ok=True)
        (self.test_dir / "status").mkdir(parents=True, exist_ok=True)
        
        print("✅ Тестовая структура создана")
        return True
    
    def test_1_image_processor(self):
        """Тест обработки изображений."""
        print("\n" + "=" * 60)
        print("🔧 ТЕСТ 1: ОБРАБОТКА ИЗОБРАЖЕНИЙ")
        print("=" * 60)
        
        try:
            from utils.image_processor import ImageProcessor
            
            # Тестовый конфиг
            config = {
                "paths": {
                    "local_image_converted": str(self.test_dir / "downloads/convert_img")
                },
                "image_processing": {
                    "enabled": True,
                    "target_width": 800,  # Меньше для быстрого теста
                    "quality": 70,
                    "add_noise": True,
                    "noise_level": 0.01,
                    "strip_metadata": True,
                    "output_format": "webp",
                    "max_file_size_mb": 5.0,
                    "delete_original": False
                }
            }
            
            processor = ImageProcessor(config)
            
            # Создаем тестовое изображение
            test_image = self._create_test_image("test_original.jpg", width=1600, height=1200)
            print(f"📸 Создано тестовое изображение: {test_image}")
            print(f"   Размер: {test_image.stat().st_size / 1024:.1f} KB")
            
            # Обрабатываем
            processed = processor.process_image(test_image)
            
            if processed and processed.exists():
                print(f"✅ Обработка успешна: {processed.name}")
                print(f"   Размер: {processed.stat().st_size / 1024:.1f} KB")
                
                # Проверяем формат
                from PIL import Image
                with Image.open(processed) as img:
                    print(f"   Формат: {img.format}, Размер: {img.size}")
                    assert img.format == 'WEBP', f"Неверный формат: {img.format}"
                    assert img.width <= 800, f"Ширина больше целевой: {img.width}"
                    
                # Проверяем что файл не слишком большой
                max_size_mb = 1.0  # webp должен быть маленьким
                file_size_mb = processed.stat().st_size / (1024 * 1024)
                assert file_size_mb <= max_size_mb, f"Файл слишком большой: {file_size_mb:.2f}MB"
                
                return True
            else:
                print("❌ Обработка не удалась")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка теста обработки: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_2_ftp_uploader(self):
        """Тест FTP соединения."""
        print("\n" + "=" * 60)
        print("☁️ ТЕСТ 2: FTP СОЕДИНЕНИЕ")
        print("=" * 60)
        
        try:
            from utils.ftp_uploader import FTPUploader
            
            # Проверяем наличие .env переменных
            from dotenv import load_dotenv
            load_dotenv()
            
            ftp_host = os.getenv('FTP_HOST')
            
            if not ftp_host:
                print("⚠️ FTP_HOST не найден в .env, пропускаем тест")
                return True  # Не ошибка, просто нет настроек
            
            config = {
                "paths": {
                    "ftp_remote_path": "/wp-content/uploads/test_uploads/"
                }
            }
            
            print(f"🔄 Подключение к FTP: {ftp_host}")
            uploader = FTPUploader(config, use_env=True)
            ftp = uploader.connect()
            
            if ftp:
                print("✅ Подключение к FTP успешно")
                
                # Тест создания директории
                try:
                    ftp.cwd("/")
                    print("✅ Корневая директория доступна")
                except Exception as e:
                    print(f"⚠️ Не удалось перейти в корень: {e}")
                
                # Тестовая загрузка файла
                test_file = self._create_test_file("ftp_test.txt", "FTP Test Content")
                if test_file.exists():
                    success = uploader.upload_file(test_file, "test_file.txt")
                    if success:
                        print("✅ Тестовый файл загружен")
                    else:
                        print("⚠️ Не удалось загрузить тестовый файл")
                
                ftp.quit()
                return True
            else:
                print("❌ Не удалось подключиться к FTP")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка теста FTP: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_3_status_tracker(self):
        """Тест трекера состояния."""
        print("\n" + "=" * 60)
        print("📊 ТЕСТ 3: ТРЕКЕР СОСТОЯНИЯ")
        print("=" * 60)
        
        try:
            from utils.status_tracker import ImageStatusTracker
            
            status_file = self.test_dir / "status" / "test_status.json"
            
            tracker = ImageStatusTracker(status_file=str(status_file))
            
            # Тестовые данные
            ns_code = "TEST-123"
            slug = "test-product"
            index = 1
            
            # Создаем тестовый файл
            test_file = self._create_test_image("status_test.jpg")
            
            # Отмечаем как скачанный
            tracker.mark_downloaded(ns_code, slug, index, test_file)
            
            # Получаем статус
            status = tracker.get_image_status(ns_code, slug, index)
            
            print(f"✅ Статус после скачивания:")
            print(f"   downloaded: {status.get('downloaded', False)}")
            print(f"   processed: {status.get('processed', False)}")
            print(f"   uploaded: {status.get('uploaded', False)}")
            
            # Проверяем
            assert status.get('downloaded', False) == True, "Файл не отмечен как скачанный"
            
            # Проверяем необходимость обработки
            needs_processing = tracker.needs_processing(ns_code, slug, index, test_file)
            print(f"   Нужна обработка? {needs_processing}")
            assert needs_processing == True, "Должна требоваться обработка"
            
            # Отмечаем как обработанный
            processed_file = test_file.with_stem("processed")
            processed_file.write_bytes(test_file.read_bytes())  # Копируем
            
            tracker.mark_processed(ns_code, slug, index, test_file, processed_file)
            
            # Проверяем статус
            status = tracker.get_image_status(ns_code, slug, index)
            assert status.get('processed', False) == True, "Файл не отмечен как обработанный"
            
            # Проверяем что теперь не нуждается в обработке
            needs_processing = tracker.needs_processing(ns_code, slug, index, processed_file)
            assert needs_processing == False, "Не должна требоваться обработка после обработки"
            
            # Проверяем файл статуса
            assert status_file.exists(), "Файл статуса не создан"
            
            import json
            with open(status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert 'images' in data, "Нет ключа images в файле статуса"
                assert f"{ns_code}-{slug}-{index}" in data['images'], "Запись не добавлена"
            
            print("✅ Все проверки трекера пройдены")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста трекера: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_4_integration(self):
        """Тест интеграции всех компонентов."""
        print("\n" + "=" * 60)
        print("🔄 ТЕСТ 4: ПОЛНАЯ ИНТЕГРАЦИЯ")
        print("=" * 60)
        
        try:
            from utils.image_processor import ImageProcessor
            from utils.ftp_uploader import FTPUploader
            from utils.status_tracker import ImageStatusTracker
            
            # Конфиг для теста
            config = {
                "paths": {
                    "local_image_download": str(self.test_dir / "downloads/images"),
                    "local_image_converted": str(self.test_dir / "downloads/convert_img"),
                    "ftp_remote_path": "/wp-content/uploads/test/"
                },
                "image_processing": {
                    "enabled": True,
                    "target_width": 600,
                    "quality": 80,
                    "add_noise": False,  # Отключаем для чистого теста
                    "strip_metadata": True,
                    "output_format": "webp"
                }
            }
            
            # Инициализация всех компонентов
            processor = ImageProcessor(config)
            uploader = FTPUploader(config, use_env=False)  # Без реального FTP
            status_file = self.test_dir / "status" / "integration_status.json"
            tracker = ImageStatusTracker(status_file=str(status_file))
            
            # Симуляция процесса
            ns_code = "INTEGRATION-001"
            slug = "integration-test"
            
            print("📋 Симуляция обработки 3 изображений:")
            
            for i in range(1, 4):
                print(f"\n  Изображение {i}:")
                
                # Создаем "скачанный" файл
                original = self._create_test_image(f"{ns_code}-{slug}-{i}.jpg", width=1200, height=800)
                
                # Отмечаем как скачанный
                tracker.mark_downloaded(ns_code, slug, i, original)
                
                # Обрабатываем
                processed = processor.process_image(original)
                
                if processed:
                    tracker.mark_processed(ns_code, slug, i, original, processed)
                    print(f"    ✅ Обработано: {processed.name}")
                    
                    # Симуляция FTP загрузки
                    print(f"    ☁️  Загружено на FTP (симуляция)")
                    tracker.mark_uploaded(ns_code, slug, i, processed)
            
            # Проверяем итоговую статистику
            import json
            with open(status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total = len(data.get("images", {}))
                processed = sum(1 for img in data["images"].values() if img.get("processed"))
                uploaded = sum(1 for img in data["images"].values() if img.get("uploaded"))
            
            print(f"\n📊 Итоговая статистика:")
            print(f"   Всего изображений: {total}")
            print(f"   Обработано: {processed}")
            print(f"   Загружено на FTP: {uploaded}")
            
            assert total == 3, f"Должно быть 3 изображения, а есть {total}"
            assert processed == 3, f"Должно быть обработано 3, а обработано {processed}"
            
            print("✅ Интеграционный тест пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка интеграционного теста: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_test_image(self, filename: str, width: int = 800, height: int = 600):
        """Создает тестовое изображение."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            img = Image.new('RGB', (width, height), color=(random.randint(50, 200), 
                                                           random.randint(50, 200), 
                                                           random.randint(50, 200)))
            draw = ImageDraw.Draw(img)
            
            # Простой текст
            try:
                font = ImageFont.truetype("arial.ttf", 30)
            except:
                font = ImageFont.load_default()
            
            draw.text((width//2 - 100, height//2 - 15), 
                     f"TEST {width}x{height}", 
                     fill=(255, 255, 255), 
                     font=font)
            
            # Добавляем случайные пиксели для "шума"
            for _ in range(100):
                x = random.randint(0, width-1)
                y = random.randint(0, height-1)
                draw.point((x, y), fill=(random.randint(0, 255), 
                                        random.randint(0, 255), 
                                        random.randint(0, 255)))
            
            save_path = self.test_dir / filename
            img.save(save_path, quality=95)
            
            return save_path
            
        except Exception as e:
            # Fallback - создаем простой файл
            save_path = self.test_dir / filename
            with open(save_path, 'wb') as f:
                f.write(b"FAKE_IMAGE_DATA" * 100)
            return save_path
    
    def _create_test_file(self, filename: str, content: str):
        """Создает тестовый файл."""
        save_path = self.test_dir / filename
        save_path.write_text(content, encoding='utf-8')
        return save_path
    
    def cleanup(self):
        """Очистка тестового окружения."""
        if self.test_dir and self.test_dir.exists():
            try:
                shutil.rmtree(self.test_dir)
                print(f"\n🧹 Очистка: удалена тестовая директория {self.test_dir}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить тестовую директорию: {e}")

def run_all_tests():
    """Запускает все тесты."""
    tester = TestImagePipeline()
    
    try:
        # Настройка
        if not tester.setup():
            print("❌ Ошибка настройки тестового окружения")
            return False
        
        # Запуск тестов
        test_results = []
        
        test_results.append(("Обработка изображений", tester.test_1_image_processor()))
        test_results.append(("FTP соединение", tester.test_2_ftp_uploader()))
        test_results.append(("Трекер состояния", tester.test_3_status_tracker()))
        test_results.append(("Полная интеграция", tester.test_4_integration()))
        
        # Вывод результатов
        print("\n" + "=" * 60)
        print("📋 ИТОГИ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        all_passed = True
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"{status} - {test_name}")
            if not result:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("💥 НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        
        return all_passed
        
    except Exception as e:
        print(f"💥 Критическая ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        tester.cleanup()

def quick_test():
    """Быстрый тест основных функций."""
    print("⚡ БЫСТРЫЙ ТЕСТ МОДУЛЕЙ")
    
    try:
        from utils.image_processor import ImageProcessor
        from utils.ftp_uploader import FTPUploader
        from utils.status_tracker import ImageStatusTracker
        
        print("✅ Все модули импортируются корректно")
        
        # Проверка методов
        print("\n📋 Проверка методов ImageProcessor:")
        print(f"  process_image: {'process_image' in dir(ImageProcessor)}")
        
        print("\n📋 Проверка методов FTPUploader:")
        print(f"  connect: {'connect' in dir(FTPUploader)}")
        print(f"  upload_file: {'upload_file' in dir(FTPUploader)}")
        
        print("\n📋 Проверка методов ImageStatusTracker:")
        print(f"  mark_downloaded: {'mark_downloaded' in dir(ImageStatusTracker)}")
        print(f"  needs_processing: {'needs_processing' in dir(ImageStatusTracker)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка быстрого теста: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ЗАПУСК ТЕСТОВ ПАЙПЛАЙНА ОБРАБОТКИ ИЗОБРАЖЕНИЙ")
    print("=" * 60)
    
    # Сначала быстрый тест
    if quick_test():
        # Затем полный тест
        success = run_all_tests()
        sys.exit(0 if success else 1)
    else:
        print("❌ Быстрый тест не пройден, пропускаем полное тестирование")
        sys.exit(1)