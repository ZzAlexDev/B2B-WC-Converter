"""
Парсер для колонки "Название категории"
"""

import re
from typing import Dict, Any, List

from .base_parser import BaseParser, ParseResult
from src.core.models.category import Category


class CategoryParser(BaseParser):
    """
    Парсер для колонки "Название категории"
    
    Обрабатывает:
    1. Разбор иерархии категорий
    2. Удаление дубликатов в строке
    3. Форматирование для WooCommerce
    4. Генерация slug для каждой категории
    """
    
    def __init__(self):
        """Инициализация парсера категории"""
        super().__init__(column_name="Название категории")
    
    def parse(self, value: str) -> ParseResult:
        """
        Парсинг категории
        
        Args:
            value: Значение из колонки "Название категории"
        
        Returns:
            ParseResult с данными:
            {
                "hierarchy": ["Родитель", "Дочерняя", "Внучка"],
                "wc_format": "Родитель > Дочерняя > Внучка",
                "categories": [Category objects],
                "level": 2,
                "main_category": "Последняя категория в цепочке"
            }
        """
        errors = []
        warnings = []
        
        # Очищаем значение
        cleaned_value = self.clean_value(value)
        
        # Проверяем обязательность
        if not cleaned_value:
            errors.append("Категория не может быть пустой")
            return self.create_result(
                data=None,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        
        try:
            # 1. Очистка строки категории
            cleaned_string = self._clean_category_string(cleaned_value)
            
            # 2. Разбор иерархии
            hierarchy = self._parse_hierarchy(cleaned_string)
            
            if not hierarchy:
                errors.append(f"Не удалось разобрать категорию: '{cleaned_string}'")
                return self.create_result(
                    data=None,
                    original_value=value,
                    errors=errors,
                    warnings=warnings
                )
            
            # 3. Проверка на дубли в иерархии
            cleaned_hierarchy = self._remove_duplicate_hierarchy(hierarchy)
            if len(cleaned_hierarchy) != len(hierarchy):
                warnings.append("Удалены дублирующиеся элементы из иерархии категорий")
            
            # 4. Создание объектов Category
            categories = Category.from_string(" - ".join(cleaned_hierarchy))
            
            # 5. Форматирование для WooCommerce
            wc_format = self._format_for_wc(cleaned_hierarchy)
            
            # 6. Проверка глубины вложенности
            if len(cleaned_hierarchy) > 3:
                warnings.append(f"Слишком глубокая вложенность категорий: {len(cleaned_hierarchy)} уровней")
            
            # 7. Основная категория (последняя в цепочке)
            main_category = cleaned_hierarchy[-1] if cleaned_hierarchy else ""
            
            # Подготовка данных
            data = {
                "hierarchy": cleaned_hierarchy,
                "wc_format": wc_format,
                "categories": categories,
                "level": len(cleaned_hierarchy) - 1,
                "main_category": main_category,
                "hierarchy_length": len(cleaned_hierarchy)
            }
            
            return self.create_result(
                data=data,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Ошибка при парсинге категории: {str(e)}")
            return self.create_result(
                data=None,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
    
    def _clean_category_string(self, category_str: str) -> str:
        """
        Очистка строки категории
        
        Args:
            category_str: Исходная строка категории
        
        Returns:
            Очищенная строка
        """
        if not category_str:
            return ""
        
        # Убираем HTML теги
        category_str = re.sub(r'<[^>]+>', '', category_str)
        
        # Заменяем разные разделители на стандартный "-"
        # Поддерживаем: "-", "–", "—", ">", "/"
        separators = ['–', '—', '>', '/', '\\', '|']
        for sep in separators:
            category_str = category_str.replace(sep, '-')
        
        # Убираем множественные дефисы
        category_str = re.sub(r'-+', '-', category_str)
        
        # Убираем пробелы вокруг дефисов
        category_str = re.sub(r'\s*-\s*', '-', category_str)
        
        # Убираем лишние пробелы
        category_str = " ".join(category_str.split())
        
        return category_str.strip()
    
    def _parse_hierarchy(self, category_str: str) -> List[str]:
        """
        Разбор иерархии категорий
        
        Args:
            category_str: Очищенная строка категории
        
        Returns:
            Список элементов иерархии
        """
        if not category_str:
            return []
        
        # Разделяем по дефису
        parts = [part.strip() for part in category_str.split('-') if part.strip()]
        
        # Очищаем каждый элемент
        cleaned_parts = []
        for part in parts:
            # Убираем лишние пробелы
            part = " ".join(part.split())
            
            # Убираем кавычки
            part = part.replace('"', '').replace("'", '')
            
            # Капитализация (первая буква заглавная)
            if part and not part[0].isupper():
                part = part[0].upper() + part[1:]
            
            if part:
                cleaned_parts.append(part)
        
        return cleaned_parts
    
    def _remove_duplicate_hierarchy(self, hierarchy: List[str]) -> List[str]:
        """
        Удаление дублирующихся элементов из иерархии
        
        Args:
            hierarchy: Иерархия категорий
        
        Returns:
            Очищенная иерархия без дубликатов подряд
        """
        if not hierarchy:
            return []
        
        cleaned = []
        for item in hierarchy:
            if not cleaned or item != cleaned[-1]:
                cleaned.append(item)
        
        return cleaned
    
    def _format_for_wc(self, hierarchy: List[str]) -> str:
        """
        Форматирование для WooCommerce
        
        Args:
            hierarchy: Иерархия категорий
        
        Returns:
            Строка в формате "Родитель > Дочерняя > Внучка"
        """
        if not hierarchy:
            return ""
        
        return " > ".join(hierarchy)