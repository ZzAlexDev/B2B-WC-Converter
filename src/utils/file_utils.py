"""
Утилиты для работы с файлами
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse
import requests
from .logger import log_error, log_info


def ensure_dir_exists(directory_path: str) -> bool:
    """
    Создание директории если не существует
    
    Args:
        directory_path: Путь к директории
    
    Returns:
        True если директория существует или создана
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        log_error(f"Ошибка создания директории {directory_path}: {e}")
        return False


def get_file_extension(url: str) -> str:
    """
    Получение расширения файла из URL
    
    Args:
        url: URL файла
    
    Returns:
        Расширение файла (без точки)
    """
    try:
        # Парсим URL
        parsed = urlparse(url)
        path = parsed.path
        
        # Получаем расширение
        _, ext = os.path.splitext(path)
        
        # Убираем точку и приводим к нижнему регистру
        if ext:
            return ext.lower().lstrip('.')
        
        return ""
    except Exception:
        return ""


def download_file(
    url: str,
    save_path: str,
    timeout: int = 30,
    retries: int = 3
) -> bool:
    """
    Скачивание файла по URL
    
    Args:
        url: URL файла
        save_path: Путь для сохранения
        timeout: Таймаут в секундах
        retries: Количество попыток
    
    Returns:
        True если файл успешно скачан
    """
    for attempt in range(retries):
        try:
            log_info(f"Скачивание {url} -> {save_path} (попытка {attempt + 1}/{retries})")
            
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Создаем директорию если не существует
            save_dir = os.path.dirname(save_path)
            ensure_dir_exists(save_dir)
            
            # Сохраняем файл
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            log_info(f"Файл успешно скачан: {save_path}")
            return True
            
        except requests.exceptions.Timeout:
            log_error(f"Таймаут при скачивании {url}")
        except requests.exceptions.RequestException as e:
            log_error(f"Ошибка скачивания {url}: {e}")
        except Exception as e:
            log_error(f"Неизвестная ошибка при скачивании {url}: {e}")
    
    return False


def clean_filename(filename: str, max_length: int = 255) -> str:
    """
    Очистка имени файла от недопустимых символов
    
    Args:
        filename: Исходное имя файла
        max_length: Максимальная длина имени
    
    Returns:
        Очищенное имя файла
    """
    # Заменяем недопустимые символы
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Убираем лишние пробелы
    filename = ' '.join(filename.split())
    
    # Обрезаем если слишком длинный
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename


def get_files_in_directory(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    Получение списка файлов в директории
    
    Args:
        directory: Путь к директории
        extensions: Список разрешенных расширений (если None - все файлы)
    
    Returns:
        Список путей к файлам
    """
    if not os.path.exists(directory):
        return []
    
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        if os.path.isfile(item_path):
            if extensions:
                _, ext = os.path.splitext(item)
                if ext.lower().lstrip('.') in extensions:
                    files.append(item_path)
            else:
                files.append(item_path)
    
    return files


def copy_file(source: str, destination: str) -> bool:
    """
    Копирование файла
    
    Args:
        source: Путь к исходному файлу
        destination: Путь к целевому файлу
    
    Returns:
        True если копирование успешно
    """
    try:
        # Создаем директорию если не существует
        dest_dir = os.path.dirname(destination)
        ensure_dir_exists(dest_dir)
        
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        log_error(f"Ошибка копирования файла {source} -> {destination}: {e}")
        return False


def delete_file(file_path: str) -> bool:
    """
    Удаление файла
    
    Args:
        file_path: Путь к файлу
    
    Returns:
        True если файл удален или не существует
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            log_info(f"Файл удален: {file_path}")
        return True
    except Exception as e:
        log_error(f"Ошибка удаления файла {file_path}: {e}")
        return False