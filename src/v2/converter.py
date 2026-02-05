"""
ConverterV2 - главный класс-оркестратор для B2B-WC Converter v2.0.
Управляет всем процессом конвертации: чтение, обработка, экспорт.
"""
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

from .models import RawProduct, WooProduct, ProcessingStats
from .config_manager import ConfigManager
from .aggregator import Aggregator
from .utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


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
        log_file = setup_logging()
        logger.info(f"Конвертер инициализирован, логи в {log_file}")
    
        
    
    def _load_configuration(self) -> None:
        """Загружает конфигурацию."""
        try:
            self.config_manager = ConfigManager.from_directory(str(self.config_path))
            self.aggregator = Aggregator(self.config_manager)
            logger.info("Конфигурация загружена успешно")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}", exc_info=True)  
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
            # Пробуем найти в папке input из настроек
            input_dir = Path(self.config_manager.get_setting('paths.input_catalog', 'data/input/'))
            alternative_path = input_dir / input_path
            if alternative_path.exists():
                input_file = alternative_path
            else:
                raise FileNotFoundError(f"Файл не найден: {input_path}")
        
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
            
            # Создаем writer для отфильтрованных товаров (опционально)
            filtered_writer = None
            log_filtered = self.config_manager.get_setting('filters.log_filtered', False)
            
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
                    
                    # Создаем writer для отфильтрованных товаров (если нужно)
                    if log_filtered:
                        filtered_file = Path("data/logs/filtered.csv")
                        filtered_file.parent.mkdir(parents=True, exist_ok=True)
                        filtered_writer = csv.writer(
                            open(filtered_file, 'w', encoding='utf-8', newline=''),
                            delimiter=delimiter
                        )
                        filtered_writer.writerow(['row_number', 'brand', 'category', 'reason', 'raw_data'])
                    
                    # Обрабатываем строки
                    for row_num, row in enumerate(reader, start=2):  # Начинаем с 2 (заголовок - строка 1)
                        try:
                            # Создаем RawProduct
                            raw_product = RawProduct.from_csv_row(row, row_num)
                            
                            # === ФИЛЬТРАЦИЯ ПО БРЕНДУ И КАТЕГОРИИ ===
                            should_process, filter_reason = self._should_process_product(raw_product)
                            if not should_process:
                                self.stats.skipped += 1
                                logger.debug(f"Пропуск строки {row_num}: {filter_reason}")
                                
                                # Записываем в лог фильтрации
                                if log_filtered and filtered_writer:
                                    filtered_writer.writerow([
                                        row_num,
                                        getattr(raw_product, 'Бренд', ''),
                                        getattr(raw_product, 'Название_категории', ''),
                                        filter_reason,
                                        str(row)
                                    ])
                                
                                continue  # Пропускаем эту строку
                            # === КОНЕЦ ФИЛЬТРАЦИИ ===
                            
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
                if filtered_writer:
                    # Закрываем файл фильтрации
                    pass
            
            return woo_products, errors
    
    def _validate_raw_product(self, raw_product: RawProduct) -> bool:
        """
        Валидирует сырой продукт.
        """
        required_fields = self.config_manager.get_setting(
            'validation.required_fields',
            ['Наименование', 'НС-код']
        )
        
        for field in required_fields:
            field_name = field.replace(' ', '_').replace('-', '_')
            value = getattr(raw_product, field_name, "")
            
            if not value or not str(value).strip():
                logger.warning(f"Пропуск строки {raw_product.row_number}: "
                            f"отсутствует обязательное поле '{field}'")
                return False
        
        # Гарантируем, что поля для фильтрации существуют
        if not hasattr(raw_product, 'Бренд'):
            raw_product.Бренд = ""
        if not hasattr(raw_product, 'Название_категории'):
            raw_product.Название_категории = ""
        
        return True
    
    
    def _should_process_product(self, raw_product: RawProduct) -> tuple[bool, str]:
        """
        Проверяет, нужно ли обрабатывать продукт на основе фильтров.
        
        Args:
            raw_product: Сырой продукт для проверки
            
        Returns:
            Кортеж (нужно_ли_обрабатывать, причина_пропуска)
        """
        # Получаем настройки фильтров
        filters_config = self.config_manager.get_setting('filters', {})
        
        # Если фильтрация отключена - обрабатываем все
        if not filters_config.get('enabled', False):
            return True, "Фильтрация отключена"
        
        # Извлекаем данные продукта
        brand = getattr(raw_product, 'Бренд', '').strip()
        category = getattr(raw_product, 'Название_категории', '').strip()
        
        # Получаем списки для фильтрации
        allowed_brands = filters_config.get('brands', [])
        allowed_categories = filters_config.get('categories', [])
        category_mode = filters_config.get('category_mode', 'exact')  # 'exact' для точного совпадения
        
        # Проверяем режим работы с пустыми значениями
        if not brand and not filters_config.get('include_empty_brand', False):
            return False, "Пустой бренд"
        
        if not category and not filters_config.get('include_empty_category', False):
            return False, "Пустая категория"
        
        # Если оба списка пустые - фильтрация не работает
        if not allowed_brands and not allowed_categories:
            return True, "Нет фильтров (списки пустые)"
        
        # Проверка бренда
        brand_allowed = brand in allowed_brands if allowed_brands else True
        brand_reason = f"бренд '{brand}' не в разрешенном списке" if not brand_allowed else ""
        
        # Проверка категории
        category_allowed = True
        category_reason = ""
        
        if allowed_categories:
            if category_mode == 'exact':
                # Точное совпадение всей строки
                category_allowed = category in allowed_categories
                if not category_allowed:
                    category_reason = f"категория '{category}' не найдена в списке"
            
            elif category_mode == 'partial':
                # Частичное совпадение
                category_allowed = any(
                    filter_cat.lower() in category.lower()
                    for filter_cat in allowed_categories
                )
                if not category_allowed:
                    category_reason = f"категория не содержит '{allowed_categories}'"
            
            else:  # 'any_level'
                # Разбиваем категорию на уровни
                category_levels = [level.strip() for level in category.split(' - ')]
                category_allowed = any(
                    filter_cat.strip().lower() == level.lower()
                    for level in category_levels
                    for filter_cat in allowed_categories
                )
                if not category_allowed:
                    category_reason = f"ни один уровень категории не совпадает"
        
        # Объединяем причины
        reasons = []
        if brand_reason:
            reasons.append(brand_reason)
        if category_reason:
            reasons.append(category_reason)
        
        # Режим AND/OR
        mode = filters_config.get('mode', 'AND').upper()
        
        if mode == 'AND':
            if brand_allowed and category_allowed:
                return True, "Соответствует фильтрам AND"
            return False, f"Не соответствует AND: {'; '.join(reasons)}"
        else:  # OR режим
            if brand_allowed or category_allowed:
                return True, "Соответствует фильтрам OR"
            return False, f"Не соответствует OR: {'; '.join(reasons)}"    
        


    
    def _export_to_csv(self, woo_products: List[WooProduct], output_file: Path) -> None:
        """
        Экспортирует продукты в CSV файл.
        """
        if not woo_products:
            logger.warning("Нет продуктов для экспорта")
            return
        
        # Получаем заголовок
        header = woo_products[0].get_csv_header()
        
        # Добавляем все возможные поля
        for product in woo_products[1:]:
            product_header = product.get_csv_header()
            for field in product_header:
                if field not in header:
                    header.append(field)
        
        logger.info(f"Экспорт {len(woo_products)} продуктов в {output_file}")
        
        try:                
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(
                    f, 
                    delimiter=';',
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,
                    escapechar='\\'
                )
                
                # 1. Пишем заголовок через writer
                writer.writerow(header)
                
                # 2. Пишем данные
                for i, product in enumerate(woo_products, 1):
                    row_data = product.to_woocommerce_dict()
                    
                    # ФИНАЛЬНАЯ ОЧИСТКА ВСЕХ СТРОКОВЫХ ПОЛЕЙ
                    cleaned_data = {}
                    for field, value in row_data.items():
                        if isinstance(value, str):
                            # Вариант A: Используем существующий HtmlRepair
                            # from .html_repair import HtmlRepair
                            # value = HtmlRepair.repair(value)
                            
                            # Вариант B: Или простая замена (если импорт не работает)
                            from html import unescape
                            value = unescape(value)
                            value = value.replace('&ndash;', '-').replace('&ndash ', '- ')
                            value = value.replace('&mdash;', '-').replace('&mdash ', '- ')
                            value = value.replace('&bull;', '•').replace('&bull ', '• ')
                            value = value.replace('&deg;', '°').replace('&deg ', '° ')
                            value = value.replace('&nbsp;', ' ')
                            value = value.replace('—', '-')
                            value = value.replace('\xa0', ' ')
                            
                        
                        cleaned_data[field] = value
                    
                    row_data = cleaned_data  # Используем очищенную версию
                    
                    # ДИАГНОСТИКА: проверяем результат
                    # print(f"Продукт {i}/{len(woo_products)}:")
                    for field in ['post_content', 'post_title', 'post_excerpt']:
                        if field in row_data:
                            val = row_data[field]
                            if isinstance(val, str):
                                contains_and = '&' in val
                                contains_ndash = 'ndash' in val.lower()
                                if contains_and or contains_ndash:
                                    # print(f"  ⚠️  {field}: содержит '&'? {contains_and}, содержит 'ndash'? {contains_ndash}")
                                    idx = val.find('&') if '&' in val else val.lower().find('ndash')
                                    # print(f"     Контекст: ...{repr(val[max(0, idx-30):idx+50])}...")
                    
                    # Формируем строку для CSV
                    row = []
                    for field in header:
                        value = row_data.get(field, "")
                        if value is None:
                            value = ""
                        row.append(str(value))
                    
                    writer.writerow(row)
                    
                    # Логируем прогресс
                    if i % 10 == 0:
                        logger.debug(f"Экспортировано {i}/{len(woo_products)} продуктов")
            
            logger.info(f"Экспорт завершен: {output_file}")
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте в CSV: {e}")
            raise


    
    def cleanup(self) -> None:
        """Очищает ресурсы."""
        if self.aggregator:
            self.aggregator.cleanup()
        logger.info("Ресурсы конвертера очищены")