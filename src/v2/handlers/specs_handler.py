"""
SpecsHandler - обработчик характеристик для B2B-WC Converter v2.0.
Обрабатывает: вес, габариты, атрибуты фильтров из поля "Характеристики".
"""
from typing import Dict, Any

# Используем относительные импорты
try:
    from .base_handler import BaseHandler
    from ..models import RawProduct
    from ..config_manager import ConfigManager
    from ..utils.logger import get_logger
    from ..utils.validators import parse_specifications
except ImportError:
    from base_handler import BaseHandler
    from models import RawProduct
    from config_manager import ConfigManager
    from utils.logger import get_logger
    from utils.validators import parse_specifications

logger = get_logger(__name__)


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
        
        # 1. Парсим характеристики с помощью утилиты
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
        
        # Используем утилиту для парсинга
        specs = parse_specifications(specs_string)
        
        # Нормализуем ключи для сопоставления с конфигом
        normalized_specs = {}
        for key, value in specs.items():
            normalized_key = self._normalize_spec_key(key)
            
            # Нормализуем значение Да/Нет
            if value.lower() in ['да', 'yes', '1', 'true', 'есть']:
                normalized_value = 'Да'
            elif value.lower() in ['нет', 'no', '0', 'false', 'отсутствует']:
                normalized_value = 'Нет'
            else:
                normalized_value = value
            
            normalized_specs[normalized_key] = normalized_value
        
        return normalized_specs
    
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
                
                # Используем метод конфиг менеджера для извлечения значения и единицы
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
                
                # Нормализуем значение (уже сделано в _parse_specifications)
                normalized_value = value.strip()
                
                # Добавляем атрибут
                result[woo_attr] = normalized_value
        
        return result
    
    def cleanup(self) -> None:
        """
        Очищает кэш характеристик.
        """
        self.specs_cache.clear()
        logger.debug(f"SpecsHandler: очищен кэш характеристик")
        super().cleanup()