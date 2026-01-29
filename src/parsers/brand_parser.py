"""
Парсер для колонки "Бренд"
"""

import re
from typing import Dict, Any, Optional  

from .base_parser import BaseParser, ParseResult


class BrandParser(BaseParser):
    """
    Парсер для колонки "Бренд"
    
    Обрабатывает:
    1. Очистка названия бренда
    2. Нормализация (приведение к стандартному виду)
    3. Извлечение из названия товара (если колонка пустая)
    """
    
    # Словарь для нормализации брендов
    BRAND_NORMALIZATION = {
        # Приведение к стандартному написанию
        'ballu': 'Ballu',
        'ballu bfh': 'Ballu',
        'ballu bec': 'Ballu',
        'shuft': 'SHUFT',          
        'royal thermo': 'Royal Thermo',  
        'royalthermo': 'Royal Thermo',   
        'timberk': 'Timberk',
        'neoclima': 'Neoclima',
        'resanta': 'Resanta',
        'уралэнерго': 'Уралэнерго',
        
        # Синонимы
        'balu': 'Ballu',
        'балу': 'Ballu',
        'балуу': 'Ballu',
        'штуфт': 'SHUFT',          
        'роял те́рмо': 'Royal Thermo',
    }
    
    # Ключевые слова брендов для извлечения из названия
    BRAND_KEYWORDS = {
        'ballu': 'Ballu',
        'shuft': 'SHUFT',          
        'royal thermo': 'Royal Thermo',  
        'royalthermo': 'Royal Thermo',   
        'timberk': 'Timberk',
        'neoclima': 'Neoclima',
        'resanta': 'Resanta',
        'electrolux': 'Electrolux',
        'scarlett': 'Scarlett',
        'polaris': 'Polaris',
        'vitek': 'Vitek',
        'bork': 'Bork',
        'tefal': 'Tefal',
        'bosch': 'Bosch',
        'samsung': 'Samsung',
        'lg': 'LG',
        'sony': 'Sony',
        'panasonic': 'Panasonic',
        'philips': 'Philips',
    }
    
    def __init__(self):
        """Инициализация парсера бренда"""
        super().__init__(column_name="Бренд")
    
    def parse(self, value: str, product_name: str = "") -> ParseResult:
        """
        Парсинг бренда
        
        Args:
            value: Значение из колонки "Бренд"
            product_name: Название товара (для извлечения бренда если колонка пустая)
        
        Returns:
            ParseResult с данными:
            {
                "brand": "Нормализованное название бренда",
                "original_brand": "Оригинальное значение",
                "extracted_from_name": True/False,
                "slug": "brand-slug"
            }
        """
        errors = []
        warnings = []
        
        # Очищаем значение
        cleaned_value = self.clean_value(value)
        
        # Пытаемся определить бренд
        brand = None
        extracted_from_name = False
        
        if cleaned_value:
            # Бренд указан в колонке
            brand = self._normalize_brand(cleaned_value)
        elif product_name:
            # Пытаемся извлечь из названия товара
            brand = self._extract_brand_from_name(product_name)
            if brand:
                extracted_from_name = True
                warnings.append(f"Бренд извлечен из названия товара: '{brand}'")
            else:
                warnings.append("Бренд не указан и не найден в названии товара")
        else:
            warnings.append("Бренд не указан")
        
        # Проверяем валидность бренда
        if brand:
            if len(brand) < 2:
                errors.append(f"Название бренда слишком короткое: '{brand}'")
            elif len(brand) > 50:
                warnings.append(f"Название бренда слишком длинное: '{brand}'")
                brand = brand[:50]
        
        # Генерация slug для бренда
        brand_slug = self._generate_brand_slug(brand) if brand else ""
        
        # Подготовка данных
        data = {
            "brand": brand,
            "original_brand": cleaned_value,
            "extracted_from_name": extracted_from_name,
            "slug": brand_slug,
            "has_brand": bool(brand)
        }
        
        return self.create_result(
            data=data,
            original_value=value,
            errors=errors,
            warnings=warnings
        )
    
    def _normalize_brand(self, brand: str) -> str:
        """
        Нормализация названия бренда
        
        Args:
            brand: Исходное название бренда
        
        Returns:
            Нормализованное название
        """
        if not brand:
            return ""
        
        # Приводим к нижнему регистру для поиска в словаре
        brand_lower = brand.lower().strip()
        
        # Ищем в словаре нормализации
        for key, normalized in self.BRAND_NORMALIZATION.items():
            if key in brand_lower:
                return normalized
        
        # Если не нашли в словаре, применяем базовую нормализацию
        # Убираем лишние пробелы
        brand = " ".join(brand.split())
        
        # Капитализация: первая буква заглавная, остальные строчные
        # Но сохраняем аббревиатуры типа "BOSCH", "LG"
        if not brand.isupper():
            # Если не вся строка в верхнем регистре
            words = brand.split()
            normalized_words = []
            
            for word in words:
                if len(word) <= 3 and word.isupper():
                    # Короткие слова в верхнем регистре оставляем как есть (LG, IBM)
                    normalized_words.append(word)
                elif word.istitle() or word.isupper():
                    # Уже правильно капитализированные
                    normalized_words.append(word)
                else:
                    # Приводим к формату с первой заглавной
                    normalized_words.append(word.capitalize())
            
            brand = " ".join(normalized_words)
        
        return brand
    
    def _extract_brand_from_name(self, product_name: str) -> Optional[str]:
        """
        Извлечение бренда из названия товара
        
        Args:
            product_name: Название товара
        
        Returns:
            Название бренда или None
        """
        if not product_name:
            return None
        
        # Приводим к нижнему регистру
        name_lower = product_name.lower()
        
        # Ищем ключевые слова брендов
        for keyword, brand in self.BRAND_KEYWORDS.items():
            if keyword in name_lower:
                # Проверяем что это отдельное слово, а не часть другого слова
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, name_lower):
                    return brand
        
        return None
    
    def _generate_brand_slug(self, brand: str) -> str:
        """
        Генерация slug для бренда
        
        Args:
            brand: Название бренда
        
        Returns:
            Slug
        """
        if not brand:
            return ""
        
        # Приводим к нижнему регистру
        slug = brand.lower()
        
        # Заменяем пробелы и спецсимволы
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        return slug