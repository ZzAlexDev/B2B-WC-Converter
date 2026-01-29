"""
Утилиты для валидации данных
"""

import re
from typing import Optional, Tuple, List
from .logger import log_error


def validate_price(price_str: str) -> Tuple[Optional[float], List[str]]:
    """
    Валидация и очистка цены
    
    Args:
        price_str: Строка с ценой (например "1 190,00")
    
    Returns:
        Кортеж (очищенная цена, список ошибок)
    """
    errors = []
    
    if not price_str or str(price_str).strip() == "":
        errors.append("Цена не указана")
        return None, errors
    
    try:
        # Приводим к строке
        price_str = str(price_str).strip()
        
        # Убираем все пробелы (разделители тысяч)
        price_str = price_str.replace(" ", "")
        
        # Заменяем запятую на точку (десятичный разделитель)
        price_str = price_str.replace(",", ".")
        

        # Убираем все нецифровые символы кроме точки и запятой
        # Игнорируем "руб.", "RUB", "₽" и другие валютные обозначения
        cleaned = ""
        has_decimal = False
        
        # Список игнорируемых валютных обозначений
        currency_words = ["руб", "rub", "rur", "р.", "₽", "руб.", "rub.", "rur."]
        
        # Проверяем наличие валютных обозначений
        price_lower = price_str.lower()
        for currency in currency_words:
            if currency in price_lower:
                # Убираем валютное обозначение
                price_str = price_str.lower().replace(currency, "")
        
        for char in price_str:
            if char.isdigit():
                cleaned += char
            elif char in ',.' and not has_decimal:
                # Заменяем запятую на точку
                cleaned += '.'
                has_decimal = True
            elif char in ' \t\n\r':
                # Игнорируем пробелы
                continue
            elif char.isalpha():
                # Игнорируем буквы (уже убрали валютные обозначения)
                continue
            else:
                # Другие символы - ошибка
                errors.append(f"Недопустимый символ в цене: '{char}'")

        
        if not cleaned:
            errors.append("Цена не содержит цифр")
            return None, errors
        
        # Конвертируем в число
        price = float(cleaned)
        
        # Проверяем диапазон
        if price <= 0:
            errors.append(f"Цена должна быть положительной: {price}")
        elif price > 10000000:  # 10 миллионов
            errors.append(f"Цена слишком большая: {price}")
        
        return price, errors
        
    except ValueError as e:
        errors.append(f"Ошибка конвертации цены '{price_str}': {e}")
        return None, errors
    except Exception as e:
        errors.append(f"Неизвестная ошибка при валидации цены: {e}")
        return None, errors


def validate_sku(sku_str: str) -> Tuple[Optional[str], List[str]]:
    """
    Валидация SKU
    
    Args:
        sku_str: Строка с SKU
    
    Returns:
        Кортеж (очищенный SKU, список ошибок)
    """
    errors = []
    
    if not sku_str or str(sku_str).strip() == "":
        errors.append("SKU не указан")
        return None, errors
    
    sku = str(sku_str).strip()
    
    # Проверяем длину
    if len(sku) < 2:
        errors.append(f"SKU слишком короткий: '{sku}'")
    
    if len(sku) > 100:
        errors.append(f"SKU слишком длинный: '{sku}'")
    
    # Проверяем на наличие запрещенных символов
    # Разрешаем: буквы, цифры, дефис, слэш, точка, подчеркивание
    if not re.match(r'^[a-zA-Z0-9\-/._]+$', sku):
        errors.append(f"SKU содержит запрещенные символы: '{sku}'")
    
    return sku, errors


def validate_barcode(barcode_str: str) -> Tuple[Optional[str], List[str]]:
    """
    Валидация штрихкода
    
    Args:
        barcode_str: Строка со штрихкодом (может быть несколько через /)
    
    Returns:
        Кортеж (первый очищенный штрихкод, список ошибок)
    """
    errors = []
    
    if not barcode_str or str(barcode_str).strip() == "":
        # Штрихкод не обязателен, возвращаем пустую строку
        return "", []
    
    barcode_str = str(barcode_str).strip()
    
    # Разделяем по возможным разделителям
    separators = ['/', ',', ';', '\\', '|']
    for sep in separators:
        barcode_str = barcode_str.replace(sep, '|')
    
    parts = [part.strip() for part in barcode_str.split('|') if part.strip()]
    
    if not parts:
        return "", []
    
    # Берем первую часть
    first_barcode = parts[0]
    
    # Очищаем от нецифровых символов
    digits_only = ''.join(filter(str.isdigit, first_barcode))
    
    if not digits_only:
        errors.append(f"Штрихкод не содержит цифр: '{first_barcode}'")
        return first_barcode, errors
    
    # Проверяем длину (EAN-13 обычно 13 цифр, UPC 12)
    if len(digits_only) not in [12, 13, 14]:
        errors.append(f"Некорректная длина штрихкода: {len(digits_only)} цифр (ожидается 12-14)")
    
    return digits_only, errors


def validate_email(email: str) -> bool:
    """
    Валидация email адреса
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Валидация URL
    """
    if not url:
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def validate_required(value, field_name: str) -> List[str]:
    """
    Валидация обязательного поля
    
    Args:
        value: Значение поля
        field_name: Название поля для сообщения об ошибке
    
    Returns:
        Список ошибок
    """
    errors = []
    
    if value is None:
        errors.append(f"Обязательное поле '{field_name}' не заполнено")
    elif isinstance(value, str) and not value.strip():
        errors.append(f"Обязательное поле '{field_name}' пустое")
    elif isinstance(value, (list, dict)) and not value:
        errors.append(f"Обязательное поле '{field_name}' пустое")
    
    return errors


def validate_specs_string(specs_str: str) -> bool:
    """
    Валидация строки характеристик
    
    Args:
        specs_str: Строка характеристик (формат: ключ: значение; ключ: значение)
    
    Returns:
        True если строка валидна
    """
    if not specs_str:
        return False
    
    # Проверяем наличие разделителей
    if ':' not in specs_str:
        log_error(f"Строка характеристик не содержит разделителей ':': {specs_str[:100]}...")
        return False
    
    # Проверяем что есть хотя бы одна пара ключ:значение
    pairs = [pair.strip() for pair in specs_str.split(';') if pair.strip()]
    
    valid_pairs = 0
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)
            if key.strip() and value.strip():
                valid_pairs += 1
    
    return valid_pairs > 0