"""
Загрузчик XLSX файлов
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

from src.utils.logger import get_logger, log_error, log_info, log_warning
from src.utils.validators import validate_required


class XLSXLoader:
    """
    Загрузчик и валидатор XLSX файлов
    """
    
    # Ожидаемые колонки (по вашему примеру)
    EXPECTED_COLUMNS = [
        "Наименование",
        "Артикул", 
        "Бренд",
        "Название категории",
        "Характеристики",
        "Изображение",
        "Видео",
        "Сопут.товар",
        "Аналоги",
        "Статья",
        "Чертежи",
        "Сертификаты",
        "Промоматериалы",
        "Инструкции",
        "Штрих код",
        "Цена",
        "НС-код",
        "Эксклюзив"
    ]
    
    # Обязательные колонки
    REQUIRED_COLUMNS = [
        "Наименование",
        "Артикул",
        "Название категории",
        "Характеристики",
        "Цена",
        "НС-код"
    ]
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        Инициализация загрузчика
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.logger = get_logger()
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Загрузка конфигурации"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации {config_path}: {e}")
            return {}
    
    def load_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Загрузка XLSX файла
        
        Args:
            file_path: Путь к XLSX файлу
        
        Returns:
            DataFrame с данными или None при ошибке
        """
        try:
            self.logger.info(f"Загрузка файла: {file_path}")
            
            # Проверяем существование файла
            if not Path(file_path).exists():
                self.logger.error(f"Файл не найден: {file_path}")
                return None
            
            # Загружаем файл
            # dtype=str - читаем все как текст
            df = pd.read_excel(
                file_path,
                dtype=str,  # Все колонки как строки
                na_filter=False  # Не заменяем пустые строки на NaN
            )
            
            self.logger.info(f"Файл загружен. Строк: {len(df)}, Колонок: {len(df.columns)}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки файла {file_path}: {e}", exc_info=True)
            return None
    
    def validate_structure(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Валидация структуры DataFrame
        
        Args:
            df: DataFrame для валидации
        
        Returns:
            Кортеж (валиден ли, список ошибок/предупреждений)
        """
        errors = []
        warnings = []
        
        if df is None or df.empty:
            errors.append("DataFrame пустой или None")
            return False, errors
        
        # Получаем фактические колонки
        actual_columns = list(df.columns)
        self.logger.info(f"Фактические колонки: {actual_columns}")
        
        # Проверяем обязательные колонки
        for required_col in self.REQUIRED_COLUMNS:
            if required_col not in actual_columns:
                errors.append(f"Отсутствует обязательная колонка: '{required_col}'")
        
        if errors:
            return False, errors
        
        # Проверяем ожидаемые колонки (предупреждения)
        for expected_col in self.EXPECTED_COLUMNS:
            if expected_col not in actual_columns:
                warnings.append(f"Отсутствует ожидаемая колонка: '{expected_col}'")
        
        # Проверяем наличие лишних колонок
        for actual_col in actual_columns:
            if actual_col not in self.EXPECTED_COLUMNS:
                warnings.append(f"Неожиданная колонка: '{actual_col}'")
        
        return True, warnings
    
    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Анализ данных в DataFrame
        
        Args:
            df: DataFrame для анализа
        
        Returns:
            Словарь с результатами анализа
        """
        analysis = {
            "total_rows": len(df),
            "columns_count": len(df.columns),
            "columns_info": {},
            "missing_data": {},
            "sample_data": {}
        }
        
        # Анализируем каждую колонку
        for column in df.columns:
            col_data = df[column]
            
            # Статистика по колонке
            non_null = col_data[col_data.notna() & (col_data != "")]
            null_count = len(df) - len(non_null)
            
            analysis["columns_info"][column] = {
                "total": len(df),
                "non_null": len(non_null),
                "null_count": null_count,
                "null_percent": (null_count / len(df)) * 100 if len(df) > 0 else 0,
                "sample_values": list(non_null.head(3).values) if len(non_null) > 0 else []
            }
            
            # Запоминаем колонки с пропусками
            if null_count > 0:
                analysis["missing_data"][column] = null_count
        
        # Примеры данных для отладки
        for column in ["Наименование", "Артикул", "Цена", "НС-код"]:
            if column in df.columns:
                sample = df[column].head(2).tolist()
                analysis["sample_data"][column] = sample
        
        return analysis
    
    def create_batches(self, df: pd.DataFrame, batch_size: int = 50) -> List[pd.DataFrame]:
        """
        Разделение DataFrame на пачки
        
        Args:
            df: Исходный DataFrame
            batch_size: Размер пачки
        
        Returns:
            Список DataFrame пачек
        """
        batches = []
        total_rows = len(df)
        
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i + batch_size].copy()
            batches.append(batch)
            
            self.logger.debug(f"Создана пачка {len(batches)}: строки {i+1}-{min(i+batch_size, total_rows)}")
        
        self.logger.info(f"Создано {len(batches)} пачек по {batch_size} строк")
        return batches
    
    def save_analysis_report(self, analysis: Dict[str, Any], output_path: str) -> bool:
        """
        Сохранение отчета анализа в JSON
        
        Args:
            analysis: Результаты анализа
            output_path: Путь для сохранения отчета
        
        Returns:
            True если успешно
        """
        try:
            # Создаем директорию если не существует
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Отчет анализа сохранен: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения отчета {output_path}: {e}")
            return False
    
    def process_file(self, file_path: str, save_analysis: bool = True) -> Optional[Dict[str, Any]]:
        """
        Полная обработка файла: загрузка, валидация, анализ
        
        Args:
            file_path: Путь к XLSX файлу
            save_analysis: Сохранять ли отчет анализа
        
        Returns:
            Словарь с результатами или None при ошибке
        """
        self.logger.info(f"Начата обработка файла: {file_path}")
        
        # 1. Загрузка файла
        df = self.load_file(file_path)
        if df is None:
            return None
        
        # 2. Валидация структуры
        is_valid, messages = self.validate_structure(df)
        
        if not is_valid:
            for error in messages:
                self.logger.error(f"Ошибка валидации: {error}")
            return None
        
        for warning in messages:
            self.logger.warning(f"Предупреждение: {warning}")
        
        # 3. Анализ данных
        analysis = self.analyze_data(df)
        
        # 4. Разделение на пачки
        batch_size = self.config.get("processing", {}).get("batch_size", 50)
        batches = self.create_batches(df, batch_size)
        analysis["batches_count"] = len(batches)
        
        # 5. Сохранение отчета
        if save_analysis:
            report_path = Path(file_path).parent / "analysis_report.json"
            self.save_analysis_report(analysis, str(report_path))
        
        # 6. Формирование результата
        result = {
            "file_path": file_path,
            "dataframe": df,
            "batches": batches,
            "analysis": analysis,
            "is_valid": is_valid,
            "messages": messages,
            "total_products": len(df)
        }
        
        self.logger.info(f"Обработка файла завершена. Товаров: {len(df)}")
        
        return result


# Функция для быстрого использования
def load_and_validate_xlsx(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Быстрая загрузка и валидация XLSX файла
    
    Args:
        file_path: Путь к XLSX файлу
    
    Returns:
        Результат обработки или None
    """
    loader = XLSXLoader()
    return loader.process_file(file_path)