"""
Модель категории (Category)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional  


@dataclass
class Category:
    """
    Модель категории товаров
    """
    
    id: int  # Временный ID
    name: str  # Название категории
    slug: str = ""  # URL-friendly название
    parent_id: Optional[int] = None  # ID родительской категории
    level: int = 0  # Уровень вложенности (0 - корневая)
    full_path: str = ""  # Полный путь (Родитель > Дочерняя > Внучка)
    
    # Для построения дерева
    children: List['Category'] = field(default_factory=list)
    
    # Статистика
    product_count: int = 0
    
    def __post_init__(self):
        """Инициализация после создания"""
        if not self.slug and self.name:
            # Базовая генерация slug (позже добавим транслитерацию)
            self.slug = self.name.lower().replace(" ", "-")
    
    @classmethod
    def from_string(cls, category_str: str, separator: str = "-") -> List['Category']:
        """
        Создание иерархии категорий из строки
        
        Пример: "Тепловое оборудование - Бытовые - Тепловентиляторы"
        Возвращает: [Category(Тепловое), Category(Бытовые), Category(Тепловентиляторы)]
        """
        if not category_str:
            return []
        
        # Разделяем строку, убираем дубли и пробелы
        parts = [part.strip() for part in category_str.split(separator)]
        
        # Убираем пустые элементы и дубли подряд
        unique_parts = []
        for part in parts:
            if part and (not unique_parts or part != unique_parts[-1]):
                unique_parts.append(part)
        
        # Создаем категории
        categories = []
        for i, part in enumerate(unique_parts):
            category = Category(
                id=i + 1,
                name=part,
                level=i,
                parent_id=i if i > 0 else None
            )
            
            # Формируем полный путь
            if i == 0:
                category.full_path = part
            else:
                category.full_path = f"{categories[i-1].full_path} > {part}"
            
            categories.append(category)
        
        return categories
    
    def to_wc_format(self) -> str:
        """Форматирование для WooCommerce (tax:product_cat)"""
        return self.full_path
    
    def to_dict(self) -> Dict[str, any]:
        """Конвертация в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "level": self.level,
            "parent_id": self.parent_id,
            "full_path": self.full_path,
            "product_count": self.product_count,
            "has_children": len(self.children) > 0
        }


@dataclass
class CategoryTree:
    """
    Дерево категорий для построения иерархии
    """
    
    categories: Dict[int, Category] = field(default_factory=dict)
    root_categories: List[Category] = field(default_factory=list)
    
    def add_category(self, category: Category):
        """Добавление категории в дерево"""
        self.categories[category.id] = category
        
        if category.parent_id is None:
            self.root_categories.append(category)
        else:
            parent = self.categories.get(category.parent_id)
            if parent:
                parent.children.append(category)
    
    def find_category_by_name(self, name: str) -> Optional[Category]:
        """Поиск категории по имени"""
        for category in self.categories.values():
            if category.name == name:
                return category
        return None
    
    def get_all_categories(self) -> List[Category]:
        """Получение всех категорий"""
        return list(self.categories.values())