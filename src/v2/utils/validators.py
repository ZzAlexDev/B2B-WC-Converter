"""
Утилиты для валидации данных.
"""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Проверяет, является ли строка валидным URL.
    
    Args:
        url: Строка для проверки
        
    Returns:
        True если URL валиден
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def extract_youtube_id(url: str) -> Optional[str]:
    """
    Извлекает YouTube ID из URL.
    
    Args:
        url: YouTube URL
        
    Returns:
        YouTube ID или None
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/user\/.*#.*\/[a-zA-Z0-9_-]{11}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_price(price_str: str) -> Tuple[str, str]:
    """
    Извлекает цену и валюту из строки.
    
    Args:
        price_str: Строка с ценой (например, "14990 руб.")
        
    Returns:
        Кортеж (цена, валюта)
    """
    if not price_str:
        return "", ""
    
    # Ищем числовую часть
    price_match = re.search(r'(\d+[\.,]?\d*)', price_str.replace(' ', ''))
    
    if not price_match:
        return "", ""
    
    price = price_match.group(1)
    
    # Ищем валюту
    currency_patterns = [
        r'руб\.?', r'р\.?', r'rub', r'rur',
        r'usd', r'\$', r'долл\.?',
        r'eur', r'€', r'евро',
        r'uah', r'грн\.?',
        r'kzt', r'тенге'
    ]
    
    for pattern in currency_patterns:
        if re.search(pattern, price_str.lower()):
            currency = pattern.replace(r'\.?', '').replace('\\', '')
            return price, currency
    
    return price, ""


def normalize_yes_no(value: str, 
                    yes_values: list = None, 
                    no_values: list = None) -> str:
    """
    Нормализует значения Да/Нет.
    
    Args:
        value: Исходное значение
        yes_values: Список значений для "Да"
        no_values: Список значений для "Нет"
        
    Returns:
        Нормализованное значение ("Да", "Нет" или оригинал)
    """
    if yes_values is None:
        yes_values = ['да', 'yes', '1', 'true', 'есть', 'y']
    
    if no_values is None:
        no_values = ['нет', 'no', '0', 'false', 'отсутствует', 'n']
    
    if not value:
        return "Нет"
    
    value_lower = value.lower().strip()
    
    if value_lower in yes_values:
        return "Да"
    elif value_lower in no_values:
        return "Нет"
    
    return value


def generate_slug(text: str, max_length: int = 200) -> str:
    """
    Генерирует slug из текста.
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина slug
        
    Returns:
        slug
    """
    if not text:
        return ""
    
    # Приводим к нижнему регистру
    text = text.lower()
    
    # Таблица транслитерации кириллицы
    cyr_to_lat = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    
    result = []
    for char in text:
        if char in cyr_to_lat:
            result.append(cyr_to_lat[char])
        elif char.isalnum():
            result.append(char)
        elif char in [' ', '-', '_']:
            result.append('-')
        else:
            # Пропускаем специальные символы
            continue
    
    slug = ''.join(result)
    
    # Убираем множественные дефисы
    slug = re.sub(r'-+', '-', slug)
    
    # Убираем дефисы в начале и конце
    slug = slug.strip('-')
    
    # Ограничиваем длину
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug


def parse_specifications(specs_string: str, delimiter: str = '/') -> dict:
    """
    Парсит строку характеристик.
    
    Args:
        specs_string: Строка характеристик
        delimiter: Разделитель характеристик
        
    Returns:
        Словарь характеристик
    """
    if not specs_string:
        return {}
    
    specs = {}
    
    # Нормализуем разделители
    string = specs_string.replace(';', delimiter).replace(',', delimiter)
    
    # Разбиваем по разделителю
    parts = [part.strip() for part in string.split(delimiter) if part.strip()]
    
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if key and value:
                specs[key] = value
    
    return specs