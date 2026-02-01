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
        """
        
        print(f"[DEBUG] !!!!!! RawProduct.Характеристики (полностью):")
        print(raw_product.Характеристики)


        result = {}
        
        # 1. Парсим характеристики
        specs = self._parse_specifications(raw_product.Характеристики)
        
        # ДОБАВЬ ОТЛАДКУ
        print(f"[DEBUG SpecsHandler] Все характеристики ({len(specs)}):")
        for key, value in specs.items():
            print(f"  '{key}': '{value}'")
        
        # 2. Обрабатываем стандартные поля (вес, габариты)
        std_fields = self._process_standard_fields(specs)
        print(f"[DEBUG] Стандартные поля: {std_fields}")
        result.update(std_fields)
        
        # 3. Обрабатываем атрибуты WooCommerce
        wc_attrs = self._process_woocommerce_attributes(specs)
        print(f"[DEBUG] Атрибуты WooCommerce: {wc_attrs}")
        result.update(wc_attrs)
        
        return result
    
    def _parse_specifications(self, specs_string: str) -> Dict[str, str]:
        """
        Парсит строку характеристик.
        """
        if not specs_string:
            return {}
        
        # Нормализуем: удаляем переносы строк
        normalized = specs_string.replace('\n', ' ').replace('\r', ' ')
        import re
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Используем утилиту
        from ..utils.validators import parse_specifications as parse_specs
        specs = parse_specs(normalized)
        
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
        """
        result = {}
        
        # Получаем маппинг стандартных полей из конфига
        standard_mapping = self.config_manager.attribute_mapping.get("standard_fields", {})
        
        print(f"[DEBUG] Маппинг стандартных полей: {standard_mapping}")
        
        for spec_key, woo_field in standard_mapping.items():
            if spec_key in specs:
                value_str = specs[spec_key]
                print(f"[DEBUG] Обрабатываем '{spec_key}' -> '{woo_field}': '{value_str}'")
                
                # Извлекаем числовое значение и единицу измерения
                numeric_value, unit = self.config_manager.extract_unit(value_str)
                
                if numeric_value:
                    # Сохраняем значение
                    result[woo_field] = numeric_value
                    print(f"[DEBUG]   Числовое значение: '{numeric_value}', единица: '{unit}'")
                    
                    # Если есть единица измерения, сохраняем ее в meta-поле
                    if unit:
                        result[f"meta:{woo_field}_unit"] = unit
        
        return result

    
    def _process_woocommerce_attributes(self, specs: Dict[str, str]) -> Dict[str, Any]:
        """
        Обрабатывает атрибуты WooCommerce.
        """
        result = {}
        
        # Получаем маппинг атрибутов из конфига
        attr_mapping = self.config_manager.attribute_mapping.get("woocommerce_attributes", {})
        
        print(f"[DEBUG] Маппинг атрибутов: {attr_mapping}")
        print(f"[DEBUG] Доступные характеристики: {list(specs.keys())[:10]}...")
        
        for spec_key, woo_attr in attr_mapping.items():
            if spec_key in specs:
                value = specs[spec_key]
                print(f"[DEBUG] Найдено: '{spec_key}' → '{woo_attr}' = '{value}'")
                
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