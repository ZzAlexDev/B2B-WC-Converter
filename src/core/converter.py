"""
Главный класс конвертера - координатор всей системы
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from src.loaders.xlsx_loader import XLSXLoader
from src.processors.product_builder import ProductBuilder
from src.processors.wc_formatter import WCFormatter
from src.exporters.csv_exporter import CSVExporter
from src.core.models.product import Product
from src.utils.logger import get_logger, log_info, log_error, log_batch_progress


class B2BWCConverter:
    """
    Главный класс конвертера B2B → WooCommerce
    """
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        Инициализация конвертера
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.logger = get_logger()
        self.config = self._load_config(config_path)
        
        # Инициализируем компоненты
        self.loader = XLSXLoader(config_path)
        self.builder = ProductBuilder(self.config)
        self.formatter = WCFormatter(self.config)
        self.exporter = CSVExporter(self.config)
        
        # Статистика
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_files": 0,
            "total_products": 0,
            "successful_products": 0,
            "failed_products": 0,
            "exported_csv_files": 0
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Загрузка конфигурации"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации {config_path}: {e}")
            return {}
    
    def convert_file(
        self,
        input_file: str,
        output_dir: str = "data/output",
        batch_size: int = None,
        skip_images_download: bool = True,
        save_json_debug: bool = False
    ) -> Dict[str, Any]:
        """
        Конвертация одного XLSX файла
        
        Args:
            input_file: Путь к входному XLSX файлу
            output_dir: Директория для выходных файлов
            batch_size: Размер пачки для обработки (None = из конфига)
            skip_images_download: Пропустить скачивание изображений
            save_json_debug: Сохранять JSON для отладки
        
        Returns:
            Результаты конвертации
        """
        self.stats["start_time"] = datetime.now()
        self.stats["total_files"] += 1
        
        self.logger.info(f"🚀 Начало конвертации файла: {input_file}")
        
        results = {
            "input_file": input_file,
            "success": False,
            "products_processed": 0,
            "products_successful": 0,
            "products_failed": 0,
            "output_files": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # 1. Загрузка XLSX файла
            self.logger.info("📂 Загрузка XLSX файла...")
            load_result = self.loader.process_file(input_file, save_analysis=True)
            
            if not load_result or not load_result.get("is_valid"):
                results["errors"].append("Не удалось загрузить или валидировать XLSX файл")
                return results
            
            df = load_result["dataframe"]
            batches = load_result["batches"]
            
            self.logger.info(f"✅ Загружено {len(df)} товаров, разделено на {len(batches)} пачек")
            
            # 2. Обработка пачек
            all_products = []
            
            for batch_idx, batch_df in enumerate(batches):
                self.logger.info(f"🔨 Обработка пачки {batch_idx + 1}/{len(batches)}...")
                
                batch_products = self._process_batch(
                    batch_df=batch_df,
                    batch_idx=batch_idx,
                    skip_images_download=skip_images_download
                )
                
                all_products.extend(batch_products)
                
                # Логирование прогресса
                processed = len(all_products)
                total = len(df)
                percent = (processed / total) * 100
                self.logger.info(f"📊 Прогресс: {processed}/{total} ({percent:.1f}%)")
            
            # 3. Фильтруем успешные товары
            successful_products = [p for p in all_products if p is not None]
            failed_count = len(all_products) - len(successful_products)
            
            results["products_processed"] = len(all_products)
            results["products_successful"] = len(successful_products)
            results["products_failed"] = failed_count
            
            if not successful_products:
                results["errors"].append("Не удалось обработать ни одного товара")
                return results
            
            # 4. Экспорт в CSV
            self.logger.info("📤 Экспорт в CSV...")
            
            # Генерируем имя выходного файла
            input_filename = Path(input_file).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"wc_import_{input_filename}_{timestamp}.csv"
            csv_path = Path(output_dir) / csv_filename
            
            # Экспортируем
            export_result = self.exporter.export_products(
                successful_products,
                str(csv_path),
                include_headers=True
            )
            
            if export_result["exported"] > 0:
                results["output_files"].append(str(csv_path))
                results["success"] = True
                
                self.logger.info(f"✅ Экспорт завершен: {csv_path}")
                self.logger.info(f"📊 Статистика: {export_result['exported']} товаров экспортировано")
            else:
                results["errors"].append("Не удалось экспортировать товары в CSV")
            
            # 5. Сохранение JSON для отладки (опционально)
            if save_json_debug:
                debug_path = Path(output_dir) / f"debug_{input_filename}_{timestamp}.json"
                self._save_debug_data(successful_products, str(debug_path))
                results["output_files"].append(str(debug_path))
                self.logger.info(f"📋 JSON для отладки сохранен: {debug_path}")
            
            # 6. Сохранение отчета
            report_path = Path(output_dir) / f"report_{input_filename}_{timestamp}.json"
            self._save_conversion_report(results, str(report_path))
            results["output_files"].append(str(report_path))
            
            # 7. Обновление статистики
            self.stats["total_products"] += len(all_products)
            self.stats["successful_products"] += len(successful_products)
            self.stats["failed_products"] += failed_count
            self.stats["exported_csv_files"] += 1 if export_result["exported"] > 0 else 0
            
            self.logger.info(f"🎉 Конвертация завершена успешно!")
            
            return results
            
        except Exception as e:
            error_msg = f"Критическая ошибка конвертации: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)
            return results
        
        finally:
            self.stats["end_time"] = datetime.now()
    
    def _process_batch(
        self,
        batch_df,
        batch_idx: int,
        skip_images_download: bool = True
    ) -> List[Optional[Product]]:
        """
        Обработка одной пачки товаров
        
        Args:
            batch_df: DataFrame с данными пачки
            batch_idx: Индекс пачки
            skip_images_download: Пропустить скачивание изображений
        
        Returns:
            Список товаров (None для неудачных)
        """
        batch_products = []
        
        # Настройка парсера изображений если нужно
        if skip_images_download and hasattr(self.builder.parsers["images"], "skip_download"):
            self.builder.parsers["images"].skip_download = True
        
        # Обрабатываем каждую строку
        for row_idx, row in batch_df.iterrows():
            global_row_idx = batch_idx * len(batch_df) + row_idx + 1
            
            try:
                # Преобразуем строку в словарь
                row_dict = row.to_dict()
                
                # Собираем товар
                product = self.builder.build_from_row(row_dict, global_row_idx)
                
                batch_products.append(product)
                
                # Логирование прогресса внутри пачки
                if (row_idx + 1) % 10 == 0:
                    self.logger.debug(f"Пачка {batch_idx + 1}: обработано {row_idx + 1}/{len(batch_df)} строк")
                
            except Exception as e:
                self.logger.error(f"Ошибка обработки строки {global_row_idx}: {e}")
                batch_products.append(None)
                continue
        
        return batch_products
    
    def _save_debug_data(self, products: List[Product], output_path: str):
        """Сохранение отладочных данных в JSON"""
        try:
            debug_data = {
                "generated_at": datetime.now().isoformat(),
                "total_products": len(products),
                "products": []
            }
            
            for product in products[:10]:  # Сохраняем только первые 10 для отладки
                if product:
                    product_data = {
                        "id": product.id,
                        "name": product.name,
                        "sku": product.sku,
                        "price": product.price,
                        "category": product.category_hierarchy,
                        "brand": product.brand,
                        "wc_fields": product.wc_fields,
                        "main_attributes": product.main_attributes,
                        "has_images": len(product.images_local) > 0,
                        "description_length": len(product.description_final)
                    }
                    debug_data["products"].append(product_data)
            
            # Создаем директорию если не существует
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения отладочных данных: {e}")
    
    def _save_conversion_report(self, results: Dict[str, Any], output_path: str):
        """Сохранение отчета о конвертации"""
        try:
            report_data = {
                "conversion_report": {
                    "timestamp": datetime.now().isoformat(),
                    "duration_seconds": (self.stats["end_time"] - self.stats["start_time"]).total_seconds() 
                                       if self.stats["start_time"] and self.stats["end_time"] else 0,

                    "input_file": results.get("input_file", ""),
                    "success": results.get("success", False),
                    "statistics": {
                        "processed": results.get("products_processed", 0),
                        "successful": results.get("products_successful", 0),
                        "failed": results.get("products_failed", 0),
                        "success_rate": (results.get("products_successful", 0) / 
                                       results.get("products_processed", 1) * 100)
                    },
                    "output_files": results.get("output_files", []),
                    "errors": results.get("errors", []),
                    "warnings": results.get("warnings", [])
                },
                "system_stats": {
                    k: (v.isoformat() if isinstance(v, datetime) else v)
                    for k, v in self.get_stats().items()
                }
            }

            
            # Создаем директорию если не существует
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"📋 Отчет сохранен: {output_path}")
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения отчета: {e}")
    
    def convert_directory(
        self,
        input_dir: str,
        output_dir: str = "data/output",
        file_pattern: str = "*.xlsx"
    ) -> List[Dict[str, Any]]:
        """
        Конвертация всех XLSX файлов в директории
        
        Args:
            input_dir: Директория с XLSX файлами
            output_dir: Директория для выходных файлов
            file_pattern: Шаблон поиска файлов
        
        Returns:
            Список результатов для каждого файла
        """
        self.logger.info(f"📁 Конвертация всех файлов в директории: {input_dir}")
        
        # Поиск файлов
        input_path = Path(input_dir)
        if not input_path.exists():
            self.logger.error(f"Директория не существует: {input_dir}")
            return []
        
        xlsx_files = list(input_path.glob(file_pattern))
        
        if not xlsx_files:
            self.logger.warning(f"Не найдено XLSX файлов в {input_dir}")
            return []
        
        self.logger.info(f"Найдено файлов: {len(xlsx_files)}")
        
        # Конвертация каждого файла
        all_results = []
        
        for file_idx, xlsx_file in enumerate(xlsx_files, 1):
            self.logger.info(f"📄 Файл {file_idx}/{len(xlsx_files)}: {xlsx_file.name}")
            
            result = self.convert_file(
                input_file=str(xlsx_file),
                output_dir=output_dir,
                skip_images_download=True
            )
            
            all_results.append(result)
            
            # Пауза между файлами (чтобы не перегружать систему)
            if file_idx < len(xlsx_files):
                time.sleep(1)
        
        # Создание сводного отчета
        self._create_summary_report(all_results, output_dir)
        
        return all_results
    
    def _create_summary_report(self, all_results: List[Dict[str, Any]], output_dir: str):
        """Создание сводного отчета для нескольких файлов"""
        try:
            summary = {
                "summary_report": {
                    "generated_at": datetime.now().isoformat(),
                    "total_files": len(all_results),
                    "total_processed": sum(r.get("products_processed", 0) for r in all_results),
                    "total_successful": sum(r.get("products_successful", 0) for r in all_results),
                    "total_failed": sum(r.get("products_failed", 0) for r in all_results),
                    "successful_files": sum(1 for r in all_results if r.get("success", False)),
                    "failed_files": sum(1 for r in all_results if not r.get("success", True)),
                    "all_output_files": []
                },
                "file_details": []
            }
            
            for result in all_results:
                summary["file_details"].append({
                    "input_file": result.get("input_file", ""),
                    "success": result.get("success", False),
                    "processed": result.get("products_processed", 0),
                    "successful": result.get("products_successful", 0),
                    "failed": result.get("products_failed", 0),
                    "output_files": result.get("output_files", [])
                })
                
                summary["summary_report"]["all_output_files"].extend(
                    result.get("output_files", [])
                )
            
            # Рассчитываем проценты
            total_processed = summary["summary_report"]["total_processed"]
            total_successful = summary["summary_report"]["total_successful"]
            
            if total_processed > 0:
                summary["summary_report"]["success_rate"] = (total_successful / total_processed) * 100
            else:
                summary["summary_report"]["success_rate"] = 0
            
            # Сохраняем отчет
            report_path = Path(output_dir) / "conversion_summary.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📊 Сводный отчет сохранен: {report_path}")
            
            # Выводим сводку в консоль
            self.logger.info("=" * 60)
            self.logger.info("📈 СВОДКА КОНВЕРТАЦИИ:")
            self.logger.info(f"   Файлов обработано: {summary['summary_report']['total_files']}")
            self.logger.info(f"   Товаров обработано: {total_processed}")
            self.logger.info(f"   Товаров успешно: {total_successful}")
            self.logger.info(f"   Успешность: {summary['summary_report']['success_rate']:.1f}%")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания сводного отчета: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики работы конвертера"""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "duration_seconds": duration,
            "success_rate": (self.stats["successful_products"] / self.stats["total_products"] * 100 
                           if self.stats["total_products"] > 0 else 0)
        }
    
    def reset_stats(self):
        """Сброс статистики"""
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_files": 0,
            "total_products": 0,
            "successful_products": 0,
            "failed_products": 0,
            "exported_csv_files": 0
        }


# Функция для быстрого использования
def convert_xlsx_to_wc(
    input_file: str,
    output_dir: str = "data/output",
    config_path: str = "config/settings.json"
) -> bool:
    """
    Быстрая конвертация XLSX в WooCommerce CSV
    
    Args:
        input_file: Путь к XLSX файлу
        output_dir: Директория для выходных файлов
        config_path: Путь к конфигурации
    
    Returns:
        True если конвертация успешна
    """
    converter = B2BWCConverter(config_path)
    result = converter.convert_file(input_file, output_dir)
    return result.get("success", False)


def convert_directory_to_wc(
    input_dir: str,
    output_dir: str = "data/output",
    config_path: str = "config/settings.json",
    file_pattern: str = "*.xlsx"
) -> List[Dict[str, Any]]:
    """
    Быстрая конвертация всех XLSX файлов в директории
    
    Args:
        input_dir: Директория с XLSX файлами
        output_dir: Директория для выходных файлов
        config_path: Путь к конфигурации
        file_pattern: Шаблон поиска файлов
    
    Returns:
        Список результатов для каждого файла
    """
    converter = B2BWCConverter(config_path)
    return converter.convert_directory(input_dir, output_dir, file_pattern)