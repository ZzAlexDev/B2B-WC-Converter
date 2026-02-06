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
        
        # Используем плоскую структуру конфига
        self.target_width = config.get('target_width', 1000)
        self.quality = config.get('quality', 85)
        self.add_noise = config.get('add_noise', True)
        self.noise_level = config.get('noise_level', 0.02)
        self.output_format = config.get('output_format', 'webp')
        self.max_file_size_mb = config.get('max_file_size_mb', 1.0)
        
        # Путь для сохранения
        if 'paths' in config and 'local_image_converted' in config['paths']:
            self.output_dir = Path(config['paths']['local_image_converted'])
        else:
            # Дефолтный путь
            self.output_dir = Path('data/downloads/converted/')
        
        # Создаем директорию
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ImageProcessor инициализирован: width={self.target_width}, "
                   f"quality={self.quality}, format={self.output_format}")
    
    def process_image(self, image_path: Path) -> Optional[Path]:
        """
        Обрабатывает изображение: изменяет размер, конвертирует формат, оптимизирует.
        """
        print(f"\n🛠️ ImageProcessor.process_image ДЕТАЛЬНО:")
        print(f"   Входной файл: {image_path}")
        
        try:
            # Открываем изображение
            with Image.open(image_path) as img:
                original_size = img.size
                print(f"   Исходный размер: {original_size}")
                print(f"   Формат: {img.format}")
                print(f"   Режим: {img.mode}")
                
                # Конвертируем RGBA в RGB если нужно
                if img.mode in ('RGBA', 'LA'):
                    print(f"   Конвертируем {img.mode} → RGB")
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img, mask=img.getchannel('A'))
                    img = background
                
                # Параметры из конфига
                target_width = self.config.get('target_width', 1000)
                target_height = self.config.get('target_height', 1000)
                quality = self.config.get('quality', 85)
                output_format = self.config.get('output_format', 'webp').lower()
                preserve_aspect_ratio = self.config.get('preserve_aspect_ratio', True)
                
                # КРИТИЧНО ВАЖНЫЕ НАСТРОЙКИ:
                upscale = self.config.get('upscale', False)  # По умолчанию False!
                force_resize = self.config.get('force_resize', False)  # Новая настройка
                
                print(f"   Target: {target_width}x{target_height}")
                print(f"   Сохранять пропорции: {preserve_aspect_ratio}")
                print(f"   Upscale разрешен: {upscale}")
                print(f"   Force resize: {force_resize}")
                
                # Определяем, нужно ли изменять размер
                original_width, original_height = original_size
                
                # 1. Если изображение больше target - уменьшаем
                # 2. Если изображение меньше target:
                #    - Если upscale=True - увеличиваем
                #    - Если force_resize=True - принудительно изменяем до target
                #    - Иначе оставляем как есть
                
                needs_resize = False
                new_width, new_height = original_width, original_height
                
                # Проверяем разные условия
                if original_width > target_width or original_height > target_height:
                    # Изображение больше target - уменьшаем
                    needs_resize = True
                    print(f"   📉 Изображение больше target - уменьшаем")
                    
                elif (original_width < target_width or original_height < target_height) and upscale:
                    # Изображение меньше target И upscale разрешен
                    needs_resize = True
                    print(f"   📈 Изображение меньше target - увеличиваем (upscale=True)")
                    
                elif force_resize:
                    # Принудительное изменение размера
                    needs_resize = True
                    print(f"   🔧 Принудительное изменение размера (force_resize=True)")
                
                # Если нужно изменить размер
                if needs_resize:
                    # Вычисляем новые размеры
                    if preserve_aspect_ratio:
                        # Сохраняем пропорции
                        ratio = min(
                            target_width / original_width,
                            target_height / original_height
                        )
                        new_width = int(original_width * ratio)
                        new_height = int(original_height * ratio)
                        
                        # Если upscale=False, не увеличиваем больше оригинала
                        if not upscale and ratio > 1:
                            print(f"   ⚠️ upscale=False, не увеличиваем изображение")
                            new_width, new_height = original_width, original_height
                            needs_resize = False
                    else:
                        # Меняем точно до target размеров
                        new_width, new_height = target_width, target_height
                    
                    print(f"   Новый размер: {new_width}x{new_height}")
                    
                    # Изменяем размер
                    if needs_resize and (new_width != original_width or new_height != original_height):
                        print(f"   🚀 Изменяем размер с {original_width}x{original_height} на {new_width}x{new_height}")
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    else:
                        print(f"   ⏭️ Размер не меняем")
                else:
                    print(f"   ⏭️ Размер не меняем (не соответствует условиям)")
                
                # Генерируем имя выходного файла
                output_filename = f"{image_path.stem}.{output_format}"
                output_path = self.output_dir / output_filename
                
                # Сохраняем с оптимизацией
                print(f"   Сохраняем как {output_format.upper()}...")
                
                save_params = {
                    'quality': quality,
                    'optimize': True
                }
                
                if output_format == 'webp':
                    save_params['method'] = 6  # Максимальное сжатие
                elif output_format == 'jpeg' or output_format == 'jpg':
                    save_params['progressive'] = True
                
                img.save(output_path, **save_params)
                
                # Проверяем размер файла
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                max_size_mb = self.config.get('max_file_size_mb', 1.0)
                
                print(f"   ✅ Обработано: {output_path.name} ({new_width}x{new_height}, {file_size_mb:.2f}MB)")
                
                if file_size_mb > max_size_mb:
                    print(f"   ⚠️ Файл превышает максимальный размер: {file_size_mb:.2f}MB > {max_size_mb}MB")
                    # Можно добавить дополнительное сжатие
                
                return output_path
                
        except Exception as e:
            print(f"   ❌ Ошибка обработки: {e}")
            import traceback
            traceback.print_exc()
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