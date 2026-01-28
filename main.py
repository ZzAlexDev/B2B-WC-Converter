"""
main.py
Основной скрипт конвертера B2B-WC-Converter
Координирует работу всех модулей для преобразования XLSX в CSV WooCommerce
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

# Добавляем корневую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты модулей обработки
from data_processors.xlsx_parser import parse_xlsx_file
from data_processors.description_builder import DescriptionBuilder
from data_processors.image_handler import ImageHandler
from data_processors.data_aggregator import DataAggregator
from output_managers.csv_exporter import CSVExporter
from config.settings import (
    INPUT_FILE, OUTPUT_FILE, IMAGES_DOWNLOAD_DIR,
    LOG_DIR, LOG_LEVEL, get_log_file_path, get_report_file_path
)


class B2BWCConverter:
    """
    Основной класс конвертера B2B в WooCommerce
    """
    
    def __init__(self):
        """
        Инициализация конвертера
        """
        # Настройка логирования
        self._setup_logging()
        
        # Инициализация обработчиков
        self.xlsx_parser = None
        self.description_builder = None
        self.image_handler = None
        self.data_aggregator = None
        self.csv_exporter = None
        
        # Статистика выполнения
        self.execution_stats = {
            'start_time': None,
            'end_time': None,
            'total_products': 0,
            'successful_products': 0,
            'failed_products': 0,
            'step_results': {},
            'errors': []
        }
        
        logger.info("=" * 60)
        logger.info("ИНИЦИАЛИЗАЦИЯ B2B-WC-CONVERTER")
        logger.info("=" * 60)
        logger.info(f"Входной файл: {INPUT_FILE}")
        logger.info(f"Выходной файл: {OUTPUT_FILE}")
        logger.info(f"Директория изображений: {IMAGES_DOWNLOAD_DIR}")
        logger.info(f"Уровень логирования: {LOG_LEVEL}")
    
    def _setup_logging(self):
        """
        Настройка системы логирования
        """
        global logger
        
        # Создаем директорию логов если не существует
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Получаем путь к файлу лога
        log_file = get_log_file_path()
        
        # Настраиваем формат логов
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Настраиваем базовую конфигурацию
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Логирование настроено. Файл лога: {log_file}")
    
    def run(self) -> bool:
        """
        Запуск полного процесса конвертации
        
        Returns:
            bool: Успешно ли выполнена конвертация
        """
        self.execution_stats['start_time'] = datetime.now()
        logger.info(f"Начало процесса конвертации: {self.execution_stats['start_time']}")
        
        try:
            # ШАГ 1: Парсинг XLSX файла
            parsed_products = self._step_parse_xlsx()
            if not parsed_products:
                logger.error("Парсинг XLSX не дал результатов. Процесс остановлен.")
                return False
            
            # ШАГ 2: Генерация описаний товаров
            products_with_descriptions = self._step_build_descriptions(parsed_products)
            
            # ШАГ 3: Обработка изображений товаров
            products_with_images = self._step_process_images(parsed_products)
            
            # ШАГ 4: Агрегация всех данных
            full_products = self._step_aggregate_data(
                parsed_products, 
                products_with_descriptions, 
                products_with_images
            )
            
            # ШАГ 5: Экспорт в CSV WooCommerce
            export_success = self._step_export_to_csv(full_products)
            
            # Завершение
            self.execution_stats['end_time'] = datetime.now()
            
            # Формирование отчета
            self._generate_report(export_success)
            
            return export_success
            
        except Exception as e:
            logger.error(f"Критическая ошибка в процессе конвертации: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            self.execution_stats['errors'].append(f"Критическая ошибка: {str(e)}")
            self.execution_stats['end_time'] = datetime.now()
            self._generate_report(False)
            
            return False
    
    def _step_parse_xlsx(self) -> List[Dict[str, Any]]:
        """
        Шаг 1: Парсинг XLSX файла
        
        Returns:
            List[Dict[str, Any]]: Парсированные товары
        """
        logger.info("\n" + "=" * 60)
        logger.info("ШАГ 1: ПАРСИНГ XLSX ФАЙЛА")
        logger.info("=" * 60)
        
        try:
            # Проверяем существование файла
            if not os.path.exists(INPUT_FILE):
                error_msg = f"Входной файл не найден: {INPUT_FILE}"
                logger.error(error_msg)
                self.execution_stats['errors'].append(error_msg)
                return []
            
            logger.info(f"Чтение файла: {INPUT_FILE}")
            
            # Используем функцию быстрого парсинга
            parsed_products, stats = parse_xlsx_file(INPUT_FILE)
            
            # Сохраняем статистику
            self.execution_stats['step_results']['xlsx_parsing'] = stats
            self.execution_stats['total_products'] = stats.get('total_rows', 0)
            
            logger.info(f"Парсинг завершен. Найдено товаров: {len(parsed_products)}")
            logger.info(f"Статистика: {stats}")
            
            if not parsed_products:
                logger.warning("Файл прочитан, но товары не найдены")
            
            return parsed_products
            
        except Exception as e:
            error_msg = f"Ошибка парсинга XLSX: {str(e)}"
            logger.error(error_msg)
            self.execution_stats['errors'].append(error_msg)
            return []
    
    def _step_build_descriptions(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Шаг 2: Генерация описаний товаров
        
        Args:
            products: Список товаров из парсера
            
        Returns:
            List[Dict[str, Any]]: Товары с описаниями
        """
        logger.info("\n" + "=" * 60)
        logger.info("ШАГ 2: ГЕНЕРАЦИЯ ОПИСАНИЙ ТОВАРОВ")
        logger.info("=" * 60)
        
        if not products:
            logger.warning("Нет товаров для генерации описаний")
            return []
        
        try:
            self.description_builder = DescriptionBuilder()
            logger.info(f"Начало генерации описаний для {len(products)} товаров")
            
            # Обрабатываем партию товаров
            products_with_descriptions = self.description_builder.process_batch(products)
            
            # Получаем статистику
            desc_stats = self.description_builder.get_stats()
            self.execution_stats['step_results']['description_building'] = desc_stats
            
            logger.info(f"Генерация описаний завершена: {desc_stats}")
            
            return products_with_descriptions
            
        except Exception as e:
            error_msg = f"Ошибка генерации описаний: {str(e)}"
            logger.error(error_msg)
            self.execution_stats['errors'].append(error_msg)
            
            # Возвращаем исходные товары без описаний
            return products
    
    def _step_process_images(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Шаг 3: Обработка изображений товаров
        
        Args:
            products: Список товаров
            
        Returns:
            List[Dict[str, Any]]: Товары с обработанными изображениями
        """
        logger.info("\n" + "=" * 60)
        logger.info("ШАГ 3: ОБРАБОТКА ИЗОБРАЖЕНИЙ ТОВАРОВ")
        logger.info("=" * 60)
        
        if not products:
            logger.warning("Нет товаров для обработки изображений")
            return []
        
        try:
            self.image_handler = ImageHandler(download_dir=IMAGES_DOWNLOAD_DIR)
            logger.info(f"Начало обработки изображений для {len(products)} товаров")
            logger.info(f"Изображения будут сохранены в: {IMAGES_DOWNLOAD_DIR}")
            
            # Обрабатываем изображения
            products_with_images = self.image_handler.process_batch(products)
            
            # Получаем статистику
            img_stats = self.image_handler.get_stats()
            self.execution_stats['step_results']['image_processing'] = img_stats
            
            logger.info(f"Обработка изображений завершена: {img_stats}")
            
            return products_with_images
            
        except Exception as e:
            error_msg = f"Ошибка обработки изображений: {str(e)}"
            logger.error(error_msg)
            self.execution_stats['errors'].append(error_msg)
            
            # Возвращаем товары без обработки изображений
            return products
    
    def _step_aggregate_data(self,
                           xlsx_products: List[Dict[str, Any]],
                           description_products: List[Dict[str, Any]],
                           images_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Шаг 4: Агрегация всех данных
        
        Args:
            xlsx_products: Товары из XLSX парсера
            description_products: Товары с описаниями
            images_products: Товары с изображениями
            
        Returns:
            List[Dict[str, Any]]: Полные агрегированные товары
        """
        logger.info("\n" + "=" * 60)
        logger.info("ШАГ 4: АГРЕГАЦИЯ ВСЕХ ДАННЫХ")
        logger.info("=" * 60)
        
        if not xlsx_products:
            logger.error("Нет товаров для агрегации")
            return []
        
        try:
            self.data_aggregator = DataAggregator()
            logger.info(f"Начало агрегации данных для {len(xlsx_products)} товаров")
            
            # Агрегируем данные
            full_products = self.data_aggregator.aggregate_batch_by_sku(
                xlsx_products=xlsx_products,
                description_products=description_products,
                images_products=images_products
            )
            
            # Получаем статистику и отчет
            agg_stats = self.data_aggregator.get_stats()
            agg_report = self.data_aggregator.get_summary_report()
            
            self.execution_stats['step_results']['data_aggregation'] = agg_stats
            
            logger.info(f"Агрегация данных завершена:")
            logger.info(agg_report)
            
            # Обновляем общую статистику
            self.execution_stats['successful_products'] = agg_stats.get('successfully_aggregated', 0)
            self.execution_stats['failed_products'] = agg_stats.get('failed_aggregation', 0)
            
            return full_products
            
        except Exception as e:
            error_msg = f"Ошибка агрегации данных: {str(e)}"
            logger.error(error_msg)
            self.execution_stats['errors'].append(error_msg)
            
            # В случае ошибки возвращаем хотя бы XLSX данные
            return xlsx_products
    
    def _step_export_to_csv(self, products: List[Dict[str, Any]]) -> bool:
        """
        Шаг 5: Экспорт в CSV WooCommerce
        
        Args:
            products: Агрегированные товары
            
        Returns:
            bool: Успешно ли экспортировано
        """
        logger.info("\n" + "=" * 60)
        logger.info("ШАГ 5: ЭКСПОРТ В CSV WOOCOMMERCE")
        logger.info("=" * 60)
        
        if not products:
            logger.error("Нет товаров для экспорта")
            return False
        
        try:
            self.csv_exporter = CSVExporter()
            logger.info(f"Начало экспорта {len(products)} товаров в CSV")
            logger.info(f"Выходной файл: {OUTPUT_FILE}")
            
            # Экспортируем в CSV
            export_success = self.csv_exporter.generate_csv(products)
            
            # Получаем статистику
            export_stats = self.csv_exporter.get_stats()
            self.execution_stats['step_results']['csv_export'] = export_stats
            
            if export_success:
                logger.info(f"Экспорт успешно завершен: {export_stats}")
                logger.info(f"CSV файл создан: {OUTPUT_FILE}")
                
                # Проверяем размер файла
                if os.path.exists(OUTPUT_FILE):
                    file_size = os.path.getsize(OUTPUT_FILE)
                    logger.info(f"Размер CSV файла: {file_size / 1024:.2f} KB")
            else:
                logger.error(f"Ошибка экспорта: {export_stats}")
            
            return export_success
            
        except Exception as e:
            error_msg = f"Ошибка экспорта в CSV: {str(e)}"
            logger.error(error_msg)
            self.execution_stats['errors'].append(error_msg)
            return False
    
    def _generate_report(self, success: bool):
        """
        Генерация итогового отчета
        
        Args:
            success: Общий успех операции
        """
        logger.info("\n" + "=" * 60)
        logger.info("ИТОГОВЫЙ ОТЧЕТ")
        logger.info("=" * 60)
        
        # Вычисляем общее время выполнения
        if self.execution_stats['start_time'] and self.execution_stats['end_time']:
            duration = self.execution_stats['end_time'] - self.execution_stats['start_time']
            self.execution_stats['duration'] = str(duration)
            
            logger.info(f"Общее время выполнения: {duration}")
        
        # Статистика по товарам
        logger.info(f"Всего товаров обработано: {self.execution_stats['total_products']}")
        logger.info(f"Успешно обработано: {self.execution_stats['successful_products']}")
        logger.info(f"Не удалось обработать: {self.execution_stats['failed_products']}")
        
        if self.execution_stats['total_products'] > 0:
            success_rate = (self.execution_stats['successful_products'] / self.execution_stats['total_products']) * 100
            logger.info(f"Процент успеха: {success_rate:.1f}%")
        
        # Ошибки
        if self.execution_stats['errors']:
            logger.warning(f"Всего ошибок: {len(self.execution_stats['errors'])}")
            for i, error in enumerate(self.execution_stats['errors'][:5], 1):
                logger.warning(f"  {i}. {error}")
            if len(self.execution_stats['errors']) > 5:
                logger.warning(f"  ... и еще {len(self.execution_stats['errors']) - 5} ошибок")
        
        # Результат
        if success:
            logger.info("✓ КОНВЕРТАЦИЯ УСПЕШНО ЗАВЕРШЕНА ✓")
        else:
            logger.error("✗ КОНВЕРТАЦИЯ ЗАВЕРШИЛАСЬ С ОШИБКАМИ ✗")
        
        # Сохраняем отчет в файл
        self._save_report_to_file(success)
    
    def _save_report_to_file(self, success: bool):
        """
        Сохранение отчета в файл
        
        Args:
            success: Общий успех операции
        """
        try:
            report_file = get_report_file_path()
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("ОТЧЕТ О КОНВЕРТАЦИИ B2B-WC-CONVERTER\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Дата выполнения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Общий результат: {'УСПЕХ' if success else 'ОШИБКА'}\n\n")
                
                if self.execution_stats.get('duration'):
                    f.write(f"Общее время выполнения: {self.execution_stats['duration']}\n")
                
                f.write(f"Всего товаров: {self.execution_stats['total_products']}\n")
                f.write(f"Успешно обработано: {self.execution_stats['successful_products']}\n")
                f.write(f"Не удалось обработать: {self.execution_stats['failed_products']}\n\n")
                
                if self.execution_stats['errors']:
                    f.write("ОШИБКИ:\n")
                    f.write("-" * 40 + "\n")
                    for i, error in enumerate(self.execution_stats['errors'], 1):
                        f.write(f"{i}. {error}\n")
                    f.write("\n")
                
                f.write("СТАТИСТИКА ПО ЭТАПАМ:\n")
                f.write("-" * 40 + "\n")
                
                for step_name, step_stats in self.execution_stats['step_results'].items():
                    f.write(f"\n{step_name.upper().replace('_', ' ')}:\n")
                    if isinstance(step_stats, dict):
                        for key, value in step_stats.items():
                            if key != 'errors' or (key == 'errors' and value):
                                f.write(f"  {key}: {value}\n")
                    else:
                        f.write(f"  {step_stats}\n")
            
            logger.info(f"Отчет сохранен в файл: {report_file}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")


def main():
    """
    Основная точка входа в программу
    """
    try:
        # Создаем и запускаем конвертер
        converter = B2BWCConverter()
        success = converter.run()
        
        # Возвращаем код завершения
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Процесс прерван пользователем")
        return 130
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)