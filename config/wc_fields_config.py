"""
config/wc_fields_config.py
Конфигурация полей для экспорта в WooCommerce CSV
Полный список полей в правильном порядке для импорта через WebToffee
"""

from typing import Dict, List
import re


class WCFieldsConfig:
    """
    Конфигурация полей WooCommerce CSV
    """
    
    # Полный список полей в правильном порядке (138 полей)
    # Порядок важен для корректного импорта в WooCommerce
    WC_FIELDS_ORDER = [
        # Основные поля товара
        'post_title',
        'post_name',
        'post_parent',
        'ID',
        'post_content',
        'post_excerpt',
        'post_status',
        'post_password',
        'menu_order',
        'post_date',
        'post_author',
        'comment_status',
        
        # Данные товара WooCommerce
        'sku',
        'parent_sku',
        'children',
        'downloadable',
        'virtual',
        'stock',
        'regular_price',
        'sale_price',
        'weight',
        'length',
        'width',
        'height',
        'tax_class',
        'visibility',
        'stock_status',
        'backorders',
        'sold_individually',
        'low_stock_amount',
        'manage_stock',
        'tax_status',
        'upsell_ids',
        'crosssell_ids',
        'purchase_note',
        'sale_price_dates_from',
        'sale_price_dates_to',
        'download_limit',
        'download_expiry',
        'product_url',
        'button_text',
        'images',
        'downloadable_files',
        'product_page_url',
        
        # Мета-поля
        'meta:total_sales',
        'meta:_global_unique_id',
        'meta:_yoast_wpseo_focuskw',
        'meta:_yoast_wpseo_canonical',
        'meta:_yoast_wpseo_bctitle',
        'meta:_yoast_wpseo_meta-robots-adv',
        'meta:_yoast_wpseo_is_cornerstone',
        'meta:_yoast_wpseo_metadesc',
        'meta:_yoast_wpseo_linkdex',
        'meta:_yoast_wpseo_estimated-reading-time-minutes',
        'meta:_yoast_wpseo_content_score',
        'meta:_yoast_wpseo_title',
        'meta:_yoast_wpseo_metakeywords',
        
        # Таксономии
        'tax:product_brand',
        'tax:product_type',
        'tax:product_visibility',
        'tax:product_cat',
        'tax:product_tag',
        'tax:product_shipping_class',
        
        # Атрибуты WooCommerce (предопределенные)
        'attribute:pa_proizvoditel',
        'attribute_data:pa_proizvoditel',
        'attribute:pa_sposob-primenenija',
        'attribute_data:pa_sposob-primenenija',
        'attribute:pa_tip-narushenij',
        'attribute_data:pa_tip-narushenij',
        'attribute:pa_tip-uchrezhdenij',
        'attribute_data:pa_tip-uchrezhdenij',
        'attribute:pa_tip-ustrojstva',
        'attribute_data:pa_tip-ustrojstva',
        'attribute:pa_zona-primenenija',
        'attribute_data:pa_zona-primenenija',
    ]
    
    # Значения по умолчанию для полей
    DEFAULT_VALUES = {
        # Обязательные поля с фиксированными значениями
        'post_status': 'publish',
        'post_password': '',
        'menu_order': '0',
        'post_author': '2',  # ID автора = 2
        'comment_status': 'closed',
        
        # Данные товара
        'post_parent': '',  # Пусто для простых товаров
        'ID': '',  # Оставить пустым, WC сам назначит
        'parent_sku': '',
        'children': '',
        'downloadable': 'no',
        'virtual': 'no',
        'stock': '',  # Пусто = неограниченно
        'sale_price': '',  # Без скидки
        'tax_class': '',
        'visibility': 'visible',
        'stock_status': 'instock',
        'backorders': 'no',
        'sold_individually': 'no',
        'low_stock_amount': '',
        'manage_stock': 'no',
        'tax_status': 'taxable',
        'upsell_ids': '',
        'crosssell_ids': '',
        'purchase_note': '',
        'sale_price_dates_from': '',
        'sale_price_dates_to': '',
        'download_limit': "'-1",  # С апострофом и минусом
        'download_expiry': "'-1",  # С апострофом и минусом
        'product_url': '',
        'button_text': '',
        'downloadable_files': '',
        'product_page_url': '',
        
        # Мета-поля
        'meta:total_sales': '0',
        'meta:_global_unique_id': '',
        'meta:_yoast_wpseo_canonical': '',
        'meta:_yoast_wpseo_bctitle': '',
        'meta:_yoast_wpseo_meta-robots-adv': '',
        'meta:_yoast_wpseo_is_cornerstone': '',
        'meta:_yoast_wpseo_title': '',
        'meta:_yoast_wpseo_metakeywords': '',
        
        # Таксономии
        'tax:product_type': 'simple',
        'tax:product_visibility': '',
        'tax:product_tag': '',
        'tax:product_shipping_class': '',
        
        # Данные атрибутов (фиксированные для всех атрибутов)
        'attribute_data:pa_proizvoditel': '',
        'attribute_data:pa_sposob-primenenija': '',
        'attribute_data:pa_tip-narushenij': '',
        'attribute_data:pa_tip-uchrezhdenij': '',
        'attribute_data:pa_tip-ustrojstva': '',
        'attribute_data:pa_zona-primenenija': '',
    }
    
    @staticmethod
    def generate_seo_fields(product_name: str, description: str = "", sku: str = "") -> Dict[str, str]:
        """
        Генерация SEO полей Yoast на основе названия товара и описания
        
        Args:
            product_name: Название товара
            description: Описание товара (опционально)
            sku: Артикул товара (опционально)
            
        Returns:
            Dict[str, str]: Сгенерированные SEO поля
        """
        seo_fields = {}
        
        # 1. Focus keyword - берем первые 2-3 слова из названия
        words = product_name.split()[:3]
        seo_fields['meta:_yoast_wpseo_focuskw'] = ' '.join(words)
        
        # 2. Meta description - создаем из начала описания или названия
        if description:
            # Убираем HTML теги для meta description
            text_only = re.sub(r'<[^>]+>', ' ', description)
            text_only = ' '.join(text_only.split()[:30])  # Берем первые 30 слов
            
            if len(text_only) > 150:
                # Обрезаем до 150 символов
                meta_desc = text_only[:150]
                last_space = meta_desc.rfind(' ')
                if last_space > 100:
                    meta_desc = meta_desc[:last_space]
                meta_desc += '...'
            else:
                meta_desc = text_only
        else:
            meta_desc = f"Купить {product_name}. Высокое качество, гарантия производителя. Доставка по всей России."
        
        seo_fields['meta:_yoast_wpseo_metadesc'] = meta_desc
        
        # 3. Linkdex - случайное значение 55-95 (как в примере)
        import random
        seo_fields['meta:_yoast_wpseo_linkdex'] = str(random.randint(55, 95))
        
        # 4. Estimated reading time - 1-3 минуты
        seo_fields['meta:_yoast_wpseo_estimated-reading-time-minutes'] = str(random.randint(1, 3))
        
        # 5. Content score - 70-100
        seo_fields['meta:_yoast_wpseo_content_score'] = str(random.randint(70, 100))
        
        return seo_fields
    
    @staticmethod
    def generate_post_name(title: str) -> str:
        """
        Генерация post_name (slug) из названия товара
        
        Args:
            title: Название товара
            
        Returns:
            str: slug для URL
        """
        if not title:
            return ""
        
        # Приводим к нижнему регистру
        slug = title.lower().strip()
        
        # Заменяем русские буквы на латинские (базовая транслитерация)
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya',
            ' ': '-', '_': '-', '/': '-', '\\': '-',
        }
        
        # Транслитерация
        result = []
        for char in slug:
            if char in translit_map:
                result.append(translit_map[char])
            elif char.isalnum():
                result.append(char)
        
        slug = ''.join(result)
        
        # Удаляем повторяющиеся дефисы
        slug = re.sub(r'-+', '-', slug)
        
        # Удаляем дефисы в начале и конце
        slug = slug.strip('-')
        
        # Ограничиваем длину
        if len(slug) > 100:
            slug = slug[:100].rstrip('-')
        
        return slug
    
    @staticmethod
    def clean_images_string(images_str: str) -> str:
        """
        Очистка строки с изображениями - оставляем только URL через |
        
        Args:
            images_str: Строка с изображениями в формате "URL ! alt : ..."
            
        Returns:
            str: Очищенная строка с URL через |
        """
        if not images_str:
            return ""
        
        # Разделяем по | если есть
        if ' | ' in images_str:
            parts = images_str.split(' | ')
        else:
            parts = [images_str]
        
        clean_urls = []
        for part in parts:
            # Ищем URL (начинается с http:// или https://)
            if 'http' in part:
                # Берем часть до первого пробела после URL или до " !"
                url_end = part.find(' !')
                if url_end != -1:
                    url = part[:url_end].strip()
                else:
                    url = part.strip()
                
                if url.startswith(('http://', 'https://')):
                    clean_urls.append(url)
        
        return ' | '.join(clean_urls) if clean_urls else ""
    
    @staticmethod
    def get_all_fields() -> List[str]:
        """
        Получить полный список полей в правильном порядке
        
        Returns:
            List[str]: Список полей
        """
        return WCFieldsConfig.WC_FIELDS_ORDER.copy()
    
    @staticmethod
    def get_default_row() -> Dict[str, str]:
        """
        Получить строку с значениями по умолчанию для всех полей
        
        Returns:
            Dict[str, str]: Словарь полей со значениями по умолчанию
        """
        row = {}
        for field in WCFieldsConfig.WC_FIELDS_ORDER:
            if field in WCFieldsConfig.DEFAULT_VALUES:
                row[field] = WCFieldsConfig.DEFAULT_VALUES[field]
            else:
                row[field] = ''
        return row


# Функции для быстрого доступа
def get_wc_fields() -> List[str]:
    """Получить список полей WC"""
    return WCFieldsConfig.get_all_fields()


def get_wc_default_row() -> Dict[str, str]:
    """Получить строку со значениями по умолчанию"""
    return WCFieldsConfig.get_default_row()


def generate_seo_for_product(product_name: str, description: str = "", sku: str = "") -> Dict[str, str]:
    """Сгенерировать SEO поля для товара"""
    return WCFieldsConfig.generate_seo_fields(product_name, description, sku)


def generate_slug_from_title(title: str) -> str:
    """Сгенерировать slug из названия"""
    return WCFieldsConfig.generate_post_name(title)


def clean_images_for_wc(images_str: str) -> str:
    """Очистить строку с изображениями для WC"""
    return WCFieldsConfig.clean_images_string(images_str)