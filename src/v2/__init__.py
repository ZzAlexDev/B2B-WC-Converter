"""
B2B-WC Converter v2.0 - основной пакет
"""

# Версия пакета
__version__ = "2.0.0"
__author__ = "B2B-WC Converter Team"


# Экспортируем основные классы
from .models import RawProduct, WooProduct, ProcessingStats
from .config_manager import ConfigManager
from .converter import ConverterV2

