"""
B2B-WC Converter v2.0 - основной пакет
"""

# Версия пакета
__version__ = "2.0.0"
__author__ = "B2B-WC Converter Team"

# Сначала определяем __all__
__all__ = [
    'RawProduct',
    'WooProduct', 
    'ProcessingStats',
    'ConfigManager',
    'ConverterV2',
]

# Ленивые импорты, чтобы избежать циклических зависимостей
import sys

def __getattr__(name):
    if name == 'RawProduct':
        from .models import RawProduct
        return RawProduct
    elif name == 'WooProduct':
        from .models import WooProduct
        return WooProduct
    elif name == 'ProcessingStats':
        from .models import ProcessingStats
        return ProcessingStats
    elif name == 'ConfigManager':
        from .config_manager import ConfigManager
        return ConfigManager
    elif name == 'ConverterV2':
        from .converter import ConverterV2
        return ConverterV2
    else:
        raise AttributeError(f"module 'v2' has no attribute '{name}'")

# Или используем простой вариант без ленивой загрузки:
try:
    from .models import RawProduct, WooProduct, ProcessingStats
    from .config_manager import ConfigManager
    from .converter import ConverterV2
except ImportError as e:
    print(f"⚠️ Внимание: ошибка импорта в v2: {e}")
    # Продолжаем, чтобы не ломать всё