"""
SpecsHandler - обработчик характеристик для B2B-WC Converter v2.0.
Обрабатывает: вес, габариты, атрибуты фильтров из поля "Характеристики".
"""
import re
from typing import Dict, Any, List, Tuple
import logging

from .base_handler import BaseHandler

# Используем относительные импорты
try:
    from ..models import RawProduct
    from ..config_manager import ConfigManager
except ImportError:
    from models import RawProduct
    from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class SpecsHandler(BaseHandler):
    """
    Обработчик характеристик товара.
    Парсит строку характеристик, извлекает вес/габариты и атрибуты WooCommerce.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует SpecsHandler.
        
        Args:
            config_manager: Менеджер конфигураций
        """
        super().__init__(config_manager)
        
        # Кэш для разобранных характеристик
        self.specs_cache: Dict[str, Dict[str, str]] = {}
    
    def process(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает характеристики товара.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полями weight, height, width, length и атрибутами
        """
        result = {}
        
        # 1. Парсим характеристики
        specs = self._parse_specifications(raw_product.Характеристики)
        
        # 2. Обрабатываем стандартные поля (вес, габариты)
        result.update(self._process_standard_fields(specs))
        
        # 3. Обрабатываем атрибуты WooCommerce
        result.update(self._process_woocommerce_attributes(specs))
        
        # 4. Сохраняем все характеристики в meta-поле для справки
        if specs:
            result["meta:все_характеристики"] = " | ".join(
                [f"{k}: {v}" for k, v in specs.items()]
            )
        
        logger.debug(f"SpecsHandler обработал продукт {raw_product.НС_код}: "
                    f"{len(specs)} характеристик, {len(result)} полей")
        return result
    
    def _parse_specifications(self, specs_string: str) -> Dict[str, str]:
        """
        Парсит строку характеристик формата "Ключ: Значение / Ключ: Значение".
        
        Args:
            specs_string: Строка характеристик
            
        Returns:
            Словарь характеристик {ключ: значение}
        """
        if not specs_string or not specs_string.strip():
            return {}
        
        specs = {}
        string = specs_string.strip()
        
        # Разные разделители в строке
        # Форматы: "Ключ: Значение / Ключ: Значение" или "Ключ: Значение, Ключ: Значение"
        # Сначала нормализуем разделители
        string = string.replace(';', '/').replace(',', '/')
        
        # Разбиваем по "/"
        parts = [part.strip() for part in string.split('/') if part.strip()]
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key and value:
                    # Нормализуем ключ (убираем лишние пробелы, приводим к стандартному виду)
                    normalized_key = self._normalize_spec_key(key)
                    specs[normalized_key] = value
        
        return specs
    
    def _normalize_spec_key(self, key: str) -> str:
        """
        Нормализует ключ характеристики для сопоставления с конфигом.
        
        Args:
            key: Исходный ключ
            
        Returns:
            Нормализованный ключ
        """
        # Убираем лишние пробелы
        key = key.strip()
        
        # Приводим к нижнему регистру для сравнения
        key_lower = key.lower()
        
        # Сопоставляем с ключами из конфига
        standard_fields = self.config_manager.attribute_mapping.get("standard_fields", {})
        woocommerce_attrs = self.config_manager.attribute_mapping.get("woocommerce_attributes", {})
        
        # Проверяем точное совпадение
        if key in standard_fields or key in woocommerce_attrs:
            return key
        
        # Проверяем совпадение без учета регистра
        for config_key in list(standard_fields.keys()) + list(woocommerce_attrs.keys()):
            if config_key.lower() == key_lower:
                return config_key
        
        # Проверяем частичное совпадение
        for config_key in list(standard_fields.keys()) + list(woocommerce_attrs.keys()):
            if config_key.lower() in key_lower or key_lower in config_key.lower():
                return config_key
        
        # Если не нашли совпадение, возвращаем оригинальный ключ
        return key
    
    def _process_standard_fields(self, specs: Dict[str, str]) -> Dict[str, Any]:
        """
        Обрабатывает стандартные поля: вес, высота, ширина, глубина.
        
        Args:
            specs: Словарь характеристик
            
        Returns:
            Словарь с полями weight, height, width, length
        """
        result = {}
        
        # Получаем маппинг стандартных полей из конфига
        standard_mapping = self.config_manager.attribute_mapping.get("standard_fields", {})
        
        for spec_key, woo_field in standard_mapping.items():
            if spec_key in specs:
                value_str = specs[spec_key]
                
                # Извлекаем числовое значение и единицу измерения
                numeric_value, unit = self.config_manager.extract_unit(value_str)
                
                if numeric_value:
                    # Сохраняем значение
                    result[woo_field] = numeric_value
                    
                    # Если есть единица измерения, сохраняем ее в meta-поле
                    if unit:
                        result[f"meta:{woo_field}_unit"] = unit
        
        return result
    
    def _process_woocommerce_attributes(self, specs: Dict[str, str]) -> Dict[str, Any]:
        """
        Обрабатывает атрибуты WooCommerce.
        
        Args:
            specs: Словарь характеристик
            
        Returns:
            Словарь с атрибутами WooCommerce
        """
        result = {}
        
        # Получаем маппинг атрибутов из конфига
        attr_mapping = self.config_manager.attribute_mapping.get("woocommerce_attributes", {})
        
        for spec_key, woo_attr in attr_mapping.items():
            if spec_key in specs:
                value = specs[spec_key]
                
                # Нормализуем значение для Да/Нет
                if spec_key in ["Наличие", "В наличии", "Есть в наличии"]:
                    normalized_value = self.config_manager.normalize_yes_no_value(value)
                else:
                    normalized_value = value.strip()
                
                # Добавляем атрибут
                result[woo_attr] = normalized_value
        
        return result
    
    def _extract_numeric_value(self, value_str: str) -> Tuple[str, str]:
        """
        Извлекает числовое значение и единицу измерения из строки.
        
        Args:
            value_str: Строка со значением (например, "10 кг")
            
        Returns:
            Кортеж (числовое значение, единица измерения)
        """
        if not value_str:
            return "", ""
        
        # Удаляем лишние пробелы
        value_str = value_str.strip()
        
        # Ищем числовую часть (целые и десятичные числа)
        # Поддерживаем форматы: 10, 10.5, 10,5, 10 кг, 10.5см и т.д.
        match = re.search(r'([0-9]+[.,]?[0-9]*)', value_str.replace(' ', ''))
        
        if not match:
            return value_str, ""
        
        numeric_value = match.group(1)
        
        # Определяем единицу измерения
        units = {
            'кг': 'kg', 'г': 'g', 'гр': 'g',
            'см': 'cm', 'мм': 'mm', 'м': 'm',
            'л': 'l', 'мл': 'ml',
            'шт': 'pcs', 'уп': 'pack'
        }
        
        # Ищем единицу измерения в строке
        for unit_ru, unit_en in units.items():
            if unit_ru in value_str.lower():
                return numeric_value, unit_en
        
        return numeric_value, ""
    
    def cleanup(self) -> None:
        """
        Очищает кэш характеристик.
        """
        self.specs_cache.clear()
        logger.debug(f"SpecsHandler: очищен кэш характеристик")
        super().cleanup()