"""
Утилиты для валидации данных.
"""
import re
from typing import Optional, Tuple, Any
from urllib.parse import urlparse


def safe_strip(value: Any, default: str = "") -> str:
    """
    Безопасно обрезает пробелы у значения.
    
    Args:
        value: Любое значение (может быть None, строкой, числом и т.д.)
        default: Значение по умолчанию, если value равно None или пустое
        
    Returns:
        Обрезанная строка или default
    """
    if value is None:
        return default
    
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    
    # Для чисел и других типов преобразуем в строку
    return str(value).strip()


def safe_getattr(obj: Any, attr_name: str, default: str = "") -> str:
    """
    Безопасно получает атрибут объекта.
    
    Args:
        obj: Объект (например, RawProduct)
        attr_name: Имя атрибута (например, "Наименование")
        default: Значение по умолчанию
        
    Returns:
        Значение атрибута или default (в виде обрезанной строки)
    """
    try:
        value = getattr(obj, attr_name, default)
        return safe_strip(value, default)
    except (AttributeError, TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Безопасно преобразует значение в float.
    
    Args:
        value: Любое значение
        default: Значение по умолчанию при ошибке
        
    Returns:
        Число float или default
    """
    try:
        if value is None or (isinstance(value, str) and not value.strip()):
            return default
        
        # Заменяем запятую на точку, удаляем пробелы
        cleaned = str(value).replace(',', '.').replace(' ', '')
        return float(cleaned)
    except (ValueError, TypeError):
        return default


# Существующие функции из вашего файла (оставляем без изменений):

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


# def parse_specifications(specs_string: str) -> dict:
    """
    Парсит строку характеристик формата "Ключ: Значение / Ключ: Значение".
    Корректно обрабатывает запятые и точки с запятой в значениях.
    
    Args:
        specs_string: Строка характеристик
        
    Returns:
        Словарь характеристик {ключ: значение}
    """
    if not specs_string:
        return {}
        
    specs = {}


    
    # Убираем лишние пробелы в начале/конце
    string = specs_string.strip()
    
    # Разбиваем по "/" - основной разделитель
    # Но защищаем от случайных "/" в значениях
    parts = []
    current_part = []
    depth = 0  # Для учета скобок/кавычек если будут
    
    for char in string:
        if char == '/' and depth == 0:
            parts.append(''.join(current_part).strip())
            current_part = []
        else:
            current_part.append(char)
            # Можно добавить учет скобок/кавычек если нужно
            # if char in '({[': depth += 1
            # elif char in ')}]': depth -= 1
    
    if current_part:
        parts.append(''.join(current_part).strip())
    
    # Фильтруем пустые части
    parts = [p for p in parts if p]
    
    for part in parts:
        # Ищем первое двоеточие, после которого начинается значение
        # Это защищает от двоеточий в значениях (например, "Размер: 10:20 см")
        colon_pos = part.find(':')
        
        if colon_pos > 0:
            key = part[:colon_pos].strip()
            value = part[colon_pos + 1:].strip()
            
            # Убираем точку с запятой в конце значения, если есть
            if value.endswith(';'):
                value = value[:-1].strip()
            
            if key and value:
                # Нормализуем ключ - убираем запятые в конце ключа
                if key.endswith(','):
                    key = key[:-1].strip()
                
                specs[key] = value
    
    return specs



def parse_specifications(specs_string: str) -> dict:
    """
    Парсит строку характеристик.
    Удаляет переносы строк внутри значений.
    """
    if not specs_string:
        return {}
    
    # 1. Удаляем переносы строк, оставляя пробелы
    # Это исправит "220 \n- 240 В" → "220 - 240 В"
    normalized = specs_string.replace('\n', ' ').replace('\r', ' ')
    
    # 2. Убираем лишние пробелы (множественные пробелы → один)
    import re
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    print(f"[DEBUG parse_specifications] Нормализованная строка: {normalized[:200]}...")
    
    specs = {}
    
    # 3. Разбиваем по "/"
    items = [item.strip() for item in normalized.split('/') if item.strip()]
    
    for item in items:
        # Ищем первое двоеточие с пробелом после
        colon_pos = item.find(': ')
        if colon_pos > 0:
            key = item[:colon_pos].strip()
            value = item[colon_pos + 2:].strip()  # +2 для ": "
        else:
            # Пробуем просто двоеточие
            colon_pos = item.find(':')
            if colon_pos > 0:
                key = item[:colon_pos].strip()
                value = item[colon_pos + 1:].strip()
            else:
                continue  # Пропускаем если нет двоеточия
        
        # Если значение начинается с "- " (как "- 240 В"), это продолжение предыдущего
        # Но у нас уже обработаны переносы строк, так что этого не должно быть
        
        specs[key] = value
    
    return specs