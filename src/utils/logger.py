"""
Утилита для логирования
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "b2b_wc_converter",
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    console_output: bool = True
) -> logging.Logger:
    """
    Настройка логгера
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов (если None - только консоль)
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Вывод в консоль
    
    Returns:
        Настроенный логгер
    """
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для консоли
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Обработчик для файла
    if log_file:
        # Создаем директорию для логов если не существует
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Глобальный логгер для удобства
_logger_instance = None


def get_logger() -> logging.Logger:
    """
    Получение глобального логгера
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = setup_logger()
    
    return _logger_instance


def log_product_processed(product_id: int, product_name: str, success: bool = True):
    """
    Логирование обработки товара
    
    Args:
        product_id: ID товара
        product_name: Название товара
        success: Успешно ли обработан
    """
    logger = get_logger()
    status = "✅" if success else "❌"
    logger.info(f"{status} Товар #{product_id}: {product_name}")


def log_batch_progress(current: int, total: int, batch_size: int = 50):
    """
    Логирование прогресса обработки пачки
    
    Args:
        current: Текущий номер товара
        total: Общее количество товаров
        batch_size: Размер пачки
    """
    logger = get_logger()
    
    if current % batch_size == 0 or current == total:
        percent = (current / total) * 100
        logger.info(f"📊 Прогресс: {current}/{total} ({percent:.1f}%)")


def log_error(error_msg: str, exc_info: bool = False):
    """
    Логирование ошибки
    
    Args:
        error_msg: Сообщение об ошибке
        exc_info: Логировать traceback
    """
    logger = get_logger()
    logger.error(error_msg, exc_info=exc_info)


def log_warning(warning_msg: str):
    """
    Логирование предупреждения
    """
    logger = get_logger()
    logger.warning(f"⚠️ {warning_msg}")


def log_info(info_msg: str):
    """
    Логирование информационного сообщения
    """
    logger = get_logger()
    logger.info(f"ℹ️ {info_msg}")


def log_debug(debug_msg: str):
    """
    Логирование отладочного сообщения
    """
    logger = get_logger()
    logger.debug(f"🔍 {debug_msg}")