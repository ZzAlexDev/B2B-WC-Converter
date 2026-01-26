# config/field_map.py
"""
Маппинг полей из B2B-выгрузки Русклимат в формат WooCommerce.
Каждое правило: 'поле_в_WC': ('поле_в_XLSX', функция_обработки)
Функция обработки получает значение из XLSX и строку всего товара.
Если функция None — значение берётся как есть.
"""
from typing import Any, Callable, Optional

# Базовые функции-помощники для обработки данных
def calculate_price(raw_price: Any) -> float:
    """Обрабатывает цену: удаляет ' руб.', конвертирует в float, применяет наценку."""
    from config.settings import biz_config
    if isinstance(raw_price, str):
        # Удаляем ВСЁ, кроме цифр и точки (включая пробелы, тире, слово 'руб.')
        clean = ''.join(ch for ch in raw_price if ch.isdigit() or ch == '.')
        base_price = float(clean) if clean else 0.0
    else:
        base_price = float(raw_price)
    # УМНОЖАЕМ на коэффициент наценки
    final_price = base_price * biz_config.DELIVERY_MARKUP
    return round(final_price, 2)


def parse_characteristics(raw_chars: str, product_data: dict) -> str:
    """Разбирает строку характеристик для включения в описание.
    Позже мы выделим отсюда отдельные атрибуты."""
    if not raw_chars or not isinstance(raw_chars, str):
        return ""
    # Заменяем точки с запятой на HTML-теги для читаемого списка
    lines = [f"<li>{line.strip()}</li>" for line in raw_chars.split('; ') if line.strip()]
    if lines:
        return "<h3>Технические характеристики:</h3><ul>" + "".join(lines) + "</ul>"
    return ""

def build_description(article_html: str, characteristics_html: str) -> str:
    """Объединяет статью и характеристики в полное описание."""
    parts = []
    if article_html and isinstance(article_html, str):
        parts.append(article_html.strip())
    if characteristics_html:
        parts.append(characteristics_html)
    return "\n\n".join(parts)

def clean_category_path(raw_category: str) -> str:
    """Преобразует 'A - B - C' в 'A > B > C' и убирает дубликаты."""
    if not isinstance(raw_category, str):
        return ''
    # Разделяем, убираем пробелы, фильтруем пустые
    parts = [part.strip() for part in raw_category.split(' - ') if part.strip()]
    # Удаляем последовательные дубликаты
    unique_parts = []
    for part in parts:
        if not unique_parts or part != unique_parts[-1]:
            unique_parts.append(part)
    return ' > '.join(unique_parts)

# ОСНОВНОЙ СЛОВАРЬ МАППИНГА
# Ключ - поле в WooCommerce CSV
# Значение - (поле в XLSX, функция-обработчик)
SUPPLIER_TO_WC_MAP = {
    # Базовые обязательные поля
    'Type': (None, lambda x, p: 'simple'),  # Все товары простые
    'SKU': ('Артикул', None),  # Берём как есть
    'Name': ('Наименование', None),
    'Regular price': ('Цена', lambda val, prod: calculate_price(val)),
    'Categories': ('Название категории', lambda val, p: clean_category_path(val)),
    
    # Поля категорий и атрибутов (первый этап)
    'Categories': ('Название категории', lambda val, p: val.replace(' - ', ' > ') if isinstance(val, str) else val),
    
    # Описание (объединяем "Статья" + "Характеристики")
    'Description': (None, lambda _, prod: build_description(
        prod.get('Статья', ''),
        parse_characteristics(prod.get('Характеристики', ''), prod)
    )),
    
    # Изображения (первый этап - просто ссылки)
    'Images': ('Изображение', lambda val, p: val if isinstance(val, str) else ''),
    
    # Статус наличия (позже доработаем)
    'Stock status': (None, lambda x, p: 'instock'),  # Временно всё "в наличии"
    
    # Атрибуты (Бренд - пример, позже добавим из характеристик)
    'Attribute 1 name': (None, lambda x, p: 'Бренд'),
    'Attribute 1 value(s)': ('Бренд', None),
    'Attribute 1 visible': (None, lambda x, p: '1'),

    # Добавляем обязательные для WooCommerce поля
    'Short description': (None, lambda _, prod: prod.get('Наименование', '')[:150]),  # Первые 150 символов названия
    'Meta title': ('Наименование', None),
    'Meta description': (None, lambda _, prod: f"Купить {prod.get('Наименование', '')} в интернет-магазине"),
    
    # Статусы
    'Stock status': ('НС-код', lambda val, p: 'instock' if val else 'outofstock'),  # Предполагаем, что если есть НС-код - товар есть
    'Backorders allowed?': (None, lambda x, p: 'no'),
    'Sold individually?': (None, lambda x, p: 'no'),
}


# Дополнительная конфигурация для парсинга характеристик
CHARACTERISTICS_TO_ATTRIBUTES = [
    'Бренд',
    'Страна производства',
    'Макс. потребляемая мощность',
    'Цвет корпуса',
    'Гарантийный срок',
    # Добавь здесь другие важные характеристики для выноса в атрибуты
]


