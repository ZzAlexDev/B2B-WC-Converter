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
        
        Returns:
            Словарь, где ключи - это названия колонок CSV WooCommerce
        """
        result = {}
        
        print(f"[DEBUG to_woocommerce_dict] Атрибуты ({len(self.attributes)}): {self.attributes}")

        
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
        
        # Добавляем атрибуты (в правильном формате WooCommerce)
        for attr_name, attr_value in self.attributes.items():
            print(f"[DEBUG] Обрабатываю атрибут: '{attr_name}' = '{attr_value}'")
            
            # attr_name может быть в формате "attribute:pa_xxx" или просто "pa_xxx"
            if attr_name.startswith('attribute:'):
                attr_slug = attr_name.replace('attribute:', '')
                csv_attr_name = attr_name
            else:
                attr_slug = attr_name
                csv_attr_name = f"attribute:{attr_name}"
            
            # 1. Основное поле с значением
            result[csv_attr_name] = attr_value if attr_value is not None else ""
            
            # 2. Поле с метаданными (attribute_data:)
            readable_name = self._get_attribute_readable_name(attr_slug)
            
            if readable_name:
                meta_value = f"name:{readable_name}|value:{attr_value}|visible:1|taxonomy:1"
                result[f"attribute_data:{attr_slug}"] = meta_value
                print(f"[DEBUG] Добавлен attribute_data: {meta_value}")
        
        # Добавляем мета-поля
        for meta_name, meta_value in self.meta_fields.items():
            result[meta_name] = meta_value if meta_value is not None else ""
        
        # КРИТИЧЕСКАЯ ОТЛАДКА: ВЫВЕДИ ФИНАЛЬНЫЙ СЛОВАРЬ
        print(f"\n[DEBUG to_woocommerce_dict ФИНАЛЬНЫЙ СЛОВАРЬ]")
        for key, value in result.items():
            if 'attribute' in key and 'data' not in key:  # Только основные атрибуты
                print(f"  '{key}': '{value}'")
        print(f"Всего полей в словаре: {len(result)}")
        
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
                
    # ОСОБЫЙ СЛУЧАЙ: tax_status должен оставаться tax_status
            if field_name == 'tax_status':
                csv_field_name = 'tax_status'
            elif field_name.startswith('tax_'):
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
    
    def _get_attribute_readable_name(self, attr_slug: str) -> str:
        """
        Преобразует slug атрибута в читаемое имя.
        Пример: "pa_oblast-primeneniya" -> "Область применения"
        
        Args:
            attr_slug: Slug атрибута
            
        Returns:
            Читаемое имя или пустая строка
        """
        print(f"[DEBUG _get_attribute_readable_name] Получил slug: '{attr_slug}'")

        # Простая таблица преобразования (можно вынести в конфиг)
        slug_to_name = {
            'pa_oblast-primeneniya': 'Область применения',
            'pa_tsvet-korpusa': 'Цвет корпуса',
            'pa_strana-proizvodstva': 'Страна производства',
            'pa_garantiynyy-srok': 'Гарантийный срок',
            'pa_srok-sluzhby': 'Срок службы',
            'pa_material': 'Материал',
            'pa_tip-tovara': 'Тип товара',
            'pa_moshchnost': 'Мощность',
            'pa_napryazhenie': 'Напряжение',
            'pa_proizvoditel': 'Производитель',
            'pa_seriya': 'Серия'
        }
        
        # Убираем префикс "pa_" для поиска
        search_slug = attr_slug.replace('pa_', '') if attr_slug.startswith('pa_') else attr_slug
        
        for slug, name in slug_to_name.items():
            if slug.replace('pa_', '') == search_slug:
                return name
        
        # Если не нашли, пытаемся преобразовать из slug
        # "oblast-primeneniya" -> "Область применения"
        if '-' in search_slug:
            words = search_slug.replace('-', ' ').split()
            return ' '.join(word.capitalize() for word in words)
        
        return search_slug.capitalize()    


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