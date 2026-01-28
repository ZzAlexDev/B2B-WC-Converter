"""
data_processors/attribute_parser.py
Парсер характеристик товаров и группировка по категориям
"""

import re
from typing import Dict, List, Any, Tuple, Optional
import logging
from dataclasses import dataclass
from collections import defaultdict

# Настройка логгера
logger = logging.getLogger(__name__)


@dataclass
class Characteristic:
    """Класс для хранения характеристики"""
    key: str
    value: str
    group: str = ""
    is_wc_attribute: bool = False
    wc_attribute_slug: str = ""
    

class AttributeParser:
    """
    Парсер для обработки характеристик товаров
    """
    
    def __init__(self):
        """
        Инициализация парсера
        """
        # Загружаем настройки при первом использовании
        self._load_settings()
        
        self.stats = {
            'total_characteristics': 0,
            'parsed_characteristics': 0,
            'grouped_characteristics': 0,
            'wc_attributes_found': 0,
        }
        
        logger.info("Инициализирован парсер характеристик")
    
    def _load_settings(self):
        """
        Загрузка настроек из конфигурации
        """
        try:
            from config import settings
            from config import field_map
            
            # Группы характеристик
            self.characteristic_groups = settings.CHARACTERISTIC_GROUPS
            self.default_group = settings.DEFAULT_GROUP
            
            # Атрибуты WooCommerce
            self.wc_attributes = settings.WC_ATTRIBUTES
            
            # Boolean значения
            self.boolean_values = settings.BOOLEAN_VALUES
            
            # Поля для извлечения
            self.extract_fields = field_map.EXTRACT_FROM_CHARACTERISTICS
            
            logger.debug("Настройки загружены успешно")
            
        except ImportError as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            # Значения по умолчанию
            self.characteristic_groups = []
            self.default_group = "Другие характеристики"
            self.wc_attributes = {}
            self.boolean_values = {'да': 'yes', 'нет': 'no'}
            self.extract_fields = {}
    
    def parse_characteristics_string(self, characteristics_str: str) -> List[Tuple[str, str]]:
        """
        Парсинг строки характеристик в список пар (ключ, значение)
        
        Args:
            characteristics_str: Строка характеристик
            
        Returns:
            List[Tuple[str, str]]: Список характеристик
        """
        if not characteristics_str:
            return []
        
        characteristics = []
        
        try:
            # Удаляем начальные/конечные пробелы
            text = characteristics_str.strip()
            
            # Разделяем по точке с запятой
            # Используем более умное разделение чтобы избежать проблем с точками с запятой в значениях
            parts = []
            current_part = ""
            bracket_count = 0
            
            for char in text:
                if char == '(':
                    bracket_count += 1
                elif char == ')':
                    bracket_count -= 1
                
                if char == ';' and bracket_count == 0:
                    if current_part.strip():
                        parts.append(current_part.strip())
                    current_part = ""
                else:
                    current_part += char
            
            # Добавляем последнюю часть
            if current_part.strip():
                parts.append(current_part.strip())
            
            # Если обычное разделение не сработало, используем простой вариант
            if len(parts) <= 1:
                parts = [p.strip() for p in text.split(';') if p.strip()]
            
            # Обрабатываем каждую часть
            for part in parts:
                if not part:
                    continue
                
                # Пытаемся разделить по двоеточию
                if ':' in part:
                    # Ищем первое двоеточие (чтобы избежать проблем с двоеточиями в значениях)
                    colon_pos = part.find(':')
                    key = part[:colon_pos].strip()
                    value = part[colon_pos + 1:].strip()
                    
                    # Удаляем точку с запятой в конце значения если есть
                    value = value.rstrip(';')
                    
                    if key and value:
                        characteristics.append((key, value))
                        self.stats['parsed_characteristics'] += 1
                else:
                    # Если нет двоеточия, добавляем как есть
                    characteristics.append((part, ""))
            
            self.stats['total_characteristics'] = len(characteristics)
            logger.debug(f"Парсинг характеристик: найдено {len(characteristics)}")
            
        except Exception as e:
            logger.error(f"Ошибка парсинга характеристик: {e}")
        
        return characteristics
    
    def _normalize_key(self, key: str) -> str:
        """
        Нормализация ключа характеристики для сравнения
        
        Args:
            key: Исходный ключ
            
        Returns:
            str: Нормализованный ключ (нижний регистр, без лишних символов)
        """
        if not key:
            return ""
        
        # Приводим к нижнему регистру
        normalized = key.lower()
        
        # Удаляем лишние символы
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Удаляем лишние пробелы
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def determine_group(self, key: str) -> str:
        """
        Определение группы для характеристики по ключу
        
        Args:
            key: Ключ характеристики
            
        Returns:
            str: Название группы
        """
        normalized_key = self._normalize_key(key)
        
        # Проверяем каждую группу
        for keywords, group_name in self.characteristic_groups:
            for keyword in keywords:
                if keyword in normalized_key:
                    return group_name
        
        # Если не нашли подходящую группу
        return self.default_group
    
    def is_wc_attribute(self, key: str) -> Tuple[bool, str]:
        """
        Проверка, является ли характеристика атрибутом WooCommerce
        
        Args:
            key: Ключ характеристики
            
        Returns:
            Tuple[bool, str]: (является ли атрибутом, slug атрибута)
        """
        # Проверяем точное соответствие
        if key in self.wc_attributes:
            return True, self.wc_attributes[key]
        
        # Проверяем частичное соответствие (для случаев когда ключи могут немного отличаться)
        normalized_key = self._normalize_key(key)
        
        for wc_key, wc_slug in self.wc_attributes.items():
            normalized_wc_key = self._normalize_key(wc_key)
            
            # Проверяем вхождение
            if normalized_wc_key in normalized_key or normalized_key in normalized_wc_key:
                return True, wc_slug
        
        return False, ""
    
    def normalize_value(self, value: str) -> str:
        """
        Нормализация значения характеристики
        
        Args:
            value: Исходное значение
            
        Returns:
            str: Нормализованное значение
        """
        if not value:
            return ""
        
        value_str = str(value).strip()
        
        # Обработка boolean значений - ДЛЯ АТРИБУТОВ WC оставляем yes/no
        # Но для отображения в описании будем использовать Да/Нет
        
        # Удаление лишних пробелов
        value_str = ' '.join(value_str.split())
        
        return value_str

    
    def parse_and_group(self, characteristics_str: str) -> Dict[str, List[Characteristic]]:
        """
        Парсинг характеристик и группировка по категориям
        
        Args:
            characteristics_str: Строка характеристик
            
        Returns:
            Dict[str, List[Characteristic]]: Характеристики сгруппированные по категориям
        """
        # Сбрасываем статистику
        self.stats = {
            'total_characteristics': 0,
            'parsed_characteristics': 0,
            'grouped_characteristics': 0,
            'wc_attributes_found': 0,
        }
        
        # Парсим характеристики
        raw_characteristics = self.parse_characteristics_string(characteristics_str)
        
        # Группируем
        grouped = defaultdict(list)
        
        for key, value in raw_characteristics:
            # Нормализуем значение
            normalized_value = self.normalize_value(value)
            
            # Определяем группу
            group = self.determine_group(key)
            
            # Проверяем, является ли атрибутом WC
            is_wc_attr, wc_slug = self.is_wc_attribute(key)
            
            if is_wc_attr:
                self.stats['wc_attributes_found'] += 1
            
            # Создаем объект характеристики
            characteristic = Characteristic(
                key=key,
                value=normalized_value,
                group=group,
                is_wc_attribute=is_wc_attr,
                wc_attribute_slug=wc_slug
            )
            
            grouped[group].append(characteristic)
            self.stats['grouped_characteristics'] += 1
        
        logger.debug(f"Группировка завершена: {len(grouped)} групп, {self.stats['grouped_characteristics']} характеристик")
        
        return dict(grouped)
    
    def extract_wc_attributes(self, characteristics_str: str) -> Dict[str, Any]:
        """
        Извлечение атрибутов WooCommerce из характеристик
        
        Args:
            characteristics_str: Строка характеристик
            
        Returns:
            Dict[str, Any]: Атрибуты WC в формате {slug: value}
        """
        grouped = self.parse_and_group(characteristics_str)
        
        wc_attributes = {}
        wc_attributes_data = {}
        
        # Собираем все характеристики из всех групп
        all_characteristics = []
        for group_chars in grouped.values():
            all_characteristics.extend(group_chars)
        
        # Извлекаем атрибуты WC
        for char in all_characteristics:
            if char.is_wc_attribute and char.wc_attribute_slug:
                # Для атрибутов WC нужно специальное форматирование
                wc_attributes[char.wc_attribute_slug] = char.value
                
                # Для attribute_data нужно создать строку настроек
                # Формат: "1:0|0" где 1 - видимость, 0 - не используется для вариаций
                wc_attributes_data[f"{char.wc_attribute_slug}_data"] = "1:0|0"
        
        # Особый случай: атрибут габаритов (объединяем несколько характеристик)
        if 'pa_dimensions' in self.wc_attributes.values():
            dimensions = self._extract_dimensions(all_characteristics)
            if dimensions:
                wc_attributes['pa_dimensions'] = dimensions
                wc_attributes_data['pa_dimensions_data'] = "1:0|0"
        
        logger.debug(f"Извлечено атрибутов WC: {len(wc_attributes)}")
        
        return {
            'attributes': wc_attributes,
            'attributes_data': wc_attributes_data
        }
    
    def _extract_dimensions(self, characteristics: List[Characteristic]) -> Optional[str]:
        """
        Извлечение и объединение габаритов
        
        Args:
            characteristics: Список характеристик
            
        Returns:
            Optional[str]: Строка габаритов или None
        """
        dimensions = {}
        
        # Ищем габаритные характеристики
        for char in characteristics:
            norm_key = self._normalize_key(char.key)
            
            if 'ширин' in norm_key:
                dimensions['width'] = char.value
            elif 'высот' in norm_key:
                dimensions['height'] = char.value
            elif 'глубин' in norm_key or 'длин' in norm_key:
                dimensions['length'] = char.value
        
        # Формируем строку
        if dimensions:
            # Формат: "ШxВxГ" или что есть
            parts = []
            for dim in ['width', 'height', 'length']:
                if dim in dimensions:
                    parts.append(dimensions[dim])
            
            if parts:
                return ' x '.join(parts)
        
        return None
    
    def extract_specific_fields(self, characteristics_str: str) -> Dict[str, str]:
        """
        Извлечение конкретных полей из характеристик (вес, габариты и т.д.)
        
        Args:
            characteristics_str: Строка характеристик
            
        Returns:
            Dict[str, str]: Извлеченные поля
        """
        grouped = self.parse_and_group(characteristics_str)
        
        extracted = {}
        
        # Собираем все характеристики
        all_characteristics = []
        for group_chars in grouped.values():
            all_characteristics.extend(group_chars)
        
        # Ищем поля из конфигурации
        for field_name, field_keys in self.extract_fields.items():
            for char in all_characteristics:
                norm_key = self._normalize_key(char.key)
                
                # Проверяем соответствие ключам поля
                for field_key in field_keys:
                    if self._normalize_key(field_key) in norm_key:
                        extracted[field_name] = char.value
                        break
                
                if field_name in extracted:
                    break
        
        logger.debug(f"Извлечено полей: {list(extracted.keys())}")
        
        return extracted
    
    def format_for_description(self, characteristics_str: str) -> str:
        """
        Форматирование характеристик для HTML описания
        
        Args:
            characteristics_str: Строка характеристик
            
        Returns:
            str: HTML с группировкой характеристик
        """
        grouped = self.parse_and_group(characteristics_str)
        
        if not grouped:
            return ""
        
        html_parts = []
        
        # Сортируем группы для красивого отображения
        group_order = [group_name for keywords, group_name in self.characteristic_groups]
        group_order.append(self.default_group)
        
        # Добавляем только существующие группы в правильном порядке
        for group_name in group_order:
            if group_name in grouped and grouped[group_name]:
                characteristics = grouped[group_name]
                
                # Заголовок группы
                html_parts.append(f'<h4>{group_name}</h4>')
                html_parts.append('<ul>')
                
                # Характеристики группы
                for char in characteristics:
                    html_parts.append(f'<li><strong>{char.key}:</strong> {char.value}</li>')
                
                html_parts.append('</ul>')
        
        # Удаляем последнюю группу если она пустая
        if html_parts and html_parts[-1] == '</ul>':
            # Проверяем что перед </ul> есть характеристики
            pass
        
        html = '\n'.join(html_parts)
        
        # Обертываем в общий блок
        if html:
            html = f'<h3>Технические характеристики</h3>\n{html}'
        
        logger.debug(f"Сформирован HTML описания: {len(html)} символов")
        
        return html
    
    def get_stats(self) -> Dict[str, int]:
        """
        Получение статистики обработки
        
        Returns:
            Dict[str, int]: Статистика
        """
        return self.stats.copy()


