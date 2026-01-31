"""
CoreHandler - основной обработчик для B2B-WC Converter v2.0.
Обрабатывает: названия, артикулы, цены, категории, SEO.
"""
import re
from typing import Dict, Any

# Используем относительные импорты
try:
    from .base_handler import BaseHandler
    from ..models import RawProduct
    from ..config_manager import ConfigManager
    from ..utils.logger import get_logger
    from ..utils.validators import generate_slug, extract_price
except ImportError:
    from base_handler import BaseHandler
    from models import RawProduct
    from config_manager import ConfigManager
    from utils.logger import get_logger
    from utils.validators import generate_slug, extract_price

logger = get_logger(__name__)


class CoreHandler(BaseHandler):
    """
    Основной обработчик товара.
    Обрабатывает ядро данных: названия, артикулы, цены, категории, SEO.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует CoreHandler.
        
        Args:
            config_manager: Менеджер конфигураций
        """
        super().__init__(config_manager)
        
        # Кэш для сгенерированных slug'ов (чтобы избежать дубликатов)
        self.slug_cache: Dict[str, str] = {}
        
        # Счетчик для уникальных slug'ов
        self.slug_counter: Dict[str, int] = {}
    
    def process(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает сырой продукт и возвращает основные поля WooProduct.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с основными полями WooProduct
        """
        result = {}
        
        # 1. Название товара
        result.update(self._process_title(raw_product))
        
        # 2. Артикулы и идентификаторы
        result.update(self._process_identifiers(raw_product))
        
        # 3. Цена
        result.update(self._process_price(raw_product))
        
        # 4. Категории
        result.update(self._process_categories(raw_product))
        
        # 5. Штрих-код
        result.update(self._process_barcode(raw_product))
        
        # 6. Эксклюзив
        result.update(self._process_exclusive(raw_product))
        
        # 7. Краткое описание (excerpt)
        result.update(self._process_excerpt(raw_product))
        
        # 8. SEO поля
        result.update(self._process_seo(raw_product, result))
        
        # 9. Статусы и авторы
        result.update(self._process_statuses())
        
        logger.debug(f"CoreHandler обработал продукт {raw_product.НС_код}: {len(result)} полей")
        return result
    
    def _process_title(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает название товара и генерирует slug.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полями post_title и post_name
        """
        title = raw_product.Наименование.strip()
        if not title:
            title = f"Товар {raw_product.НС_код}"
        
        # Генерируем slug из названия
        slug = self._generate_slug(title, raw_product.НС_код)
        
        return {
            "post_title": title,
            "post_name": slug
        }
    
    def _generate_slug(self, title: str, sku: str) -> str:
        """
        Генерирует уникальный slug из названия.
        
        Args:
            title: Название товара
            sku: Артикул товара
            
        Returns:
            Уникальный slug
        """
        # Используем утилиту для генерации slug
        slug = generate_slug(title)
        
        # Если slug пустой, используем артикул
        if not slug:
            slug = generate_slug(sku)
        
        # Проверяем уникальность
        if slug in self.slug_cache:
            # Добавляем счетчик для уникальности
            if slug not in self.slug_counter:
                self.slug_counter[slug] = 1
            self.slug_counter[slug] += 1
            slug = f"{slug}-{self.slug_counter[slug]}"
        else:
            self.slug_cache[slug] = sku
        
        return slug
    
    def _process_identifiers(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает артикулы и идентификаторы.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полями sku и meta:артикул
        """
        result = {}
        
        # Основной SKU - НС-код
        if raw_product.НС_код:
            result["sku"] = raw_product.НС_код.strip()
        
        # Артикул производителя в мета-поле
        if raw_product.Артикул:
            result["meta:артикул"] = raw_product.Артикул.strip()
        
        return result
    
    def _process_price(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Извлекает цену из строки вида "14990 руб."
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полем regular_price
        """
        price_str = raw_product.Цена.strip() if raw_product.Цена else ""
        
        if not price_str:
            return {"regular_price": ""}
        
        # Используем утилиту для извлечения цены
        price, _ = extract_price(price_str)
        
        if price:
            # Получаем разделитель десятичных из конфига
            decimal_sep = self.config_manager.get_setting('processing.decimal_separator', '.')
            
            # Если в конфиге запятая, а у нас точка - меняем
            if decimal_sep == ',' and '.' in price:
                price = price.replace('.', ',')
            
            return {"regular_price": price}
        
        return {"regular_price": ""}
    
    def _process_categories(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Преобразует категории из формата "Категория - Подкатегория" в "Категория > Подкатегория".
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полем tax:product_cat
        """
        category_str = raw_product.Название_категории.strip() if raw_product.Название_категории else ""
        
        if not category_str:
            return {"tax:product_cat": ""}
        
        # Заменяем разделители " - " на " > "
        category = category_str.replace(' - ', ' > ')
        
        return {"tax:product_cat": category}
    
    def _process_barcode(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Извлекает первый штрих-код для поля meta:_global_unique_id.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полем meta:_global_unique_id
        """
        barcode_str = raw_product.Штрих_код.strip() if raw_product.Штрих_код else ""
        
        if not barcode_str:
            return {"meta:_global_unique_id": ""}
        
        # Разделяем по "/" и берем первый
        barcodes = [b.strip() for b in barcode_str.split('/') if b.strip()]
        
        if barcodes:
            return {"meta:_global_unique_id": barcodes[0]}
        
        return {"meta:_global_unique_id": ""}
    
    def _process_exclusive(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает поле "Эксклюзив".
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полем meta:эксклюзив
        """
        exclusive_str = raw_product.Эксклюзив.strip() if raw_product.Эксклюзив else ""
        
        if not exclusive_str:
            return {"meta:эксклюзив": "Нет"}
        
        # Извлекаем значение после "Эксклюзив - "
        if " - " in exclusive_str:
            value = exclusive_str.split(" - ", 1)[1].strip()
        else:
            value = exclusive_str
        
        # Используем утилиту для нормализации
        normalized = self.config_manager.normalize_yes_no_value(value)
        
        return {"meta:эксклюзив": normalized}
    
    def _process_excerpt(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Создает краткое описание из HTML статьи.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полем post_excerpt
        """
        article_html = raw_product.Статья.strip() if raw_product.Статья else ""
        
        if not article_html:
            return {"post_excerpt": ""}
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', article_html)
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Обрезаем до 160 символов
        if len(text) > 160:
            text = text[:157] + "..."
        
        return {"post_excerpt": text}
    
    def _process_seo(self, raw_product: RawProduct, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует SEO поля по шаблонам.
        
        Args:
            raw_product: Сырые данные продукта
            processed_data: Уже обработанные данные
            
        Returns:
            Словарь с SEO полями
        """
        result = {}
        
        # Подготавливаем данные для шаблонов
        template_data = {
            "post_title": processed_data.get("post_title", ""),
            "post_name": processed_data.get("post_name", ""),
            "post_excerpt": processed_data.get("post_excerpt", ""),
            "brand": raw_product.Бренд or "",
            "sku": raw_product.НС_код or ""
        }
        
        # Генерируем основные SEO поля
        seo_fields = [
            "title_template",
            "metadesc_template", 
            "focuskw_template",
            "canonical_template",
            "og_title_template",
            "og_description_template",
            "twitter_title_template",
            "twitter_description_template"
        ]
        
        for field in seo_fields:
            template = self.config_manager.get_seo_template(field)
            if template:
                # Заменяем плейсхолдеры в шаблоне
                value = template
                for key, val in template_data.items():
                    placeholder = "{" + key + "}"
                    value = value.replace(placeholder, str(val))
                
                # Сохраняем результат
                result[f"meta:_yoast_wpseo_{field.replace('_template', '')}"] = value
        
        # Генерируем остальные мета-поля из конфига
        meta_fields = self.config_manager.seo_templates.get("meta_fields", {})
        for meta_field, template in meta_fields.items():
            if isinstance(template, str) and template.startswith("{") and template.endswith("}"):
                # Это ссылка на другой шаблон
                template_name = template[1:-1]
                if template_name in result:
                    result[meta_field] = result[template_name]
                else:
                    # Попробуем найти в основных шаблонах
                    for seo_field in seo_fields:
                        if seo_field == template_name:
                            seo_field_name = f"meta:_yoast_wpseo_{seo_field.replace('_template', '')}"
                            if seo_field_name in result:
                                result[meta_field] = result[seo_field_name]
                                break
                    else:
                        result[meta_field] = template
            else:
                # Статическое значение
                result[meta_field] = template
        
        return result
    
    def _process_statuses(self) -> Dict[str, Any]:
        """
        Возвращает стандартные статусы из конфига.
        
        Returns:
            Словарь со статусами
        """
        result = {}
        
        # Берем значения по умолчанию из конфига
        default_values = self.config_manager.settings.get("default_values", {})
        
        # Копируем только нужные поля
        status_fields = {
            "post_status": "post_status",
            "comment_status": "comment_status", 
            "post_author": "post_author",
            "tax:product_type": "tax_product_type",
            "stock_status": "stock_status",
            "manage_stock": "manage_stock",
            "sold_individually": "sold_individually",
            "backorders": "backorders",
            "downloadable": "downloadable",
            "virtual": "virtual",
            "tax_status": "tax_status",
            "download_limit": "download_limit",
            "download_expiry": "download_expiry",
            "menu_order": "menu_order",
            "featured": "featured"
        }
        
        for woo_field, config_key in status_fields.items():
            if config_key in default_values:
                result[woo_field] = default_values[config_key]
        
        return result
    
    def cleanup(self) -> None:
        """
        Очищает кэш slug'ов.
        """
        self.slug_cache.clear()
        self.slug_counter.clear()
        logger.debug(f"CoreHandler: очищен кэш slug'ов")
        super().cleanup()