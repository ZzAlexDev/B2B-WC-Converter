"""
Aggregator - сборщик данных для B2B-WC Converter v2.0.
Объединяет фрагменты от всех обработчиков в готовый WooProduct.
"""
import logging
import re
from typing import Dict, Any, List
from .models import RawProduct, WooProduct
from .config_manager import ConfigManager
from .handlers import (
    CoreHandler, 
    SpecsHandler, 
    MediaHandler, 
    ContentHandler,
    TagsHandler
)

logger = logging.getLogger(__name__)


class Aggregator:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
        # Инициализируем обработчики
        self.specs_handler = SpecsHandler(config_manager)
        self.tags_handler = TagsHandler(config_manager)  # ← НОВЫЙ
        self.tags_handler.set_specs_handler(self.specs_handler)  # ← Связываем
        
        self.handlers = [
            CoreHandler(config_manager),
            self.specs_handler,
            MediaHandler(config_manager),
            ContentHandler(config_manager)
        ]
        
        logger.info(f"Aggregator инициализирован с {len(self.handlers)} обработчиками")


    def process_product(self, raw_product: RawProduct) -> WooProduct:
        """
        Обрабатывает сырой продукт через все обработчики.
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
                    # ОТЛАДКА
                    if handler_name == 'SpecsHandler':
                        # print(f"\n[DEBUG] === SpecsHandler вернул ===")
                        for key, val in result.items():
                            print(f"  '{key}': '{val}'")
                        # print(f"=== Всего {len(result)} полей ===\n")
                else:
                    logger.warning(f"  {handler_name}: вернул пустой результат")
                    
            except Exception as e:
                logger.error(f"  {handler_name}: ошибка обработки - {e}")
                continue
        
        # Объединяем все результаты
        merged_data = self._merge_handler_results(handler_results)
        
        # Создаем WooProduct
        woo_product = self._create_woo_product(merged_data)
        
        # Добавляем бренд и теги
        brand = self._extract_brand_from_raw(raw_product)
        if brand:
            self._set_woo_product_field(woo_product, "tax:product_brand", brand)
        
        # Генерируем теги через TagsHandler
        tags = self.tags_handler.generate_tags(raw_product, brand, specs_data=None)
        if tags:
            self._set_woo_product_field(woo_product, "tax:product_tag", tags)

        
        # ОТЛАДКА
        # print(f"\n[DEBUG] === Добавленные tax-поля ===")
        # print(f"tax:product_brand: '{brand}'")
        # print(f"tax:product_tag: '{tags}'")
        # print(f"=== Конец tax-полей ===\n")
        
        # Применяем дефолтные значения
        self._apply_default_values(woo_product)
        
        # Устанавливаем пустые поля из ТЗ
        self._set_empty_fields(woo_product)
        
        logger.debug(f"Продукт {raw_product.НС_код} агрегирован: {len(merged_data)} полей")
        return woo_product
    
    def _extract_brand_from_raw(self, raw_product: RawProduct) -> str:
        """
        Извлекает бренд из RawProduct.
        """
        if hasattr(raw_product, 'Бренд') and raw_product.Бренд:
            brand = raw_product.Бренд.strip()
            if brand:
                # print(f"[DEBUG] Бренд найден в поле 'Бренд': '{brand}'")
                return brand
        
        brand_fields = ['brand', 'Brand', 'Производитель', 'manufacturer', 'vendor']
        for field in brand_fields:
            field_attr = field.replace(' ', '_').replace('-', '_')
            if hasattr(raw_product, field_attr):
                value = getattr(raw_product, field_attr)
                if value and str(value).strip():
                    brand = str(value).strip()
                    # print(f"[DEBUG] Бренд найден в поле '{field}': '{brand}'")
                    return brand
        
        if hasattr(raw_product, 'Наименование'):
            name = raw_product.Наименование.strip()
            first_word = name.split()[0] if name.split() else ""
            if len(first_word) <= 20 and not any(x in first_word for x in [' ', '-', ',', '(']):
                # print(f"[DEBUG] Бренд извлечен из названия: '{first_word}'")
                return first_word
        
        # print(f"[DEBUG] Бренд не найден для продукта: {raw_product.НС_код}")
        return ""
    
    
    # Остальные методы остаются без изменений
    def _merge_handler_results(self, handler_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        merged = {}
        
        print(f"[DEBUG Aggregator] Объединяю результаты от {len(handler_results)} обработчиков")
        
        for handler_name, result in handler_results.items():
            # print(f"\n[DEBUG] Обработчик '{handler_name}' вернул {len(result)} полей:")
            
            for key, value in result.items():
                # print(f"  '{key}': '{value}'")
                
                if key in merged and merged[key] != value:
                    logger.warning(f"Конфликт поля '{key}': было '{merged[key]}', стало '{value}' (обработчик: {handler_name})")
            
            merged.update(result)
        
        # print(f"\n[DEBUG] Итого объединено {len(merged)} полей")
        return merged
    
    def _create_woo_product(self, data: Dict[str, Any]) -> WooProduct:
        woo_product = WooProduct()
        
        print(f"[DEBUG _create_woo_product] Создаю WooProduct из {len(data)} полей")
        
        for key, value in data.items():
            self._set_woo_product_field(woo_product, key, value)
        
        return woo_product
    
    def _set_woo_product_field(self, woo_product: WooProduct, key: str, value: Any) -> None:
        print(f"[DEBUG _set_woo_product_field] Ключ: '{key}', Значение: '{value}'")
        
        if key.startswith('tax:'):
            field_name = 'tax_' + key[4:].replace('-', '_')
        elif key.startswith('meta:'):
            woo_product.meta_fields[key] = str(value) if value is not None else ""
            return
        elif key.startswith('attribute:'):
            woo_product.attributes[key] = str(value) if value is not None else ""
            return
        else:
            field_name = key
        
        if hasattr(woo_product, field_name):
            setattr(woo_product, field_name, str(value) if value is not None else "")
        else:
            woo_product.meta_fields[key] = str(value) if value is not None else ""
    
    def _apply_default_values(self, woo_product: WooProduct) -> None:
        default_values = self.config_manager.settings.get("default_values", {})
        
        for config_key, default_value in default_values.items():
            if config_key.startswith('tax:'):
                field_name = 'tax_' + config_key[4:].replace('-', '_')
                woo_field = config_key
            else:
                field_name = config_key
                woo_field = config_key
            
            current_value = None
            
            if woo_field.startswith('tax:'):
                woo_field_name = 'tax_' + woo_field[4:].replace('-', '_')
                if hasattr(woo_product, woo_field_name):
                    current_value = getattr(woo_product, woo_field_name)
            elif hasattr(woo_product, field_name):
                current_value = getattr(woo_product, field_name)
            
            if not current_value:
                self._set_woo_product_field(woo_product, config_key, default_value)
    
    def _set_empty_fields(self, woo_product: WooProduct) -> None:
        empty_fields = [
            "ID", "post_parent", "parent_sku", "children",
            "sale_price", "stock", "low_stock_amount",
            "tax_class", "visibility", "tax:product_visibility", "tax:product_shipping_class",
            "upsell_ids", "crosssell_ids",
            "purchase_note", "sale_price_dates_from", "sale_price_dates_to",
            "product_url", "button_text", "product_page_url",
            "meta:total_sales",
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
        for handler in self.handlers:
            try:
                handler.cleanup()
            except Exception as e:
                logger.warning(f"Ошибка при очистке {handler.handler_name}: {e}")
        
        try:
            self.tags_handler.cleanup()
        except Exception as e:
            logger.warning(f"Ошибка при очистке TagsHandler: {e}")

        
        logger.debug("Aggregator: очищены ресурсы всех обработчиков")