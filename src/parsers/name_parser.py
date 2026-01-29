"""
Парсер для колонки "Наименование"
"""

import re
from typing import Dict, Any
import cyrtranslit

from .base_parser import BaseParser, ParseResult


class NameParser(BaseParser):
    """
    Парсер для колонки "Наименование"
    
    Обрабатывает:
    1. Очистка названия
    2. Генерация slug (для post_name в WC)
    3. Извлечение ключевых слов
    """
    
    def __init__(self):
        """Инициализация парсера названия"""
        super().__init__(column_name="Наименование")
    
    def parse(self, value: str) -> ParseResult:
        """
        Парсинг наименования товара
        
        Args:
            value: Значение из колонки "Наименование"
        
        Returns:
            ParseResult с данными:
            {
                "name": "Очищенное название",
                "slug": "slug-для-url",
                "keywords": ["ключевые", "слова"]
            }
        """
        errors = []
        warnings = []
        
        # Очищаем значение
        cleaned_value = self.clean_value(value)
        
        # Проверяем обязательность
        if not cleaned_value:
            errors.append("Наименование не может быть пустым")
            return self.create_result(
                data=None,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        
        try:
            # 1. Очистка названия
            name = self._clean_name(cleaned_value)
            
            # 2. Генерация slug
            slug = self._generate_slug(name)
            
            # 3. Извлечение ключевых слов
            keywords = self._extract_keywords(name)
            
            # Проверка длины
            if len(name) > 200:
                warnings.append(f"Название слишком длинное ({len(name)} символов)")
            
            # Подготовка данных
            data = {
                "name": name,
                "slug": slug,
                "keywords": keywords,
                "length": len(name),
                "word_count": len(name.split())
            }
            
            return self.create_result(
                data=data,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Ошибка при парсинге наименования: {str(e)}")
            return self.create_result(
                data=None,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
    
    def _clean_name(self, name: str) -> str:
        """
        Очистка названия товара
        
        Args:
            name: Исходное название
        
        Returns:
            Очищенное название
        """
        # Убираем лишние пробелы
        name = " ".join(name.split())
        
        # Убираем двойные кавычки
        name = name.replace('"', '').replace('""', '')
        
        # Убираем HTML теги (если есть)
        name = re.sub(r'<[^>]+>', '', name)
        
        # Убираем спецсимволы в начале/конце
        name = name.strip('!@#$%^&*()_+-=[]{}|;:,.<>?/~`')
        
        # Капитализация первого символа каждого слова (опционально)
        # Можно закомментировать если нужно сохранить оригинальный регистр
        # name = name.title()
        
        return name
    
    def _generate_slug(self, name: str) -> str:
        """
        Генерация slug из названия
        
        Args:
            name: Очищенное название
        
        Returns:
            Slug для URL
        """
        # Транслитерация кириллицы
        try:
            # Пробуем использовать cyrtranslit
            slug = cyrtranslit.to_latin(name, 'ru')
        except:
            # Fallback: ручная транслитерация основных символов
            translit_map = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
                'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
                'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
                'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
                'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
                'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
                'э': 'e', 'ю': 'yu', 'я': 'ya',
                'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
                'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
                'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
                'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
                'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch',
                'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
                'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
            }
            
            slug = ''
            for char in name:
                if char in translit_map:
                    slug += translit_map[char]
                else:
                    slug += char
        
        # Приводим к нижнему регистру
        slug = slug.lower()
        
        # Заменяем пробелы и спецсимволы на дефисы
        slug = re.sub(r'[^\w\s-]', '', slug)  # Убираем спецсимволы
        slug = re.sub(r'[-\s]+', '-', slug)  # Заменяем пробелы и множественные дефисы
        slug = slug.strip('-')  # Убираем дефисы с краев
        
        # Обрезаем если слишком длинный
        if len(slug) > 100:
            slug = slug[:100]
            # Убираем обрезанное слово
            if '-' in slug:
                slug = slug[:slug.rfind('-')]
        
        # Если slug пустой (например, только спецсимволы были)
        if not slug:
            slug = f"product-{hash(name) % 10000:04d}"
        
        return slug
    
    def _extract_keywords(self, name: str) -> list:
        """
        Извлечение ключевых слов из названия
        
        Args:
            name: Название товара
        
        Returns:
            Список ключевых слов
        """
        # Убираем стоп-слова
        stop_words = {
            'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а',
            'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же',
            'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от',
            'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже',
            'ну', 'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до',
            'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя',
            'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней',
            'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто',
            'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто',
            'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь',
            'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были',
            'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два',
            'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через',
            'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много', 'разве', 'три',
            'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда',
            'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда',
            'конечно', 'всю', 'между', 'для', 'ballu', 'тепловентилятор', 'конвектор',
            'электрический', 'мини', 'настенный', 'напольный'
        }
        
        # Разбиваем на слова
        words = re.findall(r'\b[\w-]+\b', name.lower())
        
        # Фильтруем стоп-слова и короткие слова
        keywords = [
            word for word in words 
            if (word not in stop_words and len(word) > 2 and not word.isdigit())
        ]
        
        # Убираем дубли
        unique_keywords = []
        for word in keywords:
            if word not in unique_keywords:
                unique_keywords.append(word)
        
        # Ограничиваем количество
        return unique_keywords[:10]