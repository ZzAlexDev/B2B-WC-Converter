"""
CLI интерфейс для B2B-WC Converter
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.core.converter import B2BWCConverter, convert_xlsx_to_wc, convert_directory_to_wc
from src.utils.logger import setup_logger, get_logger


class CLIApp:
    """
    Консольное приложение для конвертера
    """
    
    def __init__(self):
        """Инициализация CLI приложения"""
        self.logger = get_logger()
        
    def run(self):
        """Запуск CLI приложения"""
        parser = self._create_parser()
        args = parser.parse_args()
        
        # Настраиваем логирование
        log_level = args.log_level.upper() if hasattr(args, 'log_level') else "INFO"
        setup_logger(
            name="b2b_wc_converter_cli",
            log_file=args.log_file if hasattr(args, 'log_file') else None,
            log_level=log_level,
            console_output=True
        )
        
        # Выполняем команду
        if hasattr(args, 'func'):
            args.func(args)
        else:
            parser.print_help()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Создание парсера аргументов"""
        parser = argparse.ArgumentParser(
            description="B2B-WC Converter - Конвертация каталогов товаров из XLSX в WooCommerce CSV",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Примеры использования:
  python -m interfaces.cli.cli_app convert data/input/catalog.xlsx
  python -m interfaces.cli.cli_app batch data/input/
  python -m interfaces.cli.cli_app convert data/input/catalog.xlsx --output data/output/
  python -m interfaces.cli.cli_app convert data/input/catalog.xlsx --skip-images --debug
            """
        )
        
        # Основные аргументы
        parser.add_argument(
            '--version',
            action='version',
            version='B2B-WC Converter v1.0.0'
        )
        
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Уровень логирования (по умолчанию: INFO)'
        )
        
        parser.add_argument(
            '--log-file',
            type=str,
            help='Путь к файлу логов'
        )
        
        # Субкоманды
        subparsers = parser.add_subparsers(
            title='команды',
            description='Доступные команды',
            dest='command',
            help='Дополнительная помощь по командам'
        )
        
        # Команда convert
        convert_parser = subparsers.add_parser(
            'convert',
            help='Конвертация одного XLSX файла'
        )
        convert_parser.add_argument(
            'input_file',
            type=str,
            help='Путь к XLSX файлу для конвертации'
        )
        convert_parser.add_argument(
            '-o', '--output',
            type=str,
            default='data/output',
            help='Директория для выходных файлов (по умолчанию: data/output)'
        )
        convert_parser.add_argument(
            '-c', '--config',
            type=str,
            default='config/settings.json',
            help='Путь к файлу конфигурации (по умолчанию: config/settings.json)'
        )
        convert_parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Пропустить скачивание изображений'
        )
        convert_parser.add_argument(
            '--download-images',
            action='store_true',
            help='Скачивать изображения (по умолчанию пропущено)'
        )
        convert_parser.add_argument(
            '--debug',
            action='store_true',
            help='Сохранять отладочную информацию в JSON'
        )
        convert_parser.add_argument(
            '--batch-size',
            type=int,
            help='Размер пачки для обработки (по умолчанию из конфига)'
        )
        convert_parser.set_defaults(func=self.convert_command)
        
        # Команда batch
        batch_parser = subparsers.add_parser(
            'batch',
            help='Конвертация всех XLSX файлов в директории'
        )
        batch_parser.add_argument(
            'input_dir',
            type=str,
            help='Директория с XLSX файлами'
        )
        batch_parser.add_argument(
            '-o', '--output',
            type=str,
            default='data/output',
            help='Директория для выходных файлов (по умолчанию: data/output)'
        )
        batch_parser.add_argument(
            '-c', '--config',
            type=str,
            default='config/settings.json',
            help='Путь к файлу конфигурации (по умолчанию: config/settings.json)'
        )
        batch_parser.add_argument(
            '--pattern',
            type=str,
            default='*.xlsx',
            help='Шаблон поиска файлов (по умолчанию: *.xlsx)'
        )
        batch_parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Пропустить скачивание изображений'
        )
        batch_parser.set_defaults(func=self.batch_command)
        
        # Команда validate
        validate_parser = subparsers.add_parser(
            'validate',
            help='Валидация XLSX файла без конвертации'
        )
        validate_parser.add_argument(
            'input_file',
            type=str,
            help='Путь к XLSX файлу для валидации'
        )
        validate_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Показать детальную информацию'
        )
        validate_parser.set_defaults(func=self.validate_command)
        
        # Команда config
        config_parser = subparsers.add_parser(
            'config',
            help='Показать текущую конфигурацию'
        )
        config_parser.add_argument(
            '-c', '--config-file',
            type=str,
            default='config/settings.json',
            help='Путь к файлу конфигурации'
        )
        config_parser.set_defaults(func=self.config_command)
        
        return parser
    
    def convert_command(self, args):
        """Обработка команды convert"""
        self.logger.info(f"🚀 Запуск конвертации файла: {args.input_file}")
        
        # Проверяем существование файла
        if not Path(args.input_file).exists():
            self.logger.error(f"Файл не найден: {args.input_file}")
            sys.exit(1)
        
        # Проверяем расширение
        if not args.input_file.lower().endswith(('.xlsx', '.xls')):
            self.logger.warning(f"Файл имеет нестандартное расширение: {args.input_file}")
        
        # Проверяем конфиг
        if not Path(args.config).exists():
            self.logger.warning(f"Файл конфигурации не найден: {args.config}")
            self.logger.info("Используются настройки по умолчанию")
        
        # Создаем выходную директорию
        Path(args.output).mkdir(parents=True, exist_ok=True)
        
        try:
            # Создаем конвертер
            converter = B2BWCConverter(args.config)
            
            # Запускаем конвертацию
            result = converter.convert_file(
                input_file=args.input_file,
                output_dir=args.output,
                batch_size=args.batch_size,
                skip_images_download=args.skip_images or not args.download_images,
                save_json_debug=args.debug
            )
            
            # Выводим результаты
            self._print_conversion_result(result)
            
            # Завершаем с кодом ошибки если нужно
            if not result.get("success", False):
                sys.exit(1)
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при конвертации: {e}", exc_info=True)
            sys.exit(1)
    
    def batch_command(self, args):
        """Обработка команды batch"""
        self.logger.info(f"📁 Запуск пакетной конвертации директории: {args.input_dir}")
        
        # Проверяем существование директории
        if not Path(args.input_dir).exists():
            self.logger.error(f"Директория не найдена: {args.input_dir}")
            sys.exit(1)
        
        # Проверяем конфиг
        if not Path(args.config).exists():
            self.logger.warning(f"Файл конфигурации не найден: {args.config}")
        
        # Создаем выходную директорию
        Path(args.output).mkdir(parents=True, exist_ok=True)
        
        try:
            # Создаем конвертер
            converter = B2BWCConverter(args.config)
            
            # Запускаем пакетную конвертацию
            results = converter.convert_directory(
                input_dir=args.input_dir,
                output_dir=args.output,
                file_pattern=args.pattern
            )
            
            # Выводим сводку
            self._print_batch_summary(results)
            
            # Проверяем были ли успешные конвертации
            successful_files = sum(1 for r in results if r.get("success", False))
            if successful_files == 0:
                self.logger.error("Ни один файл не был успешно сконвертирован")
                sys.exit(1)
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при пакетной конвертации: {e}", exc_info=True)
            sys.exit(1)
    
    def validate_command(self, args):
        """Обработка команды validate"""
        self.logger.info(f"🔍 Валидация файла: {args.input_file}")
        
        from src.loaders.xlsx_loader import XLSXLoader
        
        # Проверяем существование файла
        if not Path(args.input_file).exists():
            self.logger.error(f"Файл не найден: {args.input_file}")
            sys.exit(1)
        
        try:
            # Создаем загрузчик
            loader = XLSXLoader()
            
            # Загружаем файл
            result = loader.process_file(args.input_file, save_analysis=False)
            
            if not result:
                self.logger.error("Не удалось загрузить файл")
                sys.exit(1)
            
            # Выводим результаты валидации
            self._print_validation_result(result, args.detailed)
            
            if not result.get("is_valid", False):
                self.logger.warning("⚠️ Файл не прошел валидацию")
                sys.exit(1)
            else:
                self.logger.info("✅ Файл прошел валидацию")
                
        except Exception as e:
            self.logger.error(f"Ошибка при валидации: {e}", exc_info=True)
            sys.exit(1)
    
    def config_command(self, args):
        """Обработка команды config"""
        import json
        
        self.logger.info(f"⚙️  Загрузка конфигурации из: {args.config_file}")
        
        try:
            if Path(args.config_file).exists():
                with open(args.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Красиво выводим конфиг
                print(json.dumps(config, ensure_ascii=False, indent=2))
            else:
                self.logger.error(f"Файл конфигурации не найден: {args.config_file}")
                sys.exit(1)
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            sys.exit(1)
    
    def _print_conversion_result(self, result: dict):
        """Вывод результатов конвертации"""
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ КОНВЕРТАЦИИ")
        print("="*60)
        
        if result.get("success"):
            print("✅ Конвертация успешна!")
        else:
            print("❌ Конвертация не удалась")
        
        print(f"\n📁 Входной файл: {result.get('input_file', 'N/A')}")
        print(f"📈 Статистика:")
        print(f"   Обработано товаров: {result.get('products_processed', 0)}")
        print(f"   Успешно: {result.get('products_successful', 0)}")
        print(f"   Ошибок: {result.get('products_failed', 0)}")
        
        if result.get('products_processed', 0) > 0:
            success_rate = (result.get('products_successful', 0) / 
                          result.get('products_processed', 1)) * 100
            print(f"   Успешность: {success_rate:.1f}%")
        
        print(f"\n📂 Выходные файлы:")
        for output_file in result.get('output_files', []):
            print(f"   📄 {output_file}")
        
        if result.get('errors'):
            print(f"\n❌ Ошибки:")
            for error in result.get('errors', [])[:5]:  # Показываем только первые 5
                print(f"   • {error}")
            if len(result.get('errors', [])) > 5:
                print(f"   ... и еще {len(result.get('errors', [])) - 5} ошибок")
        
        if result.get('warnings'):
            print(f"\n⚠️  Предупреждения:")
            for warning in result.get('warnings', [])[:5]:
                print(f"   • {warning}")
            if len(result.get('warnings', [])) > 5:
                print(f"   ... и еще {len(result.get('warnings', [])) - 5} предупреждений")
        
        print("="*60)
    
    def _print_batch_summary(self, results: List[dict]):
        """Вывод сводки по пакетной конвертации"""
        if not results:
            print("Нет результатов для отображения")
            return
        
        print("\n" + "="*60)
        print("📈 СВОДКА ПАКЕТНОЙ КОНВЕРТАЦИИ")
        print("="*60)
        
        total_files = len(results)
        successful_files = sum(1 for r in results if r.get("success", False))
        total_processed = sum(r.get("products_processed", 0) for r in results)
        total_successful = sum(r.get("products_successful", 0) for r in results)
        
        print(f"📁 Файлов обработано: {total_files}")
        print(f"✅ Успешных файлов: {successful_files}/{total_files}")
        print(f"📊 Товаров обработано: {total_processed}")
        print(f"👍 Успешных товаров: {total_successful}")
        
        if total_processed > 0:
            success_rate = (total_successful / total_processed) * 100
            print(f"📈 Общая успешность: {success_rate:.1f}%")
        
        print(f"\n📂 Детали по файлам:")
        for i, result in enumerate(results, 1):
            status = "✅" if result.get("success", False) else "❌"
            processed = result.get("products_processed", 0)
            successful = result.get("products_successful", 0)
            filename = Path(result.get("input_file", "N/A")).name
            
            print(f"   {status} [{i:2d}] {filename}: {successful}/{processed} товаров")
        
        # Подсчет ошибок
        total_errors = sum(len(r.get("errors", [])) for r in results)
        if total_errors > 0:
            print(f"\n⚠️  Всего ошибок: {total_errors}")
        
        print("="*60)
    
    def _print_validation_result(self, result: dict, detailed: bool = False):
        """Вывод результатов валидации"""
        print("\n" + "="*60)
        print("🔍 РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
        print("="*60)
        
        print(f"📁 Файл: {result.get('file_path', 'N/A')}")
        print(f"✅ Валиден: {'Да' if result.get('is_valid', False) else 'Нет'}")
        print(f"📊 Строк: {result.get('total_products', 0)}")
        print(f"📋 Колонок: {len(result.get('dataframe', pd.DataFrame()).columns) if 'dataframe' in result else 'N/A'}")
        
        if detailed and 'analysis' in result:
            analysis = result['analysis']
            print(f"\n📈 Анализ данных:")
            print(f"   Всего строк: {analysis.get('total_rows', 0)}")
            print(f"   Колонок: {analysis.get('columns_count', 0)}")
            
            if 'columns_info' in analysis:
                print(f"\n📋 Информация по колонкам:")
                for col, info in list(analysis['columns_info'].items())[:10]:  # Показываем первые 10
                    null_percent = info.get('null_percent', 0)
                    status = "✅" if null_percent < 10 else "⚠️ " if null_percent < 50 else "❌"
                    print(f"   {status} {col}: {info.get('non_null', 0)}/{info.get('total', 0)} заполнено ({null_percent:.1f}% пусто)")
                
                if len(analysis['columns_info']) > 10:
                    print(f"   ... и еще {len(analysis['columns_info']) - 10} колонок")
        
        if result.get('messages'):
            print(f"\n📝 Сообщения:")
            for msg in result.get('messages', []):
                print(f"   • {msg}")
        
        print("="*60)


def main():
    """Точка входа CLI"""
    app = CLIApp()
    app.run()


if __name__ == "__main__":
    main()