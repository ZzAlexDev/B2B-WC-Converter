"""
Базовый класс для всех парсеров
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass

from src.utils.logger import get_logger


@dataclass
class ParseResult:
    """
    Результат парсинга колонки
    """
    success: bool  # Успешно ли распарсено
    data: Any  # Распарсенные данные
    errors: list  # Список ошибок
    warnings: list  # Список предупреждений
    original_value: str  # Исходное значение
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "original_value": self.original_value
        }


class BaseParser(ABC):
    """
    Базовый класс для всех парсеров колонок
    """
    
    def __init__(self, column_name: str):
        """
        Инициализация парсера
        
        Args:
            column_name: Название колонки которую парсит этот парсер
        """
        self.column_name = column_name
        self.logger = get_logger()
        
    @abstractmethod
    def parse(self, value: str) -> ParseResult:
        """
        Абстрактный метод парсинга
        
        Args:
            value: Значение из ячейки Excel
        
        Returns:
            ParseResult с результатами
        """
        pass
    
    def clean_value(self, value: Any) -> str:
        """
        Очистка значения перед парсингом
        
        Args:
            value: Исходное значение
        
        Returns:
            Очищенная строка
        """
        if value is None:
            return ""
        
        # Приводим к строке
        value_str = str(value)
        
        # Убираем лишние пробелы
        value_str = value_str.strip()
        
        # Заменяем множественные пробелы на один
        value_str = " ".join(value_str.split())
        
        return value_str
    
    def create_result(self, 
                     data: Any, 
                     original_value: str,
                     errors: Optional[list] = None,
                     warnings: Optional[list] = None) -> ParseResult:
        """
        Создание объекта ParseResult
        
        Args:
            data: Распарсенные данные
            original_value: Исходное значение
            errors: Список ошибок
            warnings: Список предупреждений
        
        Returns:
            ParseResult
        """
        if errors is None:
            errors = []
        if warnings is None:
            warnings = []
        
        success = len(errors) == 0
        
        return ParseResult(
            success=success,
            data=data,
            errors=errors,
            warnings=warnings,
            original_value=original_value
        )
    
    def log_parse_result(self, result: ParseResult, row_index: Optional[int] = None):
        """
        Логирование результата парсинга
        
        Args:
            result: Результат парсинга
            row_index: Индекс строки (для логов)
        """
        row_info = f" строка {row_index}" if row_index is not None else ""
        
        if not result.success:
            self.logger.error(
                f"❌ Ошибка парсинга колонки '{self.column_name}'{row_info}: "
                f"{result.errors}"
            )
        elif result.warnings:
            self.logger.warning(
                f"⚠️  Предупреждения при парсинге '{self.column_name}'{row_info}: "
                f"{result.warnings}"
            )
        else:
            self.logger.debug(
                f"✅ Успешно распарсено '{self.column_name}'{row_info}"
            )