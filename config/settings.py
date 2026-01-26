# config/settings.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

@dataclass
class PathConfig:
    """Конфигурация путей к файлам и папкам."""
    INPUT_DIR: str = os.getenv('INPUT_DIR', 'input')
    OUTPUT_DIR: str = os.getenv('OUTPUT_DIR', 'data/output')
    IMAGE_CACHE_DIR: str = os.getenv('IMAGE_CACHE_DIR', 'data/images')

@dataclass
class BusinessLogicConfig:
    """Конфигурация бизнес-логики."""
    DELIVERY_MARKUP: float = float(os.getenv('DELIVERY_MARKUP', '1.0'))

@dataclass
class ImageConfig:
    """Конфигурация обработки изображений."""
    MAX_WIDTH: int = int(os.getenv('IMAGE_MAX_WIDTH', '1200'))
    QUALITY: int = int(os.getenv('IMAGE_QUALITY', '85'))

# Создаём единый объект конфигурации для импорта в других модулях
path_config = PathConfig()
biz_config = BusinessLogicConfig()
image_config = ImageConfig()