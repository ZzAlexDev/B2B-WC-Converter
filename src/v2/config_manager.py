"""
Менеджер конфигураций для B2B-WC Converter v2.0.
Загружает и управляет JSON-конфигами из папки config/v2/
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigManager:
    """
    Менеджер конфигураций, загружающий все настройки из JSON файлов.
    """
    
    # Конфигурационные файлы
    settings: Dict[str, Any] = field(default_factory=dict)
    field_mapping: Dict[str, str] = field(default_factory=dict)
    attribute_mapping: Dict[str, Any] = field(default_factory=dict)
    seo_templates: Dict[str, Any] = field(default_factory=dict)
    
    # Кэш для быстрого доступа
    _config_path: Optional[Path] = None
    
    # ДОБАВЬТЕ ЭТОТ КОНСТРУКТОР:
    def __post_init__(self):
        """Инициализация после создания dataclass"""
        if self._config_path:
            self.load_all_configs()
            
            # Отладочная информация
            logger.info(f"Загруженные секции конфигурации: {list(self.settings.keys())}")
            if 'paths' in self.settings:
                logger.info(f"Секция paths содержит: {list(self.settings['paths'].keys())}")
            else:
                logger.warning("Секция 'paths' не найдена в конфигурации!")
    
    @classmethod
    def from_directory(cls, config_path: str) -> 'ConfigManager':
        """
        Создает ConfigManager из папки с конфигурационными файлами.
        
        Args:
            config_path: Путь к папке с конфигурационными файлами
            
        Returns:
            Экземпляр ConfigManager
            
        Raises:
            FileNotFoundError: Если отсутствуют обязательные конфигурационные файлы
            json.JSONDecodeError: Если конфигурационный файл содержит невалидный JSON
        """
        config_dir = Path(config_path)
        
        if not config_dir.exists():
            raise FileNotFoundError(f"Папка конфигурации не найдена: {config_dir}")
        
        logger.info(f"Загрузка конфигурации из: {config_dir}")
        
        # Используем dataclass конструктор
        instance = cls(_config_path=config_dir)
        # load_all_configs вызовется в __post_init__
        
        return instance
    
    def load_all_configs(self) -> None:
        """
        Загружает все конфигурационные файлы из папки.
        """
        if not self._config_path:
            raise ValueError("Путь к конфигурации не установлен")
        
        # Загружаем каждый конфигурационный файл
        self.settings = self._load_config_file("settings.json")
        self.field_mapping = self._load_config_file("field_mapping.json")
        self.attribute_mapping = self._load_config_file("attribute_mapping.json")
        self.seo_templates = self._load_config_file("seo_templates.json")
        
        logger.info(f"Загружено конфигурационных файлов: 4")
        
        # Валидируем обязательные настройки
        self._validate_configs()
    
    def _load_config_file(self, filename: str) -> Dict[str, Any]:
        """
        Загружает конфигурационный файл.
        
        Args:
            filename: Имя файла конфигурации
            
        Returns:
            Содержимое файла в виде словаря
            
        Raises:
            FileNotFoundError: Если файл не найден
            json.JSONDecodeError: Если файл содержит невалидный JSON
        """
        file_path = self._config_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Конфигурационный файл не найден: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            logger.debug(f"Загружен конфигурационный файл: {filename}")
            return config_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {filename}: {e}")
            raise
    
    def _validate_configs(self) -> None:
        """
        Валидирует загруженные конфигурации.
        Проверяет наличие обязательных секций и полей.
        """
        errors = []
        
        # Проверка settings.json
        if not self.settings:
            errors.append("settings.json пуст или не загружен")
        else:
            required_sections = ['paths', 'templates', 'processing', 'default_values']
            for section in required_sections:
                if section not in self.settings:
                    errors.append(f"В settings.json отсутствует секция: {section}")
        
        # Проверка field_mapping.json
        if not self.field_mapping:
            errors.append("field_mapping.json пуст или не загружен")
        
        # Проверка attribute_mapping.json
        if not self.attribute_mapping:
            errors.append("attribute_mapping.json пуст или не загружен")
        else:
            required_sections = ['standard_fields', 'woocommerce_attributes']
            for section in required_sections:
                if section not in self.attribute_mapping:
                    errors.append(f"В attribute_mapping.json отсутствует секция: {section}")
        
        # Проверка seo_templates.json
        if not self.seo_templates:
            errors.append("seo_templates.json пуст или не загружен")
        
        if errors:
            error_msg = "Ошибки валидации конфигурации:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Валидация конфигурации прошла успешно")
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Получает значение из настроек по пути вида 'section.subsection.key'.
        
        Args:
            key_path: Путь к значению (например, 'paths.local_image_download')
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Значение из настроек или default
        """
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                logger.debug(f"Ключ не найден в настройках: {key_path}, используется значение по умолчанию")
                return default
        
        return value
    
    def get_field_mapping(self, source_field: str) -> Optional[str]:
        """
        Получает маппинг для исходного поля.
        
        Args:
            source_field: Исходное поле из CSV
            
        Returns:
            Целевое поле WooCommerce или None
        """
        return self.field_mapping.get(source_field)
    
    def get_attribute_mapping(self, characteristic_name: str) -> Optional[str]:
        """
        Получает маппинг для характеристики.
        
        Args:
            characteristic_name: Название характеристики
            
        Returns:
            Целевое поле WooCommerce или None
        """
        # Проверяем стандартные поля
        standard_fields = self.attribute_mapping.get('standard_fields', {})
        if characteristic_name in standard_fields:
            return standard_fields[characteristic_name]
        
        # Проверяем атрибуты WooCommerce
        woocommerce_attrs = self.attribute_mapping.get('woocommerce_attributes', {})
        if characteristic_name in woocommerce_attrs:
            return woocommerce_attrs[characteristic_name]
        
        return None
    
    def get_seo_template(self, template_name: str) -> Optional[str]:
        """
        Получает SEO шаблон по имени.
        
        Args:
            template_name: Имя шаблона
            
        Returns:
            Шаблон или None
        """
        return self.seo_templates.get(template_name)
    
    def get_meta_field_template(self, meta_field_name: str) -> Optional[str]:
        """
        Получает шаблон для мета-поля.
        
        Args:
            meta_field_name: Имя мета-поля
            
        Returns:
            Шаблон или None
        """
        meta_fields = self.seo_templates.get('meta_fields', {})
        return meta_fields.get(meta_field_name)
    
    def normalize_yes_no_value(self, value: str) -> str:
        """
        Нормализует значения Да/Нет согласно настройкам.
        
        Args:
            value: Исходное значение
            
        Returns:
            Нормализованное значение ('Да' или 'Нет')
        """
        if not value:
            return "Нет"
        
        value_lower = value.lower().strip()
        
        # Получаем списки значений из настроек
        yes_values = self.get_setting('validation.yes_values', ['да', 'yes', '1', 'true'])
        no_values = self.get_setting('validation.no_values', ['нет', 'no', '0', 'false'])
        
        if value_lower in yes_values:
            return "Да"
        elif value_lower in no_values:
            return "Нет"
        
        # Проверяем правила нормализации из attribute_mapping
        normalize_rules = self.attribute_mapping.get('normalize_rules', {})
        if value in normalize_rules:
            return normalize_rules[value]
        
        # Если значение не распознано, возвращаем как есть
        return value
    
    def extract_unit(self, value_str: str) -> tuple[str, Optional[str]]:
        """
        Извлекает числовое значение и единицу измерения.
        
        Args:
            value_str: Строка со значением (например, "10 кг")
            
        Returns:
            Кортеж (числовое значение, единица измерения)
        """
        if not value_str:
            return "", None
        
        # Ищем числовую часть (включая десятичные дроби)
        import re
        match = re.search(r'([0-9]+[.,]?[0-9]*)', value_str.replace(',', '.'))
        
        if not match:
            return value_str, None
        
        numeric_value = match.group(1)
        
        # Ищем единицу измерения
        units_mapping = self.attribute_mapping.get('units_mapping', {})
        
        for unit in units_mapping.keys():
            if unit in value_str.lower():
                return numeric_value, units_mapping.get(unit)
        
        return numeric_value, None
    
    def reload_configs(self) -> None:
        """
        Перезагружает все конфигурационные файлы.
        Полезно при изменении конфигурации во время работы.
        """
        logger.info("Перезагрузка конфигурационных файлов...")
        self.load_all_configs()
        logger.info("Конфигурационные файлы перезагружены")
    
    def __str__(self) -> str:
        """Строковое представление конфигурации."""
        config_files = [
            ("settings.json", len(str(self.settings))),
            ("field_mapping.json", len(self.field_mapping)),
            ("attribute_mapping.json", len(str(self.attribute_mapping))),
            ("seo_templates.json", len(str(self.seo_templates)))
        ]
        
        files_info = ", ".join([f"{name} ({count} байт)" for name, count in config_files])
        return f"ConfigManager: {files_info}"
    

    