# batch_processor.py - отдельный скрипт для обработки накопившихся файлов
from pathlib import Path
from config_manager import ConfigManager
from image_processor import ImageProcessor
from ftp_uploader import FTPUploader

def process_existing_images():
    """Обрабатывает уже скачанные изображения."""
    config = ConfigManager.from_directory("config/v2").settings
    
    processor = ImageProcessor(config)
    uploader = FTPUploader(config, use_env=True)
    
    # Директории из настроек
    input_dir = Path(config['paths']['local_image_download'])
    output_dir = Path(config['paths']['local_image_converted'])
    
    # Обработка
    processed = processor.batch_process(input_dir, pattern="*.jpg")
    
    # Загрузка на FTP
    if processed and uploader.ftp_enabled:
        uploader.upload_directory(output_dir, pattern="*.webp")
    
    return processed