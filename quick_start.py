"""
Скрипт быстрого старта для B2B-WC Converter v2.0.
Позволяет быстро протестировать конвертер на примере.
"""
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🚀 B2B-WC Converter v2.0 - Быстрый старт")
    print("=" * 50)
    
    print("\n📋 Подготовка проекта...")
    
    # Проверяем наличие необходимых директорий
    directories = [
        "data/input",
        "data/output", 
        "data/downloads/images",
        "data/logs"
    ]
    
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Создана директория: {dir_path}")
    
    print("\n📁 Копирование примера CSV...")
    
    # Копируем пример CSV
    import shutil
    example_csv = Path("examples/sample_input.csv")
    if example_csv.exists():
        shutil.copy(example_csv, "data/input/sample_input.csv")
        print("✅ Пример CSV скопирован в data/input/sample_input.csv")
    else:
        print("⚠️  Файл примера не найден: examples/sample_input.csv")
        print("   Создайте его вручную или запустите тесты")
    
    print("\n⚙️  Проверка конфигурации...")
    
    try:
        from v2.config_manager import ConfigManager
        config = ConfigManager.from_directory("config/v2")
        print("✅ Конфигурация загружена успешно")
        
        # Проверяем ключевые настройки
        required_settings = [
            ('paths.local_image_download', 'data/downloads/images/'),
            ('paths.final_image_url_template', 'https://вашсайт.ru/'),
            ('processing.skip_on_error', True)
        ]
        
        for setting, expected in required_settings:
            value = config.get_setting(setting)
            if value is not None:
                print(f"✅ Настройка {setting}: OK")
            else:
                print(f"⚠️  Настройка {setting}: не найдена")
                
    except Exception as e:
        print(f"❌ Ошибка при загрузке конфигурации: {e}")
        print("\n📝 Создайте конфигурационные файлы в config/v2/")
        print("   Скопируйте их из config/v2/ или создайте заново")
    
    print("\n🎯 Готово! Теперь вы можете:")
    print("1. Запустить тест: python test_final.py")
    print("2. Конвертировать пример: python run_v2.py --input data/input/sample_input.csv")
    print("3. Настроить config/v2/ под свои нужды")
    print("4. Использовать свой CSV файл")
    
    print("\n" + "=" * 50)
    print("✨ Проект готов к использованию!")

if __name__ == "__main__":
    main()