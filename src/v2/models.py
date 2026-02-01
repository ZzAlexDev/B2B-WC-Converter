"""
Модели данных для B2B-WC Converter v2.0
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime

# В файл models.py добавим этот метод в начале
def _safe_str(value: Any, default: str = "") -> str:
    """Безопасно преобразует любое значение в строку, обрезает пробелы."""
    if value is None:
        return default
    return str(value).strip() if isinstance(value, str) else str(value)

@dataclass
class RawProduct:
    """
    Сырые данные из исходного CSV.
    Соответствует фиксированным колонкам из ТЗ п.4.1
    """
    Наименование: str = ""
    Артикул: str = ""
    НС_код: str = ""
    Бренд: str = ""
    Название_категории: str = ""
    Характеристики: str = ""
    Изображение: str = ""
    Видео: str = ""
    Статья: str = ""
    Чертежи: str = ""
    Сертификаты: str = ""
    Промоматериалы: str = ""
    Инструкции: str = ""
    Штрих_код: str = ""
    Цена: str = ""
    Эксклюзив: str = ""
    
    # Дополнительные поля для обработки
    row_number: int = 0  # Номер строки в исходном файле
    raw_data: Dict[str, str] = field(default_factory=dict)  # Все исходные данные
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str], row_number: int) -> 'RawProduct':
        """
        Создает RawProduct из строки CSV с защитой от None.
        """
        # Создаем словарь с безопасными значениями
        safe_values = {}
        for key, value in row.items():
            # Используем оригинальные имена полей, как в CSV
            safe_values[key] = _safe_str(value)
        
        # Создаем продукт с безопасными значениями
        product = cls(row_number=row_number, raw_data=safe_values)
        
        # Прямое присвоение основных полей с преобразованием имен
        # Если поле отсутствует в CSV - оставляем значение по умолчанию (пустую строку)
        product.Наименование = _safe_str(safe_values.get('Наименование'))
        product.Артикул = _safe_str(safe_values.get('Артикул'))
        product.НС_код = _safe_str(safe_values.get('НС-код'))  # Обратите внимание на дефис
        product.Бренд = _safe_str(safe_values.get('Бренд'))
        product.Название_категории = _safe_str(safe_values.get('Название категории'))
        product.Характеристики = _safe_str(safe_values.get('Характеристики'))
        product.Изображение = _safe_str(safe_values.get('Изображение'))
        product.Видео = _safe_str(safe_values.get('Видео'))
        product.Статья = _safe_str(safe_values.get('Статья'))
        product.Чертежи = _safe_str(safe_values.get('Чертежи'))
        product.Сертификаты = _safe_str(safe_values.get('Сертификаты'))
        product.Промоматериалы = _safe_str(safe_values.get('Промоматериалы'))
        product.Инструкции = _safe_str(safe_values.get('Инструкции'))
        product.Штрих_код = _safe_str(safe_values.get('Штрих код'))  # Пробел в имени
        product.Цена = _safe_str(safe_values.get('Цена'))
        product.Эксклюзив = _safe_str(safe_values.get('Эксклюзив'))
        
        return product
    
    def to_dict(self) -> Dict[str, str]:
        """Возвращает словарь с исходными данными."""
        return self.raw_data.copy()


@dataclass
class WooProduct:
    """
    Данные товара для импорта в WooCommerce.
    Соответствует формату плагина WebToffee Import Export.
    """
    # Основные поля товара
    ID: str = ""
    post_title: str = ""
    post_name: str = ""
    post_content: str = ""
    post_excerpt: str = ""
    post_status: str = ""
    comment_status: str = ""
    post_author: str = ""
    
    # Цены и наличие
    regular_price: str = ""
    sale_price: str = ""
    stock: str = ""
    stock_status: str = ""
    low_stock_amount: str = ""
    manage_stock: str = ""
    
    # Артикулы и идентификаторы
    sku: str = ""
    parent_sku: str = ""
    children: str = ""
    post_parent: str = ""
    
    # Физические характеристики
    weight: str = ""
    length: str = ""
    width: str = ""
    height: str = ""
    
    # Таксономии
    tax_product_type: str = ""
    tax_product_cat: str = ""
    tax_product_brand: str = ""
    tax_product_tag: str = ""
    tax_product_shipping_class: str = ""
    tax_product_visibility: str = ""
    
    # Прочие настройки
    tax_status: str = ""
    tax_class: str = ""
    sold_individually: str = ""
    backorders: str = ""
    downloadable: str = ""
    virtual: str = ""
    visibility: str = ""
    upsell_ids: str = ""
    crosssell_ids: str = ""
    purchase_note: str = ""
    sale_price_dates_from: str = ""
    sale_price_dates_to: str = ""
    featured: str = ""
    menu_order: str = ""
    
    # Загрузки
    download_limit: str = ""
    download_expiry: str = ""
    downloadable_files: str = ""
    
    # Изображения
    images: str = ""
    
    # Атрибуты (динамические поля, будут добавляться через __post_init__)
    attributes: Dict[str, str] = field(default_factory=dict)
    
    # Мета-поля (динамические поля)
    meta_fields: Dict[str, str] = field(default_factory=dict)
    
    # Ссылки
    product_url: str = ""
    button_text: str = ""
    product_page_url: str = ""
    
    def __post_init__(self):
        """Инициализация динамических полей."""
        if not self.attributes:
            self.attributes = {}
        if not self.meta_fields:
            self.meta_fields = {}
    
    def to_woocommerce_dict(self) -> Dict[str, str]:
        """
        Преобразует продукт в словарь для экспорта в CSV WooCommerce.
        Формат атрибутов: attribute:Гарантийный срок, attribute_data:Гарантийный срок
        """
        result = {}
        
        # print(f"[DEBUG to_woocommerce_dict] Атрибуты ({len(self.attributes)}): {self.attributes}")
        
        # Основные поля
        for field_name in self.__dataclass_fields__.keys():
            if field_name in ['attributes', 'meta_fields']:
                continue
                
            value = getattr(self, field_name, "")
            if field_name.startswith('tax_'):
                csv_field_name = 'tax:' + field_name[4:]
            else:
                csv_field_name = field_name
                
            result[csv_field_name] = value if value is not None else ""
        
        # Атрибуты: генерируем в двух форматах
        for attr_name, attr_value in self.attributes.items():
            # Формат 1: С pa_ slug'ами (для совместимости)
            result[attr_name] = attr_value  # attribute:pa_garantiynyy-srok
            
            # Получаем slug
            if attr_name.startswith('attribute:'):
                attr_slug = attr_name.replace('attribute:', '')
            else:
                attr_slug = attr_name
            
            # Получаем кириллическое название
            readable_name = self._get_attribute_readable_name(attr_slug)
            
            if readable_name:
                # Формат 2: С кириллическими названиями
                cyr_attr_field = f"attribute:{readable_name}"
                cyr_data_field = f"attribute_data:{readable_name}"
                
                result[cyr_attr_field] = attr_value
                result[cyr_data_field] = "0|1|1"
                
                print(f"[DEBUG] Создан атрибут: '{cyr_attr_field}' = '{attr_value}'")

        
        # Мета-поля
        for meta_name, meta_value in self.meta_fields.items():
            result[meta_name] = meta_value if meta_value is not None else ""
        
        return result
    
    def get_csv_header(self) -> List[str]:
        """
        Возвращает заголовок для CSV файла.
        Сохраняет парность attribute:/attribute_data: полей.
        """
        header = []
        
        # 1. Основные поля (не атрибуты)
        basic_fields = []
        for field_name in self.__dataclass_fields__.keys():
            if field_name in ['attributes', 'meta_fields']:
                continue
                
            if field_name == 'tax_status':
                csv_field_name = 'tax_status'
            elif field_name.startswith('tax_'):
                csv_field_name = 'tax:' + field_name[4:]
            else:
                csv_field_name = field_name
                
            basic_fields.append(csv_field_name)
        
        # Сортируем основные поля
        basic_fields.sort()
        header.extend(basic_fields)
        
        # Атрибуты в двух форматах
        for attr_name in self.attributes.keys():
            # Формат 1: С pa_ slug'ами (оригинальный)
            if attr_name not in header:
                header.append(attr_name)
            
            # Добавляем attribute_data: для pa_ формата
            if attr_name.startswith('attribute:'):
                attr_slug = attr_name.replace('attribute:', '')
                data_field = f"attribute_data:{attr_slug}"
            else:
                data_field = f"attribute_data:{attr_name}"
            
            if data_field not in header:
                header.append(data_field)
            
            # Формат 2: С кириллическими названиями
            readable_name = self._get_attribute_readable_name(
                attr_slug if 'attr_slug' in locals() else attr_name
            )
            
            if readable_name:
                cyr_attr_field = f"attribute:{readable_name}"
                cyr_data_field = f"attribute_data:{readable_name}"
                
                if cyr_attr_field not in header:
                    header.append(cyr_attr_field)
                if cyr_data_field not in header:
                    header.append(cyr_data_field)

        
        # 3. Мета-поля
        meta_fields = list(self.meta_fields.keys())
        meta_fields.sort()
        header.extend(meta_fields)
        
        return header  # БЕЗ sorted() в конце!



  # Сортируем для консистентности
    
    def _get_attribute_readable_name(self, attr_slug: str) -> str:
        """
        Преобразует slug атрибута в читаемое имя на кириллице.
        """
        # Полное соответствие slug -> кириллическое название
        exact_mapping = {
            'pa_garantiynyy-srok': 'Гарантийный срок',
            'pa_oblast-primeneniya': 'Область применения',
            'pa_tsvet-korpusa': 'Цвет корпуса',
            'pa_strana-proizvodstva': 'Страна производства',
            'pa_srok-sluzhby': 'Срок службы',
            'pa_seriya': 'Серия',
            'pa_material': 'Материал',
            'pa_tip-tovara': 'Тип товара',
            'pa_moshchnost': 'Мощность',
            'pa_napryazhenie': 'Напряжение',
            'pa_proizvoditel': 'Производитель'
        }
        
        # Ищем точное совпадение
        if attr_slug in exact_mapping:
            return exact_mapping[attr_slug]
        
        # Ищем совпадение без префикса pa_
        clean_slug = attr_slug.replace('pa_', '') if attr_slug.startswith('pa_') else attr_slug
        
        for slug, name in exact_mapping.items():
            if slug.replace('pa_', '') == clean_slug:
                return name
        
        # Если не нашли
        return clean_slug.replace('-', ' ').replace('_', ' ').title()

    


@dataclass
class ProcessingStats:
    """Статистика обработки."""
    total_rows: int = 0
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def start(self):
        """Начинает отсчет времени."""
        self.start_time = datetime.now()
    
    def finish(self):
        """Заканчивает отсчет времени."""
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        """Возвращает длительность обработки в секундах."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Возвращает статистику в виде словаря."""
        return {
            'total_rows': self.total_rows,
            'processed': self.processed,
            'skipped': self.skipped,
            'errors': self.errors,
            'duration_seconds': self.get_duration(),
            'success_rate': (self.processed / self.total_rows * 100) if self.total_rows > 0 else 0
        }