"""
Aggregator - сборщик данных для B2B-WC Converter v2.0.
Объединяет фрагменты от всех обработчиков в готовый WooProduct.
"""
from typing import Dict, Any, List
import logging

from .models import RawProduct, WooProduct
from .config_manager import ConfigManager
from .handlers import (
    CoreHandler, 
    SpecsHandler, 
    MediaHandler, 
    ContentHandler
)

logger = logging.getLogger(__name__)


class Aggregator:
    """
    Сборщик данных товара.
    Объединяет результаты обработчиков и применяет дефолтные значения.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует агрегатор и обработчики.
        
        Args:
            config_manager: Менеджер конфигураций
        """
        self.config_manager = config_manager
        
        # Инициализируем обработчики
        self.handlers = [
            CoreHandler(config_manager),
            SpecsHandler(config_manager),
            MediaHandler(config_manager),
            ContentHandler(config_manager)
        ]
        
        logger.info(f"Aggregator инициализирован с {len(self.handlers)} обработчиками")
    
    def process_product(self, raw_product: RawProduct) -> WooProduct:
        """
        Обрабатывает сырой продукт через все обработчики.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Готовый продукт WooCommerce
        """
        logger.debug(f"Обработка продукта: {raw_product.НС_код}")
        
        # Собираем данные от всех обработчиков
        handler_results = {}
        
        for handler in self.handlers:
            try:
                handler_name = handler.handler_name
                result = handler.handle(raw_product)
                
                if result:
                    handler_results[handler_name] = result
                    logger.debug(f"  {handler_name}: обработано {len(result)} полей")
                else:
                    logger.warning(f"  {handler_name}: вернул пустой результат")
                    
            except Exception as e:
                logger.error(f"  {handler_name}: ошибка обработки - {e}")
                # Продолжаем работу с другими обработчиками
                continue
        
        # Объединяем все результаты
        merged_data = self._merge_handler_results(handler_results)
        
        # Создаем WooProduct
        woo_product = self._create_woo_product(merged_data)
        
        # Применяем дефолтные значения
        self._apply_default_values(woo_product)
        
        # Устанавливаем пустые поля из ТЗ
        self._set_empty_fields(woo_product)
        
        logger.debug(f"Продукт {raw_product.НС_код} агрегирован: {len(merged_data)} полей")
        return woo_product
    
    def _merge_handler_results(self, handler_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Объединяет результаты от всех обработчиков.
        
        Args:
            handler_results: Словарь {имя_обработчика: результат}
            
        Returns:
            Объединенный словарь данных
        """
        merged = {}
        
        for handler_name, result in handler_results.items():
            # Проверяем конфликты полей
            for key, value in result.items():
                if key in merged and merged[key] != value:
                    logger.warning(f"Конфликт поля '{key}': "
                                  f"было '{merged[key]}', стало '{value}' "
                                  f"(обработчик: {handler_name})")
            
            # Объединяем
            merged.update(result)
        
        return merged
    
    def _create_woo_product(self, data: Dict[str, Any]) -> WooProduct:
        """
        Создает объект WooProduct из объединенных данных.
        
        Args:
            data: Объединенные данные от обработчиков
            
        Returns:
            Экземпляр WooProduct
        """
        woo_product = WooProduct()
        
        # Заполняем основные поля
        for key, value in data.items():
            self._set_woo_product_field(woo_product, key, value)
        
        return woo_product
    
    def _set_woo_product_field(self, woo_product: WooProduct, key: str, value: Any) -> None:
        """
        Устанавливает поле в WooProduct с учетом типа поля.
        
        Args:
            woo_product: Продукт WooCommerce
            key: Ключ поля
            value: Значение поля
        """
        # Определяем тип поля
        if key.startswith('tax:'):
            # Таксономии
            field_name = 'tax_' + key[4:].replace('-', '_')
        elif key.startswith('meta:'):
            # Мета-поля
            woo_product.meta_fields[key] = str(value) if value is not None else ""
            return
        elif key.startswith('attribute:'):
            # Атрибуты
            woo_product.attributes[key] = str(value) if value is not None else ""
            return
        else:
            # Обычные поля
            field_name = key
        
        # Проверяем, существует ли поле в WooProduct
        if hasattr(woo_product, field_name):
            setattr(woo_product, field_name, str(value) if value is not None else "")
        else:
            # Если поле не найдено, добавляем в мета-поля
            woo_product.meta_fields[key] = str(value) if value is not None else ""
    
    def _apply_default_values(self, woo_product: WooProduct) -> None:
        """
        Применяет значения по умолчанию из конфига.
        
        Args:
            woo_product: Продукт WooCommerce
        """
        default_values = self.config_manager.settings.get("default_values", {})
        
        for config_key, default_value in default_values.items():
            # Определяем поле WooProduct
            if config_key.startswith('tax:'):
                field_name = 'tax_' + config_key[4:].replace('-', '_')
                woo_field = config_key  # Сохраняем оригинальное имя для проверки
            else:
                field_name = config_key
                woo_field = config_key
            
            # Проверяем, установлено ли уже значение
            current_value = None
            
            if woo_field.startswith('tax:'):
                # Для таксономий проверяем поле с префиксом tax_
                woo_field_name = 'tax_' + woo_field[4:].replace('-', '_')
                if hasattr(woo_product, woo_field_name):
                    current_value = getattr(woo_product, woo_field_name)
            elif hasattr(woo_product, field_name):
                current_value = getattr(woo_product, field_name)
            
            # Если значение не установлено, применяем дефолтное
            if not current_value:
                self._set_woo_product_field(woo_product, config_key, default_value)
    
    def _set_empty_fields(self, woo_product: WooProduct) -> None:
        """
        Устанавливает пустые значения для полей из ТЗ п.4.2.
        
        Args:
            woo_product: Продукт WooCommerce
        """
        # Список полей, которые должны быть пустыми (из ТЗ п.4.2)
        empty_fields = [
            # Основные поля
            "ID", "post_parent", "parent_sku", "children",
            
            # Цены и наличие
            "sale_price", "stock", "low_stock_amount",
            
            # Таксономии и классы
            "tax_class", "visibility", "tax:product_visibility",
            "tax:product_tag", "tax:product_shipping_class",
            
            # Связи
            "upsell_ids", "crosssell_ids",
            
            # Заметки и даты
            "purchase_note", "sale_price_dates_from", "sale_price_dates_to",
            
            # Ссылки
            "product_url", "button_text", "product_page_url",
            
            # Мета-поля WooCommerce
            "meta:total_sales",
            
            # SEO поля Yoast (кроме тех, что заполняются автоматически)
            "meta:_yoast_wpseo_bctitle",
            "meta:_yoast_wpseo_meta-robots-adv",
            "meta:_yoast_wpseo_is_cornerstone",
            "meta:_yoast_wpseo_linkdex",
            "meta:_yoast_wpseo_estimated-reading-time-minutes",
            "meta:_yoast_wpseo_content_score",
            "meta:_yoast_wpseo_metakeywords"
        ]
        
        for field in empty_fields:
            self._set_woo_product_field(woo_product, field, "")
    
    def cleanup(self) -> None:
        """
        Очищает ресурсы всех обработчиков.
        """
        for handler in self.handlers:
            try:
                handler.cleanup()
            except Exception as e:
                logger.warning(f"Ошибка при очистке {handler.handler_name}: {e}")
        
        logger.debug("Aggregator: очищены ресурсы всех обработчиков")