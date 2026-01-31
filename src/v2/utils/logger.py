"""
Утилиты для логирования.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = "data/logs", log_level: int = logging.INFO) -> str:
    """
    Настраивает логирование для всего приложения.
    
    Args:
        log_dir: Директория для логов
        log_level: Уровень логирования
        
    Returns:
        Путь к файлу лога
    """
    # Создаем директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Создаем имя файла с timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"converter_{timestamp}.log"
    
    # Настраиваем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем обработчики
    handlers = []
    
    # Файловый обработчик
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Удаляем старые обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Добавляем новые обработчики
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Настраиваем логгеры для внешних библиотек
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return str(log_file)


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает логгер с указанным именем.
    
    Args:
        name: Имя логгера
        
    Returns:
        Объект логгера
    """
    return logging.getLogger(name)