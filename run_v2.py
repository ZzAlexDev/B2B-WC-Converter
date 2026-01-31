"""
Точка входа (CLI) для B2B-WC Converter v2.0
"""
import argparse
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / "src"))

from v2.converter import ConverterV2
from v2.config_manager import ConfigManager


def main():
    """Основная функция CLI."""
    parser = argparse.ArgumentParser(
        description="Конвертер CSV для импорта в WooCommerce (v2.0)"
    )
    
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Путь к исходному CSV файлу"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        help="Путь для выходного CSV файла (по умолчанию: data/output/output_<timestamp>.csv)"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        default="config/v2",
        help="Путь к папке с конфигурационными файлами"
    )
    
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Пропускать строки с ошибками"
    )
    
    args = parser.parse_args()
    
    try:
        # Инициализируем конвертер
        converter = ConverterV2(config_path=args.config)
        
        # Запускаем конвертацию
        result = converter.convert(
            input_path=args.input,
            output_path=args.output,
            skip_errors=args.skip_errors
        )
        
        print(f"✅ Конвертация завершена успешно!")
        print(f"   Обработано товаров: {result['processed']}")
        print(f"   Пропущено товаров: {result['skipped']}")
        print(f"   Выходной файл: {result['output_path']}")
        print(f"   Лог ошибок: {result['log_path']}")
        
    except Exception as e:
        print(f"❌ Ошибка при конвертации: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()