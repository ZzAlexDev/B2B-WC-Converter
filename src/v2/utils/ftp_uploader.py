"""
ftp_uploader.py - загрузка файлов на FTP сервер
"""
from ftplib import FTP, FTP_TLS
import os
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv  # pip install python-dotenv

logger = logging.getLogger(__name__)


class FTPUploader:
    """Загрузчик файлов на FTP/FTPS сервер."""
    
    def __init__(self, config: dict, use_env: bool = True):
        self.config = config
        
        if use_env:
            load_dotenv()
            self.ftp_config = {
                'host': os.getenv('FTP_HOST'),
                'username': os.getenv('FTP_USERNAME'),
                'password': os.getenv('FTP_PASSWORD'),
                'port': int(os.getenv('FTP_PORT', 21)),
                'use_ftps': os.getenv('FTP_USE_FTPS', 'false').lower() == 'true'
            }
        else:
            self.ftp_config = config.get('ftp', {})
        
        self.remote_base_path = config['paths']['ftp_remote_path']
    
    def connect(self) -> Optional[FTP]:
        """Устанавливает соединение с FTP сервером."""
        try:
            if self.ftp_config.get('use_ftps'):
                ftp = FTP_TLS()
                ftp.connect(
                    host=self.ftp_config['host'],
                    port=self.ftp_config.get('port', 21)
                )
                ftp.login(
                    user=self.ftp_config['username'],
                    passwd=self.ftp_config['password']
                )
                ftp.prot_p()  # Включаем защищенный канал
            else:
                ftp = FTP()
                ftp.connect(
                    host=self.ftp_config['host'],
                    port=self.ftp_config.get('port', 21)
                )
                ftp.login(
                    user=self.ftp_config['username'],
                    passwd=self.ftp_config['password']
                )
            
            logger.info(f"Подключились к FTP: {self.ftp_config['host']}")
            return ftp
            
        except Exception as e:
            logger.error(f"Ошибка подключения к FTP: {e}")
            return None
    
    def upload_file(self, local_path: Path, remote_filename: str) -> bool:
        """
        Загружает один файл на FTP.
        
        Returns:
            True если успешно
        """
        ftp = self.connect()
        if not ftp:
            return False
        
        try:
            # Переходим в нужную директорию (создаем если нет)
            remote_dirs = self.remote_base_path.strip('/').split('/')
            for directory in remote_dirs:
                try:
                    ftp.cwd(directory)
                except:
                    ftp.mkd(directory)
                    ftp.cwd(directory)
            
            # Загружаем файл
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_filename}', f)
            
            logger.info(f"Загружено: {remote_filename} ({local_path.stat().st_size / 1024:.1f} KB)")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки {local_path}: {e}")
            return False
            
        finally:
            ftp.quit()
    
    def upload_directory(self, local_dir: Path, pattern: str = "*.webp") -> dict:
        """
        Загружает все файлы из директории.
        
        Returns:
            Словарь {filename: success}
        """
        results = {}
        
        for file_path in local_dir.glob(pattern):
            success = self.upload_file(file_path, file_path.name)
            results[file_path.name] = success
        
        successful = sum(1 for v in results.values() if v)
        logger.info(f"Загружено {successful}/{len(results)} файлов")
        
        return results