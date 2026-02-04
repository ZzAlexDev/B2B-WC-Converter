import os
import json
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).parent.parent.parent

class ConfigLoader:
    def __init__(self):
        self.configs = {}
        
    def load_config(self, filename: str) -> Dict[str, Any]:
        """Загружает JSON конфиг из папки config"""
        config_path = BASE_DIR / 'config' / filename
        
        if not config_path.exists():
            # Пробуем альтернативный путь в src/v2/config
            alt_path = BASE_DIR / 'src' / 'v2' / 'config' / filename
            if alt_path.exists():
                config_path = alt_path
            else:
                raise FileNotFoundError(f"Config file {filename} not found")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_settings(self):
        if 'settings' not in self.configs:
            self.configs['settings'] = self.load_config('settings.json')
        return self.configs['settings']
    
    def get_field_mapping(self):
        if 'field_mapping' not in self.configs:
            self.configs['field_mapping'] = self.load_config('field_mapping.json')
        return self.configs['field_mapping']
    
    def get_attribute_mapping(self):
        if 'attribute_mapping' not in self.configs:
            self.configs['attribute_mapping'] = self.load_config('attribute_mapping.json')
        return self.configs['attribute_mapping']
    
    def get_env_var(self, key: str, default: Any = None) -> Any:
        """Получает переменную окружения"""
        return os.getenv(key, default)

# Глобальный экземпляр конфига
config = ConfigLoader()