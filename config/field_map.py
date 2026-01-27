"""
config/field_map.py
Маппинг полей между исходным XLSX и WooCommerce CSV
"""

from config.settings import WC_ATTRIBUTES, WC_DEFAULTS

# ======================
# ПРЯМЫЕ СООТВЕТСТВИЯ ПОЛЕЙ
# ======================

# Исходное поле XLSX → Поле WooCommerce CSV
DIRECT_MAPPINGS = {
    # Основные поля
    'Наименование': 'post_title',
    'Артикул': 'sku',
    'Бренд': 'tax:product_brand',
    'Название категории': 'tax:product_cat',
    'Цена': 'regular_price',
    
    # Описание (будет обрабатываться отдельно)
    'Статья': '_raw_description',  # временное поле для обработки
    
    # Изображения (будут обрабатываться отдельно)
    'Изображение': '_raw_images',  # временное поле
}

# ======================
# ПОЛЯ ДЛЯ ОБРАБОТКИ
# ======================

# Поле с характеристиками (будет парситься)
CHARACTERISTICS_FIELD = 'Характеристики'

# Поля с файлами (будут добавляться в описание)
DOCUMENT_FIELDS = [
    'Видеo',
    'Чертежи',
    'Сертификаты',
    'Промоматериалы',
    'Инструкции',
]

# Поля с дополнительной информацией (в описание)
INFO_FIELDS = [
    'НС-код',
    'Штрих код',
    'Эксклюзив',
]

# Поля, которые игнорируем на первом этапе
IGNORED_FIELDS = [
    'Сопут.товар',
    'Аналоги',
]

# ======================
# ПРАВИЛА ПРЕОБРАЗОВАНИЯ
# ======================

# Функции для преобразования значений полей
TRANSFORM_RULES = {
    'Артикул': {
        'function': 'clean_sku',
        'params': {'old': '/', 'new': '-'}
    },
    'Цена': {
        'function': 'clean_price',
        'params': {'patterns': ['руб.', ' ', '₽']}
    },
    'Название категории': {
        'function': 'convert_category',
        'params': {'input_sep': ' - ', 'output_sep': ' > ', 'remove_dups': True}
    },
}

# ======================
# ВЫХОДНЫЕ ПОЛЯ WOOCOMMERCE
# ======================

# Полный список полей для выходного CSV
WC_OUTPUT_FIELDS = [
    # Основные поля
    'ID',
    'post_title',
    'post_name',
    'post_content',
    'post_excerpt',
    'post_status',
    
    # Данные товара
    'sku',
    'parent_sku',
    'regular_price',
    'sale_price',
    'stock',
    'stock_status',
    'backorders',
    'manage_stock',
    'sold_individually',
    'weight',
    'length',
    'width',
    'height',
    'tax_class',
    'tax_status',
    'visibility',
    
    # Таксономии
    'tax:product_cat',
    'tax:product_brand',
    'tax:product_type',
    'tax:product_tag',
    
    # Изображения
    'images',
    
    # Мета-поля
    'meta:_gtin',
    
    # Атрибуты (будут добавляться динамически)
]

# ======================
# ПОЛЯ ДЛЯ ИЗВЛЕЧЕНИЯ ИЗ ХАРАКТЕРИСТИК
# ======================

# Характеристики, которые нужно извлечь в отдельные поля
EXTRACT_FROM_CHARACTERISTICS = {
    'weight': ['Вес товара', 'Масса товара', 'Вес'],
    'width': ['Ширина товара', 'Ширина'],
    'height': ['Высота товара', 'Высота'],
    'length': ['Длина товара', 'Длина', 'Глубина товара', 'Глубина'],
}

# ======================
# УТИЛИТНЫЕ ФУНКЦИИ
# ======================

def get_wc_output_fields_with_attributes():
    """
    Получить полный список полей CSV включая атрибуты
    """
    fields = WC_OUTPUT_FIELDS.copy()
    
    # Добавляем поля для атрибутов WC
    for attribute_slug in WC_ATTRIBUTES.values():
        fields.append(f'attribute:{attribute_slug}')
        fields.append(f'attribute_data:{attribute_slug}')
    
    return fields

def get_required_input_fields():
    """
    Получить список обязательных полей во входном файле
    """
    return list(DIRECT_MAPPINGS.keys()) + [CHARACTERISTICS_FIELD]