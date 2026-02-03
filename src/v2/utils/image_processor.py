"""
image_processor.py - обработка изображений (конвертация, ресайз, шум)
"""
from PIL import Image, ImageFilter
import os
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Обработчик изображений: ресайз, шум, удаление метаданных."""
    
    def __init__(self, config: dict):
        self.config = config
        self.processing_config = config.get('image_processing', {})
        
    def process_image(self, input_path: Path) -> Optional[Path]:
        """
        Обрабатывает одно изображение.
        
        Returns:
            Path к обработанному файлу или None при ошибке
        """
        if not input_path.exists():
            logger.error(f"Файл не найден: {input_path}")
            return None
        
        try:
            # 1. Открываем изображение
            with Image.open(input_path) as img:
                # Конвертируем в RGB если нужно (для PNG с альфа-каналом)
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')
                
                # 2. Ресайз до target_width с сохранением пропорций
                target_width = self.processing_config.get('target_width', 1000)
                if img.width > target_width:
                    ratio = target_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                
                # 3. Добавляем шум (легкое размытие)
                if self.processing_config.get('add_noise', True):
                    noise_level = self.processing_config.get('noise_level', 0.02)
                    img = img.filter(ImageFilter.GaussianBlur(radius=noise_level))
                
                # 4. Определяем выходной путь
                output_dir = Path(self.config['paths']['local_image_converted'])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_format = self.processing_config.get('output_format', 'webp')
                output_path = output_dir / f"{input_path.stem}.{output_format}"
                
                # 5. Сохраняем с настройками качества БЕЗ метаданных
                save_kwargs = {
                    'quality': self.processing_config.get('quality', 85),
                    'optimize': True,
                }
                
                if output_format.lower() == 'webp':
                    save_kwargs['method'] = 6  # Более медленный, но лучшее качество
                
                # Ключевой момент: save() без exif удаляет метаданные
                img.save(output_path, **save_kwargs)
                
                # 6. Проверяем размер
                max_size_mb = self.processing_config.get('max_file_size_mb', 1.0)
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                
                if file_size_mb > max_size_mb:
                    logger.warning(f"Файл {output_path.name} слишком большой: {file_size_mb:.2f}MB")
                    # Можно добавить дополнительное сжатие
                
                logger.info(f"Обработано: {input_path.name} → {output_path.name} "
                           f"({img.width}x{img.height}, {file_size_mb:.2f}MB)")
                
                return output_path
                
        except Exception as e:
            logger.error(f"Ошибка обработки {input_path}: {e}")
            return None
    
    def batch_process(self, input_dir: Path, pattern: str = "*.jpg") -> list[Path]:
        """Обрабатывает все изображения в директории."""
        processed = []
        
        for img_file in input_dir.glob(pattern):
            result = self.process_image(img_file)
            if result:
                processed.append(result)
        
        logger.info(f"Обработано {len(processed)} из {len(list(input_dir.glob(pattern)))} изображений")
        return processed