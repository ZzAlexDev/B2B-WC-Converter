"""
ConverterV2 - главный класс-оркестратор для B2B-WC Converter v2.0.
Управляет всем процессом конвертации: чтение, обработка, экспорт.
"""
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

from .models import RawProduct, WooProduct, ProcessingStats
from .config_manager import ConfigManager
from .aggregator import Aggregator

logger = logging.getLogger(__name__)


class ConverterV2:
    """
    Главный класс конвертера.
    Управляет всем процессом преобразования CSV.
    """
    
    def __init__(self, config_path: str = "config/v2"):
        """
        Инициализирует конвертер.
        
        Args:
            config_path: Путь к папке с конфигурационными файлами
        """
        self.config_path = Path(config_path)
        self.config_manager: Optional[ConfigManager] = None
        self.aggregator: Optional[Aggregator] = None
        self.stats = ProcessingStats()
        
        self._setup_logging()
        self._load_configuration()
    
    def _setup_logging(self) -> None:
        """Настраивает логирование."""
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"converter_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger.info(f"Конвертер инициализирован, логи в {log_file}")
    
    def _load_configuration(self) -> None:
        """Загружает конфигурацию."""
        try:
            self.config_manager = ConfigManager.from_directory(str(self.config_path))
            self.aggregator = Aggregator(self.config_manager)
            logger.info("Конфигурация загружена успешно")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            raise
    
    def convert(self, input_path: str, output_path: Optional[str] = None, 
                skip_errors: bool = True) -> Dict[str, Any]:
        """
        Выполняет конвертацию CSV файла.
        
        Args:
            input_path: Путь к исходному CSV файлу
            output_path: Путь для выходного CSV файла
            skip_errors: Пропускать строки с ошибками
            
        Returns:
            Словарь с результатами конвертации
        """
        input_file = Path(input_path)
        
        if not input_file.exists():
            raise FileNotFoundError(f"Файл не найден: {input_file}")
        
        # Создаем имя выходного файла
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f"data/output/converted_{timestamp}.csv")
        else:
            output_file = Path(output_path)
        
        # Создаем папку для вывода
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Файл для ошибок
        errors_file = Path("data/logs/errors.csv")
        errors_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Начало конвертации: {input_file}")
        logger.info(f"Выходной файл: {output_file}")
        
        self.stats.start()
        
        try:
            # Читаем и обрабатываем CSV
            woo_products, errors = self._process_csv_file(
                input_file, errors_file, skip_errors
            )
            
            # Экспортируем в CSV
            self._export_to_csv(woo_products, output_file)
            
            self.stats.finish()
            
            result = {
                "processed": self.stats.processed,
                "skipped": self.stats.skipped,
                "errors": self.stats.errors,
                "output_path": str(output_file.absolute()),
                "log_path": str(errors_file.absolute()),
                "duration": self.stats.get_duration()
            }
            
            logger.info(f"Конвертация завершена: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при конвертации: {e}")
            raise
    
    def _process_csv_file(self, input_file: Path, errors_file: Path, 
                         skip_errors: bool) -> tuple[List[WooProduct], List[Dict]]:
        """
        Обрабатывает CSV файл.
        
        Args:
            input_file: Путь к входному файлу
            errors_file: Путь к файлу ошибок
            skip_errors: Пропускать строки с ошибками
            
        Returns:
            Кортеж (обработанные продукты, ошибки)
        """
        woo_products = []
        errors = []
        
        # Открываем файл ошибок для записи
        errors_writer = None
        
        try:
            # Читаем CSV файл
            with open(input_file, 'r', encoding='utf-8') as f:
                # Определяем разделитель
                sample = f.read(1024)
                f.seek(0)
                
                delimiter = ';' if ';' in sample else ','
                
                reader = csv.DictReader(f, delimiter=delimiter)
                self.stats.total_rows = sum(1 for _ in reader)
                f.seek(0)
                next(reader)  # Пропускаем заголовок
                
                logger.info(f"Файл: {input_file.name}, разделитель: '{delimiter}'")
                logger.info(f"Всего строк: {self.stats.total_rows}")
                
                # Создаем writer для ошибок
                errors_writer = csv.writer(
                    open(errors_file, 'w', encoding='utf-8', newline=''),
                    delimiter=delimiter
                )
                errors_writer.writerow(['row_number', 'error', 'raw_data'])
                
                # Обрабатываем строки
                for row_num, row in enumerate(reader, start=2):  # Начинаем с 2 (заголовок - строка 1)
                    try:
                        # Создаем RawProduct
                        raw_product = RawProduct.from_csv_row(row, row_num)
                        
                        # Валидация обязательных полей
                        if not self._validate_raw_product(raw_product):
                            self.stats.skipped += 1
                            error_msg = "Отсутствуют обязательные поля"
                            errors_writer.writerow([row_num, error_msg, str(row)])
                            errors.append({
                                'row': row_num,
                                'error': error_msg,
                                'data': row
                            })
                            continue
                        
                        # Обрабатываем через агрегатор
                        woo_product = self.aggregator.process_product(raw_product)
                        woo_products.append(woo_product)
                        self.stats.processed += 1
                        
                        # Логируем прогресс
                        if self.stats.processed % 100 == 0:
                            logger.info(f"Обработано: {self.stats.processed}/{self.stats.total_rows}")
                        
                    except Exception as e:
                        self.stats.errors += 1
                        error_msg = str(e)
                        logger.error(f"Ошибка в строке {row_num}: {error_msg}")
                        
                        if errors_writer:
                            errors_writer.writerow([row_num, error_msg, str(row)])
                        
                        errors.append({
                            'row': row_num,
                            'error': error_msg,
                            'data': row
                        })
                        
                        if not skip_errors:
                            raise
                        
        except Exception as e:
            logger.error(f"Ошибка при чтении файла: {e}")
            raise
        finally:
            if errors_writer:
                # Закрываем файл ошибок
                pass
        
        return woo_products, errors
    
    def _validate_raw_product(self, raw_product: RawProduct) -> bool:
        """
        Валидирует сырой продукт.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            True если продукт валиден
        """
        # Получаем обязательные поля из конфига
        required_fields = self.config_manager.get_setting(
            'validation.required_fields',
            ['Наименование', 'НС-код']
        )
        
        for field in required_fields:
            # Преобразуем имя поля для атрибута RawProduct
            field_name = field.replace(' ', '_').replace('-', '_')
            value = getattr(raw_product, field_name, "")
            
            if not value or not str(value).strip():
                logger.warning(f"Пропуск строки {raw_product.row_number}: "
                              f"отсутствует обязательное поле '{field}'")
                return False
        
        return True
    
    def _export_to_csv(self, woo_products: List[WooProduct], output_file: Path) -> None:
        """
        Экспортирует продукты в CSV файл.
        
        Args:
            woo_products: Список продуктов WooCommerce
            output_file: Путь к выходному файлу
        """
        if not woo_products:
            logger.warning("Нет продуктов для экспорта")
            return
        
        # Получаем заголовок из первого продукта
        header = woo_products[0].get_csv_header()
        
        # Добавляем все возможные поля из всех продуктов
        for product in woo_products[1:]:
            product_header = product.get_csv_header()
            for field in product_header:
                if field not in header:
                    header.append(field)
        
        # Сортируем заголовок для консистентности
        header.sort()
        
        logger.info(f"Экспорт {len(woo_products)} продуктов в {output_file}")
        logger.info(f"Колонок в CSV: {len(header)}")
        
        try:
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(
                    f, 
                    fieldnames=header,
                    delimiter=';',
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL
                )
                
                writer.writeheader()
                
                for product in woo_products:
                    row_data = product.to_woocommerce_dict()
                    
                    # Заполняем все колонки (даже если в продукте нет такого поля)
                    row = {}
                    for field in header:
                        row[field] = row_data.get(field, "")
                    
                    writer.writerow(row)
            
            logger.info(f"Экспорт завершен: {output_file}")
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте в CSV: {e}")
            raise
    
    def cleanup(self) -> None:
        """Очищает ресурсы."""
        if self.aggregator:
            self.aggregator.cleanup()
        logger.info("Ресурсы конвертера очищены")