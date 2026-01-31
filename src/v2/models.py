"""
Модели данных для B2B-WC Converter v2.0
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


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
        Создает RawProduct из строки CSV.
        
        Args:
            row: Словарь с данными строки CSV
            row_number: Номер строки в файле
            
        Returns:
            Экземпляр RawProduct
        """
        # Нормализуем имена колонок (заменяем пробелы и дефисы на подчеркивания)
        normalized_row = {}
        for key, value in row.items():
            # Заменяем специальные символы для создания валидных имен атрибутов
            normalized_key = (
                key.strip()
                .replace(" ", "_")
                .replace("-", "_")
                .replace(".", "")
                .replace("(", "")
                .replace(")", "")
            )
            normalized_row[normalized_key] = value.strip() if value else ""
        
        # Создаем экземпляр класса
        product = cls(row_number=row_number, raw_data=row)
        
        # Заполняем атрибуты из нормализованной строки
        for field_name in cls.__dataclass_fields__.keys():
            if field_name in ['row_number', 'raw_data']:
                continue
                
            csv_field_name = field_name
            if field_name == "НС_код":
                csv_field_name = "НС_код"  # Уже нормализовано
            elif field_name == "Штрих_код":
                csv_field_name = "Штрих_код"
            elif field_name == "Название_категории":
                csv_field_name = "Название_категории"
                
            if csv_field_name in normalized_row:
                setattr(product, field_name, normalized_row[csv_field_name])
        
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
        
        Returns:
            Словарь, где ключи - это названия колонок CSV WooCommerce
        """
        result = {}
        
        # Основные поля
        for field_name in self.__dataclass_fields__.keys():
            if field_name in ['attributes', 'meta_fields']:
                continue
                
            value = getattr(self, field_name, "")
            # Преобразуем названия полей для CSV (tax_product_type -> tax:product_type)
            if field_name.startswith('tax_'):
                csv_field_name = 'tax:' + field_name[4:]
            else:
                csv_field_name = field_name
                
            result[csv_field_name] = value if value is not None else ""
        
        # Добавляем атрибуты
        for attr_name, attr_value in self.attributes.items():
            result[attr_name] = attr_value
        
        # Добавляем мета-поля
        for meta_name, meta_value in self.meta_fields.items():
            result[meta_name] = meta_value
        
        return result
    
    def get_csv_header(self) -> List[str]:
        """
        Возвращает заголовок для CSV файла.
        Включает все поля WooCommerce + динамические атрибуты и мета-поля.
        
        Returns:
            Список названий колонок
        """
        header = []
        
        # Основные поля
        for field_name in self.__dataclass_fields__.keys():
            if field_name in ['attributes', 'meta_fields']:
                continue
                
            if field_name.startswith('tax_'):
                csv_field_name = 'tax:' + field_name[4:]
            else:
                csv_field_name = field_name
                
            header.append(csv_field_name)
        
        # Добавляем атрибуты (уникальные для всех продуктов)
        for attr_name in self.attributes.keys():
            if attr_name not in header:
                header.append(attr_name)
        
        # Добавляем мета-поля (уникальные для всех продуктов)
        for meta_name in self.meta_fields.keys():
            if meta_name not in header:
                header.append(meta_name)
        
        return sorted(header)  # Сортируем для консистентности


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