"""
Утилиты для работы с файлами.
"""
import os
import re
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse, unquote
import requests
import logging

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от небезопасных символов.
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        Очищенное имя файла
    """
    if not filename:
        return ""
    
    # Заменяем небезопасные символы на подчеркивания
    unsafe_chars = r'[<>:"/\\|?*\'"`\s]'
    safe_name = re.sub(unsafe_chars, '_', filename)
    
    # Убираем множественные подчеркивания
    safe_name = re.sub(r'_+', '_', safe_name)
    
    # Убираем подчеркивания в начале и конце
    safe_name = safe_name.strip('_')
    
    # Ограничиваем длину
    if len(safe_name) > 255:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:255 - len(ext)] + ext
    
    return safe_name


def download_file(url: str, destination: Path, 
                 timeout: int = 30, retries: int = 2) -> bool:
    """
    Скачивает файл по URL.
    
    Args:
        url: URL файла
        destination: Путь для сохранения
        timeout: Таймаут в секундах
        retries: Количество попыток
        
    Returns:
        True если файл скачан успешно
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Сохраняем файл
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.debug(f"Файл скачан: {destination.name}")
            return True
            
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"Попытка {attempt + 1} не удалась для {url}: {e}")
                continue
            else:
                logger.error(f"Не удалось скачать {url}: {e}")
                return False
    
    return False


def get_file_extension_from_url(url: str) -> str:
    """
    Определяет расширение файла из URL.
    
    Args:
        url: URL файла
        
    Returns:
        Расширение файла (без точки)
    """
    try:
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        filename = os.path.basename(path)
        
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            # Ограничиваем длину расширения
            if len(ext) > 10:
                ext = 'dat'
            return ext
    except:
        pass
    
    return ''


def ensure_directory(directory: Path) -> bool:
    """
    Создает директорию, если она не существует.
    
    Args:
        directory: Путь к директории
        
    Returns:
        True если директория существует или создана
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Не удалось создать директорию {directory}: {e}")
        return False


def split_image_urls(images_string: str) -> List[str]:
    """
    Разбивает строку с URL изображений на список.
    
    Args:
        images_string: Строка с URL через запятую
        
    Returns:
        Список URL изображений
    """
    if not images_string:
        return []
    
    # Разбиваем по запятой, убираем пробелы
    urls = [url.strip() for url in images_string.split(',') if url.strip()]
    
    # Фильтруем валидные URL
    valid_urls = []
    for url in urls:
        try:
            result = urlparse(url)
            if all([result.scheme, result.netloc]):
                valid_urls.append(url)
            else:
                logger.warning(f"Невалидный URL изображения: {url}")
        except:
            logger.warning(f"Невалидный URL изображения: {url}")
    
    return valid_urls


def get_unique_filename(directory: Path, base_name: str, extension: str) -> Path:
    """
    Генерирует уникальное имя файла в директории.
    
    Args:
        directory: Директория для файла
        base_name: Базовое имя файла
        extension: Расширение файла (без точки)
        
    Returns:
        Уникальный путь к файлу
    """
    # Очищаем базовое имя
    safe_base = sanitize_filename(base_name)
    
    # Пробуем базовое имя
    counter = 1
    while True:
        if counter == 1:
            filename = f"{safe_base}.{extension}"
        else:
            filename = f"{safe_base}_{counter}.{extension}"
        
        file_path = directory / filename
        
        if not file_path.exists():
            return file_path
        
        counter += 1