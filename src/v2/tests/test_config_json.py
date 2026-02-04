# test_configs.py
import json
import os
from pathlib import Path

def test_all_configs():
    """Тестирует все конфигурационные файлы"""
    config_dir = Path("E:/AlexZ/dev_project/B2B-WC-Converter/config")
    
    config_files = [
        "settings.json",
        "field_mapping.json", 
        "attribute_mapping.json",
        "seo_templates.json",
        "ftp_config.json",
        "image_processing_config.json"
    ]
    
    print("🔍 Проверка конфигурационных файлов:")
    print("=" * 50)
    
    all_valid = True
    
    for config_file in config_files:
        file_path = config_dir / config_file
        
        if not file_path.exists():
            print(f"❌ {config_file}: Файл не найден")
            all_valid = False
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data:
                print(f"✅ {config_file}: Загружен успешно ({len(data) if isinstance(data, dict) else 'данные'})")
            else:
                print(f"⚠️ {config_file}: Файл пустой")
                all_valid = False
                
        except json.JSONDecodeError as e:
            print(f"❌ {config_file}: Ошибка JSON - {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {config_file}: Ошибка - {e}")
            all_valid = False
    
    print("=" * 50)
    
    if all_valid:
        print("🎯 ВСЕ КОНФИГИ ВАЛИДНЫ! Можно запускать run_v2.py")
        
        # Проверяем структуру папок
        print("\n📁 Проверка структуры папок:")
        required_dirs = [
            "data/downloads/images",
            "data/downloads/converted", 
            "data/output",
            "data/logs",
            "data/temp"
        ]
        
        base_dir = Path("E:/AlexZ/dev_project/B2B-WC-Converter")
        for dir_path in required_dirs:
            full_path = base_dir / dir_path
            if full_path.exists():
                print(f"  ✅ {dir_path}")
            else:
                print(f"  ⚠️ {dir_path} - создайте папку")
                
    else:
        print("⚠️ Есть проблемы с конфигами. Исправьте перед запуском.")

if __name__ == "__main__":
    test_all_configs()