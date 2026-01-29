"""
Модель товара (Product)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Product:
    """
    Модель товара для внутреннего представления
    """
    
    # Основные поля
    id: int  # Временный ID для связи данных
    name: str = ""  # Наименование
    sku: str = ""  # Основной SKU (НС-код)
    article: str = ""  # Артикул производителя
    
    # Категория и бренд
    category_hierarchy: List[str] = field(default_factory=list)  # ["Тепловое", "Бытовые", "Тепловентиляторы"]
    brand: str = ""  # Бренд
    
    # Цена и коды
    price: float = 0.0
    barcode_raw: str = ""  # Исходный штрихкод
    barcode_clean: str = ""  # Очищенный первый штрихкод
    
    # Характеристики
    specs_raw: str = ""  # Исходная строка характеристик
    specs_dict: Dict[str, str] = field(default_factory=dict)  # Парсированные характеристики
    main_attributes: Dict[str, str] = field(default_factory=dict)  # Основные атрибуты для WC
    
    # Описание
    description_raw: str = ""  # Исходное описание из "Статья"
    description_final: str = ""  # Финальное HTML описание
    
    # Изображения
    images_raw: str = ""  # Исходная строка с URL изображений
    images_local: List[str] = field(default_factory=list)  # Локальные пути к скачанным изображения
    images_wc_format: str = ""  # Форматированная строка для WC
    
    # Документы
    documents: Dict[str, List[str]] = field(default_factory=dict)  # {"сертификаты": [], "инструкции": []}
    documents_html: str = ""  # HTML блок с документацией
    
    # Флаги
    exclusive: bool = False  # Эксклюзивный товар
    
    # WC поля
    wc_slug: str = ""  # post_name (slug)
    wc_fields: Dict[str, Any] = field(default_factory=dict)  # Все поля для WC CSV
    
    # Метаданные
    created_at: datetime = field(default_factory=datetime.now)
    source_row: int = 0  # Номер строки в исходном XLSX
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if not self.sku and self.article:
            self.sku = self.article
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "article": self.article,
            "price": self.price,
            "brand": self.brand,
            "category": " > ".join(self.category_hierarchy) if self.category_hierarchy else "",
            "exclusive": self.exclusive,
            "has_images": len(self.images_local) > 0,
            "has_description": bool(self.description_final),
            "specs_count": len(self.specs_dict)
        }
    
    def validate(self) -> List[str]:
        """
        Валидация товара
        Возвращает список ошибок
        """
        errors = []
        
        if not self.name:
            errors.append("Отсутствует наименование")
        
        if not self.sku:
            errors.append("Отсутствует SKU")
        
        if self.price <= 0:
            errors.append(f"Некорректная цена: {self.price}")
        
        return errors
    
    def get_wc_field(self, field_name: str, default: Any = "") -> Any:
        """Получение поля для WC"""
        return self.wc_fields.get(field_name, default)
    
    def set_wc_field(self, field_name: str, value: Any):
        """Установка поля для WC"""
        self.wc_fields[field_name] = value