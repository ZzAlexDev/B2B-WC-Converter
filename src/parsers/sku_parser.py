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
            ParseResult с данными:
            {
                "article": "Артикул производителя",
                "ns_code": "НС-код",
                "sku": "Основной SKU (нс-код или артикул)",
                "is_ns_code_primary": True/False
            }
        """
        errors = []
        warnings = []
        
        # Очищаем значения
        article_cleaned = self.clean_value(article_value)
        ns_code_cleaned = self.clean_value(ns_code_value)
        
        # Валидация артикула
        article, article_errors = validate_sku(article_cleaned)
        if article_errors:
            errors.extend([f"Артикул: {err}" for err in article_errors])
        elif not article_cleaned:
            warnings.append("Артикул не указан")
        
        # Валидация НС-кода
        ns_code = ns_code_cleaned
        if ns_code_cleaned:
            # НС-код может содержать "НС-" префикс, оставляем как есть
            if not re.match(r'^[a-zA-Z0-9\-/_]+$', ns_code_cleaned):
                errors.append(f"НС-код содержит запрещенные символы: '{ns_code_cleaned}'")
        else:
            warnings.append("НС-код не указан")
        
        # Определяем основной SKU
        if self.use_ns_code_as_sku and ns_code_cleaned:
            sku = ns_code_cleaned
            is_ns_code_primary = True
        elif article:
            sku = article
            is_ns_code_primary = False
        else:
            sku = ""
            is_ns_code_primary = False
            if not errors:  # Не добавляем ошибку если уже есть ошибки валидации
                errors.append("Не удалось определить SKU: нет ни артикула, ни НС-кода")
        
        # Проверка на слишком короткий SKU
        if sku and len(sku) < 3:
            warnings.append(f"SKU слишком короткий: '{sku}'")
        
        # Проверка на слишком длинный SKU
        if sku and len(sku) > 50:
            warnings.append(f"SKU слишком длинный: '{sku}'")
            # Обрезаем
            sku = sku[:50]
        
        # Подготовка данных
        data = {
            "article": article_cleaned,
            "ns_code": ns_code_cleaned,
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