# Функции для быстрого использования
def parse_characteristics(characteristics_str: str) -> Dict[str, List[Characteristic]]:
    """
    Быстрый парсинг и группировка характеристик
    
    Args:
        characteristics_str: Строка характеристик
        
    Returns:
        Dict[str, List[Characteristic]]: Сгруппированные характеристики
    """
    parser = AttributeParser()
    return parser.parse_and_group(characteristics_str)


def get_wc_attributes_from_characteristics(characteristics_str: str) -> Dict[str, Any]:
    """
    Быстрое извлечение атрибутов WC из характеристик
    
    Args:
        characteristics_str: Строка характеристик
        
    Returns:
        Dict[str, Any]: Атрибуты WC
    """
    parser = AttributeParser()
    return parser.extract_wc_attributes(characteristics_str)


def format_characteristics_for_description(characteristics_str: str) -> str:
    """
    Быстрое форматирование характеристик для описания
    
    Args:
        characteristics_str: Строка характеристик
        
    Returns:
        str: HTML с характеристиками
    """
    parser = AttributeParser()
    return parser.format_for_description(characteristics_str)

    # ДОБАВИМ НОВЫЙ МЕТОД ДЛЯ ОТОБРАЖЕНИЯ В ОПИСАНИИ:
    def format_value_for_display(self, value: str, is_for_display: bool = True) -> str:
        """
        Форматирование значения для отображения
        
        Args:
            value: Исходное значение
            is_for_display: True - для отображения, False - для атрибутов WC
            
        Returns:
            str: Отформатированное значение
        """
        if not value:
            return ""
        
        value_str = str(value).strip().lower()
        
        if is_for_display:
            # Для отображения в описании
            if value_str == 'yes':
                return 'Да'
            elif value_str == 'no':
                return 'Нет'
            elif value_str == 'true':
                return 'Да'
            elif value_str == 'false':
                return 'Нет'
        else:
            # Для атрибутов WC
            if value_str == 'да':
                return 'yes'
            elif value_str == 'нет':
                return 'no'
        
        return value  # Возвращаем как есть