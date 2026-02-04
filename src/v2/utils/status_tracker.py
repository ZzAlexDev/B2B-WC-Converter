"""
status_tracker.py - отслеживание состояния обработки файлов
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

class ImageStatusTracker:
    """Отслеживает состояние обработки изображений."""
    
    def __init__(self, status_file: str = "data/status/image_status.json"):
        self.status_file = Path(status_file)
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_data = self._load_status()
    
    def _load_status(self) -> Dict:
        """Загружает статус из файла."""
        if self.status_file.exists():
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "images": {}
        }
    
    def _save_status(self):
        """Сохраняет статус в файл."""
        self.status_data["last_updated"] = datetime.now().isoformat()
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status_data, f, indent=2, ensure_ascii=False)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Вычисляет хеш файла для отслеживания изменений."""
        if not file_path.exists():
            return ""
        
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def get_image_status(self, ns_code: str, slug: str, index: int) -> Dict:
        """Получает статус конкретного изображения."""
        key = f"{ns_code}-{slug}-{index+1}"
        return self.status_data["images"].get(key, {
            "downloaded": False,
            "processed": False,
            "uploaded": False,
            "original_hash": "",
            "processed_hash": "",
            "last_downloaded": None,
            "last_processed": None,
            "last_uploaded": None
        })
    
    def mark_downloaded(self, ns_code: str, slug: str, index: int, file_path: Path):
        """Отмечает файл как скачанный."""
        key = f"{ns_code}-{slug}-{index}"
        
        self.status_data["images"][key] = {
            "downloaded": True,
            "downloaded_path": str(file_path),
            "original_hash": self._get_file_hash(file_path),
            "last_downloaded": datetime.now().isoformat(),
            "processed": False,
            "uploaded": False,
            "last_processed": None,
            "last_uploaded": None
        }
        self._save_status()
    
    def mark_processed(self, ns_code: str, slug: str, index: int, original_path: Path, processed_path: Path):
        """Отмечает файл как обработанный."""
        key = f"{ns_code}-{slug}-{index}"
        
        if key not in self.status_data["images"]:
            self.status_data["images"][key] = {}
        
        self.status_data["images"][key].update({
            "processed": True,
            "processed_path": str(processed_path),
            "processed_hash": self._get_file_hash(processed_path),
            "last_processed": datetime.now().isoformat()
        })
        self._save_status()
    
    def mark_uploaded(self, ns_code: str, slug: str, index: int, file_path: Path):
        """Отмечает файл как загруженный на FTP."""
        key = f"{ns_code}-{slug}-{index}"
        
        if key not in self.status_data["images"]:
            self.status_data["images"][key] = {}
        
        self.status_data["images"][key].update({
            "uploaded": True,
            "last_uploaded": datetime.now().isoformat()
        })
        self._save_status()
    
    def needs_processing(self, ns_code: str, slug: str, index: int, file_path: Path) -> bool:
        """Проверяет, нужно ли обрабатывать файл."""
        status = self.get_image_status(ns_code, slug, index)
        
        # Если файл не скачан или не существует
        if not status["downloaded"] or not file_path.exists():
            return True
        
        # Если файл изменен (хеш не совпадает)
        current_hash = self._get_file_hash(file_path)
        if current_hash != status.get("original_hash", ""):
            return True
        
        # Если еще не обработан
        if not status.get("processed", False):
            return True
        
        # Если изменились настройки обработки (можно добавить хеш настроек)
        return False
    
    def needs_upload(self, ns_code: str, slug: str, index: int) -> bool:
        """Проверяет, нужно ли загружать файл на FTP."""
        status = self.get_image_status(ns_code, slug, index)
        
        # Если не обработан, нечего загружать
        if not status.get("processed", False):
            return False
        
        # Если еще не загружено
        if not status.get("uploaded", False):
            return True
        
        # Если файл изменился после последней загрузки
        processed_path = Path(status.get("processed_path", ""))
        if processed_path.exists():
            current_hash = self._get_file_hash(processed_path)
            if current_hash != status.get("processed_hash", ""):
                return True
        
        return False