"""
Экспортер в CSV для WooCommerce
"""

import csv
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.core.models.product import Product
from src.processors.wc_formatter import WCFormatter
from src.utils.logger import get_logger, log_info, log_error
from src.utils.file_utils import ensure_dir_exists


class CSVExporter:
    """
    Экспортер товаров в CSV для WooCommerce
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация экспортера
        
        Args:
            config: Конфигурация из settings.json
        """
        self.logger = get_logger()
        self.config = config or {}
        self.formatter = WCFormatter(config)
    
    def export_products(
        self,
        products: List[Product],
        output_path: str,
        include_headers: bool = True,
        encoding: str = "utf-8-sig"  # UTF-8 with BOM для Excel
    ) -> Dict[str, Any]:
        """
        Экспорт товаров в CSV файл
        
        Args:
            products: Список товаров для экспорта
            output_path: Путь для сохранения CSV
            include_headers: Включать ли заголовки
            encoding: Кодировка файла
        
        Returns:
            Словарь с результатами экспорта
        """
        self.logger.info(f"📤 Начало экспорта {len(products)} товаров в {output_path}")
        
        results = {
            "total_products": len(products),
            "exported": 0,
            "failed": 0,
            "errors": [],
            "output_path": output_path,
            "file_size": 0
        }
        
        if not products:
            results["errors"].append("Нет товаров для экспорта")
            return results
        
        try:
            # 1. Форматируем товары для WC
            formatted_rows = self.formatter.format_products_batch(products)
            
            if not formatted_rows:
                results["errors"].append("Не удалось отформатировать товары")
                return results
            
            # 2. Получаем заголовки
            headers = self.formatter.get_csv_headers(products)
            
            # 3. Создаем директорию если не существует
            output_dir = Path(output_path).parent
            ensure_dir_exists(str(output_dir))
            
            # 4. Записываем CSV файл
            with open(output_path, 'w', newline='', encoding=encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers, delimiter=',', quotechar='"')
                
                if include_headers:
                    writer.writeheader()
                
                for row in formatted_rows:
                    try:
                        # Создаем строку только с нужными полями
                        row_data = {field: row.get(field, "") for field in headers}
                        writer.writerow(row_data)
                        results["exported"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"Ошибка записи строки: {str(e)}")
                        self.logger.error(f"Ошибка записи в CSV: {e}")
            
            # 5. Получаем размер файла
            file_size = Path(output_path).stat().st_size
            results["file_size"] = file_size
            
            # 6. Логирование успеха
            log_info(f"✅ Экспорт завершен: {results['exported']}/{results['total_products']} товаров")
            log_info(f"📄 Файл: {output_path} ({file_size / 1024:.1f} KB)")
            
            # 7. Сохраняем отчет об экспорте
            self._save_export_report(results, output_path)
            
            return results
            
        except Exception as e:
            error_msg = f"Критическая ошибка экспорта: {str(e)}"
            results["errors"].append(error_msg)
            log_error(error_msg, exc_info=True)
            return results
    
    def _save_export_report(self, results: Dict[str, Any], csv_path: str):
        """
        Сохранение отчета об экспорте
        
        Args:
            results: Результаты экспорта
            csv_path: Путь к CSV файлу
        """
        try:
            report_path = Path(csv_path).with_suffix('.report.json')
            
            report_data = {
                "export_date": datetime.now().isoformat(),
                "csv_file": str(csv_path),
                "results": results,
                "summary": {
                    "success_rate": (results["exported"] / results["total_products"] * 100 
                                   if results["total_products"] > 0 else 0),
                    "errors_count": len(results["errors"])
                }
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📋 Отчет экспорта сохранен: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения отчета: {e}")
    
    def validate_csv(self, csv_path: str, check_required: bool = True) -> Dict[str, Any]:
        """
        Валидация CSV файла перед импортом в WooCommerce
        
        Args:
            csv_path: Путь к CSV файлу
            check_required: Проверять обязательные поля
        
        Returns:
            Результаты валидации
        """
        validation = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "row_count": 0,
            "missing_required": [],
            "sample_data": {}
        }
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                if not rows:
                    validation["errors"].append("CSV файл пустой")
                    return validation
                
                validation["row_count"] = len(rows)
                
                # Проверяем обязательные поля
                if check_required:
                    required_fields = ["post_title", "sku", "regular_price", "post_content"]
                    first_row = rows[0]
                    
                    for field in required_fields:
                        if field not in first_row or not first_row.get(field, "").strip():
                            validation["missing_required"].append(field)
                    
                    if validation["missing_required"]:
                        validation["errors"].append(
                            f"Отсутствуют обязательные поля: {validation['missing_required']}"
                        )
                
                # Сохраняем пример данных
                if rows:
                    validation["sample_data"] = {
                        "headers": list(rows[0].keys()),
                        "first_row": {k: v[:100] + "..." if len(str(v)) > 100 else v 
                                     for k, v in rows[0].items() if k in required_fields}
                    }
                
                # Если нет ошибок - файл валиден
                if not validation["errors"]:
                    validation["is_valid"] = True
                    validation["warnings"].append(f"CSV содержит {len(rows)} строк")
                
                return validation
                
        except Exception as e:
            validation["errors"].append(f"Ошибка чтения CSV: {str(e)}")
            return validation
    
    def export_to_multiple_files(
        self,
        products: List[Product],
        base_output_path: str,
        max_rows_per_file: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Экспорт в несколько CSV файлов (для больших каталогов)
        
        Args:
            products: Список товаров
            base_output_path: Базовый путь для файлов
            max_rows_per_file: Максимальное количество строк в файле
        
        Returns:
            Список результатов для каждого файла
        """
        all_results = []
        
        # Разделяем товары на пачки
        total_products = len(products)
        num_files = (total_products + max_rows_per_file - 1) // max_rows_per_file
        
        self.logger.info(f"📦 Разделение {total_products} товаров на {num_files} файлов")
        
        for i in range(num_files):
            start_idx = i * max_rows_per_file
            end_idx = min((i + 1) * max_rows_per_file, total_products)
            
            batch = products[start_idx:end_idx]
            
            # Генерируем имя файла с номером
            base_path = Path(base_output_path)
            file_name = f"{base_path.stem}_part{i+1:02d}{base_path.suffix}"
            file_path = base_path.parent / file_name
            
            # Экспортируем пачку
            self.logger.info(f"Экспорт пачки {i+1}: товары {start_idx+1}-{end_idx}")
            result = self.export_products(batch, str(file_path))
            all_results.append(result)
        
        # Создаем суммарный отчет
        self._create_summary_report(all_results, base_output_path)
        
        return all_results
    
    def _create_summary_report(self, all_results: List[Dict[str, Any]], base_path: str):
        """Создание суммарного отчета для нескольких файлов"""
        try:
            summary = {
                "total_files": len(all_results),
                "total_products": sum(r.get("total_products", 0) for r in all_results),
                "total_exported": sum(r.get("exported", 0) for r in all_results),
                "total_failed": sum(r.get("failed", 0) for r in all_results),
                "files": [],
                "generated_at": datetime.now().isoformat()
            }
            
            for i, result in enumerate(all_results):
                summary["files"].append({
                    "file_index": i + 1,
                    "output_path": result.get("output_path", ""),
                    "exported": result.get("exported", 0),
                    "file_size": result.get("file_size", 0)
                })
            
            report_path = Path(base_path).parent / "export_summary.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📊 Сводный отчет сохранен: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания сводного отчета: {e}")


# Функции для быстрого использования
def export_products_to_csv(
    products: List[Product],
    output_path: str,
    config: Dict[str, Any] = None
) -> bool:
    """
    Быстрый экспорт товаров в CSV
    
    Args:
        products: Список товаров
        output_path: Путь для сохранения
        config: Конфигурация
    
    Returns:
        True если успешно
    """
    exporter = CSVExporter(config)
    result = exporter.export_products(products, output_path)
    return result["exported"] > 0 and len(result["errors"]) == 0


def validate_csv_file(csv_path: str) -> Dict[str, Any]:
    """
    Быстрая валидация CSV файла
    
    Args:
        csv_path: Путь к CSV файлу
    
    Returns:
        Результаты валидации
    """
    exporter = CSVExporter()
    return exporter.validate_csv(csv_path)