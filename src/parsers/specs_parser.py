"""
Парсер для колонки "Характеристики"
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .base_parser import BaseParser, ParseResult
from src.utils.validators import validate_barcode


@dataclass
class SpecItem:
    """Элемент характеристики"""
    key: str  # Название характеристики
    value: str  # Значение
    normalized_value: str  # Нормализованное значение (Да/Нет)
    is_main_attribute: bool  # Входит в основные атрибуты для WC
    order: int  # Порядковый номер


class SpecsParser(BaseParser):
    """
    Парсер для колонки "Характеристики"
    
    Обрабатывает сложную строку характеристик вида:
    "ключ1: значение1; ключ2: значение2; ..."
    """
    
    def __init__(self, main_attributes: Optional[List[str]] = None):
        """
        Инициализация парсера характеристик
        
        Args:
            main_attributes: Список основных атрибутов для WC
                             Если None - будет загружено из конфига
        """
        super().__init__(column_name="Характеристики")
        
        # Основные атрибуты для WooCommerce
        self.main_attributes = main_attributes or [
            "Область применения",
            "Гарантийный срок",
            "Цвет корпуса",
            "Страна производства",
            "Макс. потребляемая мощность",
            "Масса товара (нетто)",
            "Ширина товара",
            "Глубина товара",
            "Высота товара",
            "Срок службы"
        ]
        
        # Словарь для нормализации значений
                # Словарь для нормализации значений
        self.normalization_map = {
            # Булевы значения - полные совпадения
            "true": "Да",
            "false": "Нет",
            "yes": "Да",
            "no": "Нет",
            "да": "Да",
            "нет": "Нет",
            "есть": "Да",
            "отсутствует": "Нет",
            "имеется": "Да",
            "присутствует": "Да",
            "не имеется": "Нет",
            
            # Сокращения
            "t": "Да",  # иногда true сокращают
            "f": "Нет", # иногда false сокращают
            "y": "Да",  # yes
            "n": "Нет", # no
            
            # Единицы измерения (полные)
            "квт": "кВт",
            "кВт": "кВт",  # уже правильно
            "вт": "Вт",
            "Вт": "Вт",    # уже правильно
            "вольт": "В",
            "в": "В",
            "гц": "Гц",
            "Гц": "Гц",    # уже правильно
            "герц": "Гц",
        }
        
        # Регулярные выражения для извлечения характеристик
        self.patterns = [
            # Стандартный формат: "ключ: значение"
            r'([^:]+?)\s*:\s*([^;]+)(?=;|$)',
            
            # Формат с точкой: "ключ. значение"
            r'([^\.]+?)\s*\.\s*([^;]+)(?=;|$)',
            
            # Формат с тире: "ключ - значение"
            r'([^-]+?)\s*-\s*([^;]+)(?=;|$)',
        ]
    
    def parse(self, value: str) -> ParseResult:
        """
        Парсинг строки характеристик
        
        Args:
            value: Строка характеристик из колонки
        
        Returns:
            ParseResult с данными:
            {
                "all_specs": [SpecItem],  # Все характеристики
                "main_attributes": {ключ: значение},  # Основные атрибуты для WC
                "specs_dict": {ключ: значение},  # Все характеристики как словарь
                "specs_for_description": [{"key":, "value":}],  # Для HTML описания
                "barcode_info": {инфо о штрихкоде},  # Если есть штрихкод
                "stats": {статистика}
            }
        """
        errors = []
        warnings = []
        
        # Очищаем значение
        cleaned_value = self.clean_value(value)
        
        # Если строка пустая
        if not cleaned_value:
            warnings.append("Строка характеристик пустая")
            return self.create_result(
                data=self._create_empty_result(),
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        
        try:
            # 1. Парсим характеристики
            specs_items = self._parse_specs_string(cleaned_value)
            
            if not specs_items:
                errors.append("Не удалось извлечь характеристики из строки")
                return self.create_result(
                    data=self._create_empty_result(),
                    original_value=value,
                    errors=errors,
                    warnings=warnings
                )
            
            # 2. Нормализуем значения
            specs_items = self._normalize_specs_items(specs_items)
            
            # 3. Разделяем на основные и все характеристики
            main_attrs, all_specs = self._separate_main_attributes(specs_items)
            
            # 4. Проверяем наличие штрихкода в характеристиках
            barcode_info = self._extract_barcode_from_specs(specs_items)
            
            # 5. Собираем статистику
            stats = self._collect_stats(specs_items, main_attrs)
            
            # 6. Подготавливаем данные для описания
            specs_for_description = self._prepare_for_description(all_specs)
            
            # 7. Форматируем для HTML (будет использоваться в description_parser)
            html_ready = self._format_for_html(all_specs)
            
            # Подготовка данных
            data = {
                "all_specs": specs_items,  # Все объекты SpecItem
                "main_attributes": main_attrs,  # Основные атрибуты для WC
                "specs_dict": {item.key: item.value for item in specs_items},  # Словарь
                "specs_for_description": specs_for_description,  # Для описания
                "html_ready": html_ready,  # Отформатировано для HTML
                "barcode_info": barcode_info,  # Информация о штрихкоде
                "stats": stats,  # Статистика
            }
            
            # Логирование успеха
            self.logger.debug(f"Распарсено характеристик: {len(specs_items)}, "
                            f"основных: {len(main_attrs)}")
            
            return self.create_result(
                data=data,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Ошибка при парсинге характеристик: {str(e)}")
            self.logger.error(f"Ошибка парсинга характеристик: {e}", exc_info=True)
            return self.create_result(
                data=self._create_empty_result(),
                original_value=value,
                errors=errors,
                warnings=warnings
            )
    
    def _parse_specs_string(self, specs_str: str) -> List[SpecItem]:
        """
        Разбор строки характеристик на отдельные элементы
        
        Args:
            specs_str: Строка характеристик
        
        Returns:
            Список объектов SpecItem
        """
        specs_items = []
        
        # Пробуем разные паттерны для парсинга
        for pattern in self.patterns:
            matches = re.findall(pattern, specs_str, re.IGNORECASE | re.DOTALL)
            
            if matches:
                for idx, (key, val) in enumerate(matches):
                    # Очищаем ключ и значение
                    key_clean = self._clean_key(key.strip())
                    val_clean = self._clean_value_spec(val.strip())
                    
                    if key_clean and val_clean:
                        # Проверяем, не дублируется ли ключ
                        existing_keys = {item.key for item in specs_items}
                        if key_clean not in existing_keys:
                            specs_items.append(SpecItem(
                                key=key_clean,
                                value=val_clean,
                                normalized_value=val_clean,  # Пока без нормализации
                                is_main_attribute=False,  # Определим позже
                                order=idx
                            ))
                
                # Если нашли характеристики - выходим
                if specs_items:
                    break
        
        # Если не нашли по паттернам, пробуем ручной разбор
        if not specs_items:
            specs_items = self._manual_parse(specs_str)
        
        return specs_items
    
    def _manual_parse(self, specs_str: str) -> List[SpecItem]:
        """
        Ручной разбор строки характеристик (fallback метод)
        
        Args:
            specs_str: Строка характеристик
        
        Returns:
            Список объектов SpecItem
        """
        items = []
        
        # Разделяем по точке с запятой
        parts = [p.strip() for p in specs_str.split(';') if p.strip()]
        
        for idx, part in enumerate(parts):
            # Пробуем разделить по двоеточию
            if ':' in part:
                key_val = part.split(':', 1)
                if len(key_val) == 2:
                    key, val = key_val
                    key_clean = self._clean_key(key.strip())
                    val_clean = self._clean_value_spec(val.strip())
                    
                    if key_clean and val_clean:
                        items.append(SpecItem(
                            key=key_clean,
                            value=val_clean,
                            normalized_value=val_clean,
                            is_main_attribute=False,
                            order=idx
                        ))
        
        return items
    
    def _clean_key(self, key: str) -> str:
        """
        Очистка ключа характеристики
        
        Args:
            key: Исходный ключ
        
        Returns:
            Очищенный ключ
        """
        if not key:
            return ""
        
        # Убираем кавычки
        key = key.replace('"', '').replace("'", "")
        
        # Убираем HTML теги
        key = re.sub(r'<[^>]+>', '', key)
        
        # Капитализация первой буквы
        if key and not key[0].isupper():
            key = key[0].upper() + key[1:]
        
        return key
    
    def _clean_value_spec(self, value: str) -> str:
        """
        Очистка значения характеристики
        
        Args:
            value: Исходное значение
        
        Returns:
            Очищенное значение
        """
        if not value:
            return ""
        
        # Убираем кавычки
        value = value.replace('"', '').replace("'", "")
        
        # Убираем HTML теги
        value = re.sub(r'<[^>]+>', '', value)
        
        # Убираем точку с запятой в конце
        value = value.rstrip(';')
        
        # Убираем лишние пробелы
        value = " ".join(value.split())
        
        return value
    
    def _normalize_specs_items(self, items: List[SpecItem]) -> List[SpecItem]:
        """
        Нормализация значений характеристик
        
        Args:
            items: Список характеристик
        
        Returns:
            Нормализованный список
        """
        for item in items:
            original_value = item.value
            val_lower = original_value.lower().strip()
            
            # 1. Сначала проверяем точное совпадение
            if val_lower in self.normalization_map:
                item.normalized_value = self.normalization_map[val_lower]
                continue
            
            # 2. Проверяем булевы значения в начале/конце строки
            # Пример: "Да (с вилкой)" → "Да"
            bool_words = ['да', 'нет', 'yes', 'no', 'true', 'false', 'есть', 'отсутствует']
            for bool_word in bool_words:
                if val_lower.startswith(bool_word + ' ') or val_lower.endswith(' ' + bool_word):
                    if bool_word in self.normalization_map:
                        item.normalized_value = self.normalization_map[bool_word]
                        break
                elif bool_word == val_lower:
                    if bool_word in self.normalization_map:
                        item.normalized_value = self.normalization_map[bool_word]
                        break
            
            if item.normalized_value != original_value:
                continue  # Уже нормализовали
            
            # 3. Проверяем частичные совпадения для единиц измерения
            # Пример: "1.5 квт" → "1.5 кВт"
            normalized_value = original_value
            
            # Единицы измерения
            unit_replacements = [
                ('квт', 'кВт'),
                ('квт.', 'кВт'),
                ('вт', 'Вт'),
                ('вт.', 'Вт'),
                ('вольт', 'В'),
                ('вольт.', 'В'),  # Без точки после В
                ('гц', 'Гц'),
                ('гц.', 'Гц'),
                ('герц', 'Гц'),
                ('герц.', 'Гц'),
                ('кг', 'кг'),
                ('кг.', 'кг'),
                ('гр', 'г'),
                ('гр.', 'г'),
                ('см', 'см'),
                ('см.', 'см'),
                ('мм', 'мм'),
                ('мм.', 'мм'),
                ('м', 'м'),
                ('м.', 'м'),
            ]

            # Работаем с копией в нижнем регистре для поиска
            temp_lower = normalized_value.lower()
            
            for old, new in unit_replacements:
                if old in temp_lower:
                    # Находим все вхождения
                    pattern = re.compile(re.escape(old), re.IGNORECASE)
                    normalized_value = pattern.sub(new, normalized_value)
                    # Обновляем temp_lower для следующей итерации
                    temp_lower = normalized_value.lower()
            
            # 4. Заменяем "false" и "true" в любом месте строки
            temp_lower = normalized_value.lower()
            if 'true' in temp_lower:
                normalized_value = normalized_value.replace('true', 'Да').replace('True', 'Да')
            if 'false' in temp_lower:
                normalized_value = normalized_value.replace('false', 'Нет').replace('False', 'Нет')
            if 'yes' in temp_lower:
                normalized_value = normalized_value.replace('yes', 'Да').replace('Yes', 'Да')
            if 'no' in temp_lower:
                normalized_value = normalized_value.replace('no', 'Нет').replace('No', 'Нет')
            
            # 5. Капитализация "да" и "нет"
            temp_lower = normalized_value.lower()
            if temp_lower == 'да':
                normalized_value = 'Да'
            elif temp_lower == 'нет':
                normalized_value = 'Нет'
            elif temp_lower == 'есть':
                normalized_value = 'Да'
            elif temp_lower == 'отсутствует':
                normalized_value = 'Нет'
            
            # 6. Убираем точку после единиц измерения (ФИКС ДЛЯ "220 В.")
            # Сначала с пробелом, потом без пробела
            units_to_clean = ['В', 'кВт', 'Вт', 'Гц', 'кг', 'г', 'см', 'мм', 'м']
            
            for unit in units_to_clean:
                # Вариант с пробелом: " В." → " В"
                with_space = f' {unit}.'
                if with_space in normalized_value:
                    normalized_value = normalized_value.replace(with_space, f' {unit}')
                
                # Вариант без пробела: "В." → "В"
                without_space = f'{unit}.'
                if without_space in normalized_value:
                    normalized_value = normalized_value.replace(without_space, unit)
            
            item.normalized_value = normalized_value
        
        return items

    def _separate_main_attributes(self, items: List[SpecItem]) -> Tuple[Dict[str, str], List[SpecItem]]:
        """
        Разделение на основные атрибуты и все характеристики
        
        Args:
            items: Все характеристики
        
        Returns:
            Кортеж (основные_атрибуты, все_характеристики)
        """
        main_attrs = {}
        
        for item in items:
            # Проверяем, входит ли в основные атрибуты
            is_main = any(main_attr.lower() in item.key.lower() 
                         for main_attr in self.main_attributes)
            
            item.is_main_attribute = is_main
            
            if is_main:
                main_attrs[item.key] = item.normalized_value
        
        return main_attrs, items
    
    def _extract_barcode_from_specs(self, items: List[SpecItem]) -> Dict[str, Any]:
        """
        Извлечение информации о штрихкоде из характеристик
        
        Args:
            items: Список характеристик
        
        Returns:
            Информация о штрихкоде
        """
        barcode_info = {
            "found": False,
            "value": "",
            "clean": "",
            "key": ""
        }
        
        # Ключи, которые могут содержать штрихкод
        barcode_keys = ["штрихкод", "штрих код", "ean", "upc", "barcode", "код"]
        
        for item in items:
            key_lower = item.key.lower()
            
            # Проверяем, содержит ли ключ упоминание штрихкода
            if any(barcode_key in key_lower for barcode_key in barcode_keys):
                barcode_info["found"] = True
                barcode_info["value"] = item.value
                barcode_info["key"] = item.key
                
                # Валидируем штрихкод
                clean_barcode, errors = validate_barcode(item.value)
                barcode_info["clean"] = clean_barcode
                barcode_info["errors"] = errors
                
                break
        
        return barcode_info
    
    def _collect_stats(self, items: List[SpecItem], main_attrs: Dict[str, str]) -> Dict[str, Any]:
        """
        Сбор статистики по характеристикам
        
        Args:
            items: Все характеристики
            main_attrs: Основные атрибуты
        
        Returns:
            Словарь со статистикой
        """
        return {
            "total_specs": len(items),
            "main_attributes_count": len(main_attrs),
            "has_barcode": any("штрих" in item.key.lower() for item in items),
            "specs_keys": [item.key for item in items],
            "main_attributes_keys": list(main_attrs.keys())
        }
    
    def _prepare_for_description(self, items: List[SpecItem]) -> List[Dict[str, str]]:
        """
        Подготовка характеристик для HTML описания
        
        Args:
            items: Все характеристики
        
        Returns:
            Список словарей для описания
        """
        description_specs = []
        
        for item in items:
            description_specs.append({
                "key": item.key,
                "value": item.normalized_value,
                "is_main": item.is_main_attribute
            })
        
        return description_specs
    
    def _format_for_html(self, items: List[SpecItem]) -> str:
        """
        Форматирование характеристик для HTML
        
        Args:
            items: Все характеристики
        
        Returns:
            HTML строка
        """
        if not items:
            return ""
        
        html_lines = ["<h2>Технические характеристики</h2>", "<ul>"]
        
        for item in items:
            html_lines.append(
                f'<li><strong>{item.key}:</strong> {item.normalized_value}</li>'
            )
        
        html_lines.append("</ul>")
        
        return "\n".join(html_lines)
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Создание пустого результата"""
        return {
            "all_specs": [],
            "main_attributes": {},
            "specs_dict": {},
            "specs_for_description": [],
            "html_ready": "",
            "barcode_info": {"found": False, "value": "", "clean": "", "key": ""},
            "stats": {
                "total_specs": 0,
                "main_attributes_count": 0,
                "has_barcode": False,
                "specs_keys": [],
                "main_attributes_keys": []
            }
        }
    

    def normalize_value(self, value: str) -> str:
        """
        Нормализация отдельного значения (для тестирования)
        
        Args:
            value: Значение для нормализации
        
        Returns:
            Нормализованное значение
        """
        if not value:
            return ""
        
        original_value = value
        val_lower = original_value.lower().strip()
        
        # 1. Сначала проверяем точное совпадение
        if val_lower in self.normalization_map:
            return self.normalization_map[val_lower]
        
        # 2. Проверяем булевы значения
        bool_words = ['да', 'нет', 'yes', 'no', 'true', 'false', 'есть', 'отсутствует']
        for bool_word in bool_words:
            if val_lower == bool_word and bool_word in self.normalization_map:
                return self.normalization_map[bool_word]
        
        # 3. Проверяем единицы измерения
        normalized_value = original_value
        
        # Единицы измерения
        unit_replacements = [
            (' квт', ' кВт'),
            (' квт.', ' кВт'),
            (' вт', ' Вт'),
            (' вт.', ' Вт'),
            (' вольт', ' В'),
            (' вольт.', ' В'),  # ← БЕЗ ТОЧКИ
            (' гц', ' Гц'),
            (' гц.', ' Гц'),
            (' герц', ' Гц'),
            (' герц.', ' Гц'),
            (' кг', ' кг'),
            (' кг.', ' кг'),
            (' гр', ' г'),
            (' гр.', ' г'),
            (' см', ' см'),
            (' см.', ' см'),
            (' мм', ' мм'),
            (' мм.', ' мм'),
            (' м', ' м'),
            (' м.', ' м'),
        ]
        
        for old, new in unit_replacements:
            if old in val_lower:
                # Заменяем с сохранением регистра
                if old in normalized_value.lower():
                    idx = normalized_value.lower().find(old)
                    normalized_value = normalized_value[:idx] + new + normalized_value[idx+len(old):]
        
        # 4. Заменяем английские булевы значения
        if 'true' in val_lower:
            normalized_value = normalized_value.replace('true', 'Да').replace('True', 'Да')
        if 'false' in val_lower:
            normalized_value = normalized_value.replace('false', 'Нет').replace('False', 'Нет')
        if 'yes' in val_lower:
            normalized_value = normalized_value.replace('yes', 'Да').replace('Yes', 'Да')
        if 'no' in val_lower:
            normalized_value = normalized_value.replace('no', 'Нет').replace('No', 'Нет')
        
        # 5. Капитализация русских булевых значений
        if val_lower == 'да':
            normalized_value = 'Да'
        elif val_lower == 'нет':
            normalized_value = 'Нет'
        elif val_lower == 'есть':
            normalized_value = 'Да'
        elif val_lower == 'отсутствует':
            normalized_value = 'Нет'
        
        # 6. Убираем точку после единиц измерения (ДОБАВИТЬ ЭТО!)
        # Сначала с пробелом, потом без пробела
        units_to_clean = ['В', 'кВт', 'Вт', 'Гц', 'кг', 'г', 'см', 'мм', 'м']
        
        for unit in units_to_clean:
            # Вариант с пробелом: " В." → " В"
            with_space = f' {unit}.'
            if with_space in normalized_value:
                normalized_value = normalized_value.replace(with_space, f' {unit}')
            
            # Вариант без пробела: "В." → "В"
            without_space = f'{unit}.'
            if without_space in normalized_value:
                normalized_value = normalized_value.replace(without_space, unit)
        
        return normalized_value