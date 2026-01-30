"""
Парсер для колонок "Артикул" и "НС-код"
"""

import re
from typing import Dict, Any

from .base_parser import BaseParser, ParseResult
from src.utils.validators import validate_sku


class SKUParser(BaseParser):
    """
    Парсер для колонок "Артикул" и "НС-код"
    
    Обрабатывает:
    1. Артикул производителя (в атрибуты)
    2. НС-код (основной SKU для WC)
    3. Проверка уникальности (будет в отдельном валидаторе)
    """
    
    def __init__(self, use_ns_code_as_sku: bool = True):
        """
        Инициализация парсера SKU
        
        Args:
            use_ns_code_as_sku: Использовать НС-код как основной SKU
                                Если False - использовать Артикул
        """
        super().__init__(column_name="Артикул и НС-код")
        self.use_ns_code_as_sku = use_ns_code_as_sku
    
    def parse(self, article_value: str, ns_code_value: str = "") -> ParseResult:
        """
        Парсинг артикула и НС-кода
        
        Args:
            article_value: Значение из колонки "Артикул"
            ns_code_value: Значение из колонки "НС-код" (опционально)
        
        Returns:
            ParseResult с данными
        """
        errors = []
        warnings = []
        
        # Очищаем значения
        article_cleaned = self.clean_value(article_value)
        ns_code_cleaned = self.clean_value(ns_code_value)
        
        # Инициализируем переменные
        article = article_cleaned
        ns_code = ns_code_cleaned
        
        # Валидация артикула (но не блокируем если есть ошибки)
        if article_cleaned:
            article_result, article_errors = validate_sku(article_cleaned)
            if article_errors:
                # Добавляем ошибки но не блокируем
                errors.extend([f"Артикул: {err}" for err in article_errors])
                # Используем очищенное значение если есть, иначе оригинальное
                article = article_result if article_result else article_cleaned
        else:
            warnings.append("Артикул не указан")
        
        # Валидация НС-кода (также не блокируем)
        if ns_code_cleaned:
            # Простая проверка на опасные символы
            dangerous_chars = ['<', '>', '"', "'", ';', '=', '&', '%', '$', '#', '@', '!', '*', '(', ')', '[', ']', '{', '}', '\\']
            has_dangerous = any(char in ns_code_cleaned for char in dangerous_chars)
            if has_dangerous:
                warnings.append(f"НС-код содержит опасные символы, они будут удалены: '{ns_code_cleaned}'")
                # Удаляем опасные символы
                for char in dangerous_chars:
                    ns_code_cleaned = ns_code_cleaned.replace(char, '')
                ns_code = ns_code_cleaned
        else:
            warnings.append("НС-код не указан")
        
        # Определяем основной SKU
        if self.use_ns_code_as_sku and ns_code:
            sku = ns_code
            is_ns_code_primary = True
        elif article:
            sku = article
            is_ns_code_primary = False
        else:
            sku = ""
            is_ns_code_primary = False
            if not article_cleaned and not ns_code_cleaned:
                errors.append("Не удалось определить SKU: нет ни артикула, ни НС-кода")
        
        # Проверка на слишком короткий SKU
        if sku and len(sku) < 2:
            warnings.append(f"SKU слишком короткий: '{sku}'")
        
        # Проверка на слишком длинный SKU
        if sku and len(sku) > 50:
            warnings.append(f"SKU слишком длинный: '{sku}'")
            sku = sku[:50]
        
        # Подготовка данных
        data = {
            "article": article,
            "ns_code": ns_code,
            "sku": sku,
            "is_ns_code_primary": is_ns_code_primary,
            "has_article": bool(article_cleaned),
            "has_ns_code": bool(ns_code_cleaned)
        }
        
        return self.create_result(
            data=data,
            original_value=f"Артикул: {article_value}, НС-код: {ns_code_value}",
            errors=errors,
            warnings=warnings
        )
    
    def parse_single(self, value: str, is_ns_code: bool = False) -> ParseResult:
        """
        Парсинг одиночного значения (артикула или НС-кода)
        
        Args:
            value: Значение для парсинга
            is_ns_code: True если это НС-код, False если артикул
        
        Returns:
            ParseResult
        """
        if is_ns_code:
            return self.parse("", value)
        else:
            return self.parse(value, "")