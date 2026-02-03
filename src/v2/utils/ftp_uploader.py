"""
ftp_uploader.py - загрузка файлов на FTP сервер
"""
from ftplib import FTP, FTP_TLS
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv  # pip install python-dotenv

logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()

class FTPUploader:
    """Класс для загрузки файлов на FTP сервер"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализирует FTPUploader.
        
        Args:
            config: Конфигурация с настройками FTP
            
        Raises:
            ValueError: Если отсутствуют обязательные настройки
        """
        # Используем get_logger из вашей утилиты, если есть
        try:
            from ..utils.logger import get_logger
            self.logger = get_logger(__name__)
        except ImportError:
            self.logger = logging.getLogger(__name__)
        
        # ИСПРАВЛЕННАЯ СТРОКА 32: безопасное получение ftp_remote_path
        # Вариант 1: ищем в разных местах конфига
        ftp_remote_path = None
        
        # Пробуем разные варианты получения пути
        if 'paths' in config and isinstance(config['paths'], dict):
            ftp_remote_path = config['paths'].get('ftp_remote_path')
        elif 'ftp_remote_path' in config:
            ftp_remote_path = config.get('ftp_remote_path')
        elif 'ftp' in config and isinstance(config['ftp'], dict):
            ftp_remote_path = config['ftp'].get('remote_path')
        
        # Значение по умолчанию
        self.remote_base_path = ftp_remote_path or '/wp-content/uploads/images/'
        
        # Получаем настройки FTP
        self.host = config.get('ftp', {}).get('host') or os.getenv('FTP_HOST')
        self.username = config.get('ftp', {}).get('username') or os.getenv('FTP_USERNAME')
        self.password = config.get('ftp', {}).get('password') or os.getenv('FTP_PASSWORD')
        self.port = config.get('ftp', {}).get('port', 21)
        self.timeout = config.get('ftp', {}).get('timeout', 30)
        self.use_tls = config.get('ftp', {}).get('use_tls', False)
        
        # Проверяем обязательные настройки
        missing_configs = []
        if not self.host:
            missing_configs.append('host')
        if not self.username:
            missing_configs.append('username')
        if not self.password:
            missing_configs.append('password')
        
        if missing_configs:
            self.enabled = False
            self.logger.warning(f"FTPUploader отключен: отсутствуют настройки: {', '.join(missing_configs)}")
        else:
            self.enabled = True
            self.logger.info(f"FTPUploader инициализирован для хоста {self.host}:{self.port}")
            self.logger.info(f"Удаленный путь: {self.remote_base_path}")
    
    def upload_file(self, local_path: Path, remote_filename: str) -> bool:
        """
        Загружает файл на FTP сервер.
        
        Args:
            local_path: Локальный путь к файлу
            remote_filename: Имя файла на сервере
            
        Returns:
            True если успешно, False если ошибка
        """
        if not self.enabled:
            self.logger.warning("FTPUploader отключен, загрузка невозможна")
            return False
        
        if not local_path.exists():
            self.logger.error(f"Локальный файл не найден: {local_path}")
            return False
        
        try:
            # Создаем подключение
            if self.use_tls:
                ftp = FTP_TLS()
            else:
                ftp = FTP()
            
            ftp.connect(self.host, self.port, timeout=self.timeout)
            ftp.login(self.username, self.password)
            
            if self.use_tls:
                ftp.prot_p()  # Включаем защищенное соединение
            
            # Переходим в нужную директорию
            ftp.cwd(self.remote_base_path)
            
            # Загружаем файл
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_filename}', f)
            
            # Закрываем соединение
            ftp.quit()
            
            self.logger.info(f"Файл загружен на FTP: {remote_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки файла на FTP: {e}")
            return False
    
    def create_directory(self, directory_path: str) -> bool:
        """
        Создает директорию на FTP сервере.
        
        Args:
            directory_path: Путь к директории
            
        Returns:
            True если успешно, False если ошибка
        """
        if not self.enabled:
            return False
        
        try:
            if self.use_tls:
                ftp = FTP_TLS()
            else:
                ftp = FTP()
            
            ftp.connect(self.host, self.port, timeout=self.timeout)
            ftp.login(self.username, self.password)
            
            if self.use_tls:
                ftp.prot_p()
            
            # Создаем директорию (если не существует)
            try:
                ftp.mkd(directory_path)
                self.logger.info(f"Создана директория на FTP: {directory_path}")
            except Exception as e:
                # Директория уже может существовать
                self.logger.debug(f"Директория уже существует или ошибка: {e}")
            
            ftp.quit()
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания директории на FTP: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Тестирует подключение к FTP серверу.
        
        Returns:
            True если подключение успешно, False если ошибка
        """
        if not self.enabled:
            return False
        
        try:
            if self.use_tls:
                ftp = FTP_TLS()
            else:
                ftp = FTP()
            
            ftp.connect(self.host, self.port, timeout=self.timeout)
            ftp.login(self.username, self.password)
            
            # Получаем приветственное сообщение
            welcome_msg = ftp.getwelcome()
            self.logger.info(f"FTP подключение успешно: {welcome_msg[:50]}...")
            
            ftp.quit()
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка подключения к FTP: {e}")
            return False
    
    def __str__(self) -> str:
        """Строковое представление объекта"""
        status = "enabled" if self.enabled else "disabled"
        return f"FTPUploader({status}, host={self.host}, path={self.remote_base_path})"