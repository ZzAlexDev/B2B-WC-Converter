"""
Тестирование менеджера конфигураций.
"""
import sys
import os
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / "src"))

from v2.config_manager import ConfigManager


def test_config_loading():
    """Тестирование загрузки конфигурации."""
    print("=== Тест ConfigManager ===")
    
    try:
        # Загружаем конфигурацию
        config_manager = ConfigManager.from_directory("config/v2")
        
        print("✅ Конфигурация загружена успешно")
        print(f"ConfigManager: {config_manager}")
        
        # Проверяем основные секции
        print(f"\nПроверка секций конфигурации:")
        print(f"  settings: {'Есть' if config_manager.settings else 'Нет'}")
        print(f"  field_mapping: {len(config_manager.field_mapping)} полей")
        print(f"  attribute_mapping: {len(config_manager.attribute_mapping)} секций")
        print(f"  seo_templates: {'Есть' if config_manager.seo_templates else 'Нет'}")
        
        return config_manager
        
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_setting(config_manager):
    """Тестирование получения настроек."""
    print("\n=== Тест получения настроек ===")
    
    # Тест 1: Получение существующей настройки
    local_image_path = config_manager.get_setting('paths.local_image_download')
    print(f"1. paths.local_image_download: {local_image_path}")
    
    # Тест 2: Получение несуществующей настройки с дефолтом
    non_existent = config_manager.get_setting('paths.non_existent', 'default_value')
    print(f"2. Несуществующая настройка с дефолтом: {non_existent}")
    
    # Тест 3: Получение вложенной настройки
    decimal_separator = config_manager.get_setting('processing.decimal_separator')
    print(f"3. processing.decimal_separator: {decimal_separator}")
    
    # Тест 4: Получение булевой настройки
    skip_on_error = config_manager.get_setting('processing.skip_on_error')
    print(f"4. processing.skip_on_error: {skip_on_error}")


def test_field_mapping(config_manager):
    """Тестирование маппинга полей."""
    print("\n=== Тест маппинга полей ===")
    
    test_fields = [
        "Наименование",
        "НС-код",
        "Бренд",
        "Цена",
        "Несуществующее поле"
    ]
    
    for field in test_fields:
        mapping = config_manager.get_field_mapping(field)
        status = "✅" if mapping else "❌"
        print(f"{status} {field:20} -> {mapping or 'Нет маппинга'}")


def test_attribute_mapping(config_manager):
    """Тестирование маппинга характеристик."""
    print("\n=== Тест маппинга характеристик ===")
    
    test_characteristics = [
        "Масса товара (нетто)",
        "Высота товара",
        "Область применения",
        "Цвет корпуса",
        "Несуществующая характеристика"
    ]
    
    for char in test_characteristics:
        mapping = config_manager.get_attribute_mapping(char)
        status = "✅" if mapping else "❌"
        print(f"{status} {char:25} -> {mapping or 'Нет маппинга'}")


def test_seo_templates(config_manager):
    """Тестирование SEO шаблонов."""
    print("\n=== Тест SEO шаблонов ===")
    
    templates_to_test = [
        "title_template",
        "metadesc_template",
        "focuskw_template",
        "canonical_template"
    ]
    
    for template_name in templates_to_test:
        template = config_manager.get_seo_template(template_name)
        status = "✅" if template else "❌"
        print(f"{status} {template_name:20} -> {template[:50] if template else 'Нет шаблона'}...")
    
    # Тест мета-полей
    print(f"\nМета-поля SEO:")
    meta_fields = config_manager.seo_templates.get('meta_fields', {})
    for meta_field, template in list(meta_fields.items())[:3]:  # Покажем первые 3
        print(f"  {meta_field}: {template[:50]}...")


def test_normalization(config_manager):
    """Тестирование нормализации значений."""
    print("\n=== Тест нормализации значений ===")
    
    test_values = [
        "Да",
        "да",
        "Нет",
        "нет",
        "Yes",
        "No",
        "1",
        "0",
        "Есть",
        "Отсутствует",
        "Неизвестное значение"
    ]
    
    for value in test_values:
        normalized = config_manager.normalize_yes_no_value(value)
        print(f"  '{value}' -> '{normalized}'")


def test_unit_extraction(config_manager):
    """Тестирование извлечения единиц измерения."""
    print("\n=== Тест извлечения единиц измерения ===")
    
    test_strings = [
        "10 кг",
        "5.5 см",
        "1000 мм",
        "2,5 л",
        "220 В",
        "Без единиц",
        "",
        "15.7"
    ]
    
    for test_str in test_strings:
        value, unit = config_manager.extract_unit(test_str)
        print(f"  '{test_str}' -> значение: '{value}', единица: '{unit or 'Нет'}'")


def main():
    """Запуск всех тестов."""
    print("Тестирование ConfigManager B2B-WC Converter v2.0\n")
    
    # Проверяем существование конфигурационных файлов
    config_dir = Path("config/v2")
    if not config_dir.exists():
        print(f"❌ Папка конфигурации не найдена: {config_dir.absolute()}")
        print("Сначала создайте конфигурационные файлы.")
        return
    
    config_files = list(config_dir.glob("*.json"))
    if len(config_files) < 4:
        print(f"❌ Найдено только {len(config_files)} JSON файлов, ожидается 4")
        return
    
    print(f"Найдено конфигурационных файлов: {len(config_files)}")
    
    try:
        config_manager = test_config_loading()
        
        if config_manager:
            test_get_setting(config_manager)
            test_field_mapping(config_manager)
            test_attribute_mapping(config_manager)
            test_seo_templates(config_manager)
            test_normalization(config_manager)
            test_unit_extraction(config_manager)
            
            print("\n✅ Все тесты ConfigManager пройдены успешно!")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании ConfigManager: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()