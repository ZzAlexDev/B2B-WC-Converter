"""
Парсер для колонки "Цена"
"""

import re
from typing import Dict, Any, Tuple, Optional

from .base_parser import BaseParser, ParseResult
from src.utils.validators import validate_price


class PriceParser(BaseParser):
    """
    Парсер для колонки "Цена"
    
    Обрабатывает:
    1. Очистка формата (пробелы тысяч, запятая десятичная)
    2. Конвертация в число
    3. Проверка валидности
    4. Форматирование для WC
    """
    
    def __init__(self, currency: str = "RUB"):
        """
        Инициализация парсера цены
        
        Args:
            currency: Валюта (RUB, USD, EUR)
        """
        super().__init__(column_name="Цена")
        self.currency = currency
        
        # Регулярные выражения для разных форматов цены
        self.price_patterns = [
            # Формат с пробелом тысяч и запятой десятичной: "1 190,00"
            r'(\d{1,3}(?:\s\d{3})*)[,.](\d{2})',
            
            # Формат с точкой десятичной: "1190.00"
            r'(\d+)[.,](\d{2})',
            
            # Формат без копеек: "1 190"
            r'(\d{1,3}(?:\s\d{3})*)',
            
            # Просто число: "1190"
            r'(\d+)',
        ]
    
    def parse(self, value: str) -> ParseResult:
        """
        Парсинг цены
        
        Args:
            value: Значение из колонки "Цена"
        
        Returns:
            ParseResult с данными:
            {
                "price": 1190.00,  # Число
                "price_formatted": "1190.00",  # Строка с 2 знаками
                "currency": "RUB",
                "original_format": "1 190,00",
                "has_cents": True/False
            }
        """
        errors = []
        warnings = []
        
        # Очищаем значение
        
        cleaned_value = self._clean_price_string(self.clean_value(value))
        
        # Проверяем обязательность
        if not cleaned_value:
            errors.append("Цена не может быть пустой")
            return self.create_result(
                data=self._create_empty_result(value),
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        
        try:
            # 1. Валидация и очистка цены
            price, validation_errors = validate_price(cleaned_value)
            
            if validation_errors:
                errors.extend(validation_errors)
                return self.create_result(
                    data=self._create_empty_result(value),
                    original_value=value,
                    errors=errors,
                    warnings=warnings
                )
            
            if price is None:
                errors.append("Не удалось определить цену")
                return self.create_result(
                    data=self._create_empty_result(value),
                    original_value=value,
                    errors=errors,
                    warnings=warnings
                )
            
            # 2. Проверка диапазона
            if price <= 0:
                errors.append(f"Цена должна быть положительной: {price}")
            elif price > 10000000:  # 10 миллионов
                warnings.append(f"Цена очень большая: {price}")
            elif price < 1:
                warnings.append(f"Цена очень маленькая: {price}")
            
            # 3. Форматирование для WooCommerce
            price_formatted = self._format_for_wc(price)
            
            # 4. Определяем есть ли копейки/центы
            has_cents = (price % 1) > 0
            
            # Подготовка данных
            data = {
                "price": price,
                "price_formatted": price_formatted,
                "currency": self.currency,
                "original_format": cleaned_value,
                "has_cents": has_cents,
                "is_free": price == 0,
                "price_int": int(price) if price.is_integer() else price,
            }
            
            return self.create_result(
                data=data,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Ошибка при парсинге цены: {str(e)}")
            self.logger.error(f"Ошибка парсинга цены '{value}': {e}", exc_info=True)
            return self.create_result(
                data=self._create_empty_result(value),
                original_value=value,
                errors=errors,
                warnings=warnings
            )
    
    def _format_for_wc(self, price: float) -> str:
        """
        Форматирование цены для WooCommerce
        
        Args:
            price: Числовая цена
        
        Returns:
            Отформатированная строка (2 знака после запятой)
        """
        # Форматируем с 2 знаками после запятой
        formatted = f"{price:.2f}"
        
        # Убираем лишние нули в конце
        if formatted.endswith('.00'):
            formatted = formatted[:-3]
        elif formatted.endswith('0'):
            formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted
    
    def _create_empty_result(self, original_value: str) -> Dict[str, Any]:
        """Создание пустого результата"""
        return {
            "price": 0.0,
            "price_formatted": "",
            "currency": self.currency,
            "original_format": original_value,
            "has_cents": False,
            "is_free": True,
            "price_int": 0,
        }
    
    def extract_price_from_text(self, text: str) -> Optional[float]:
        """
        Извлечение цены из произвольного текста
        
        Args:
            text: Текст который может содержать цену
        
        Returns:
            Цена или None
        """
        if not text:
            return None
        
        # Ищем числа в тексте
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    # Обрабатываем найденное число
                    if len(match.groups()) == 2:
                        # Есть десятичная часть
                        int_part = match.group(1).replace(' ', '')
                        dec_part = match.group(2)
                        price_str = f"{int_part}.{dec_part}"
                    else:
                        # Только целая часть
                        int_part = match.group(1).replace(' ', '')
                        price_str = int_part
                    
                    price = float(price_str)
                    return price
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _clean_price_string(self, price_str: str) -> str:
        """
        Очистка строки с ценой от валютных обозначений
        
        Args:
            price_str: Строка с ценой (например "99990 руб.")
        
        Returns:
            Очищенная строка
        """
        if not price_str:
            return ""
        
        # Убираем валютные обозначения
        currency_patterns = [
            r'\s*руб\.?\s*', r'\s*rub\.?\s*', r'\s*rur\.?\s*',
            r'\s*р\.\s*', r'\s*₽\s*', r'\s*usd\.?\s*', r'\s*eur\.?\s*',
            r'\s*€\s*', r'\s*\$\s*'
        ]
        
        cleaned = price_str
        for pattern in currency_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()