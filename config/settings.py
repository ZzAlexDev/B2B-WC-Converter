"""
config/settings.py
Основные настройки обработки данных и бизнес-логика
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# ======================
# КОНСТАНТЫ ИЗ .ENV
# ======================

# Пути к файлам
INPUT_FILE = os.getenv('INPUT_FILE', 'input/catalog.xlsx')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'output/wc_products.csv')
IMAGES_DOWNLOAD_DIR = os.getenv('IMAGES_DOWNLOAD_DIR', 'downloads/images')
DOCS_DOWNLOAD_DIR = os.getenv('DOCS_DOWNLOAD_DIR', 'downloads/documents')
LOG_DIR = os.getenv('LOG_DIR', 'logs')

# Пути для CSV
IMAGES_CSV_PATH = os.getenv('IMAGES_CSV_PATH', '/wp-content/uploads/products/')
ICONS_PATH = os.getenv('ICONS_PATH', '/wp-content/uploads/2026/02/')

# Настройки WooCommerce
DEFAULT_STATUS = os.getenv('DEFAULT_STATUS', 'publish')
DEFAULT_TYPE = os.getenv('DEFAULT_TYPE', 'simple')
DEFAULT_STOCK_STATUS = os.getenv('DEFAULT_STOCK_STATUS', 'instock')
MANAGE_STOCK = os.getenv('MANAGE_STOCK', 'no')

# Настройки обработки
MAX_IMAGES_PER_PRODUCT = int(os.getenv('MAX_IMAGES_PER_PRODUCT', '10'))
SKU_CLEAN_REPLACE = os.getenv('SKU_CLEAN_REPLACE', '/:-').split(':')
TITLE_SLUGIFY = os.getenv('TITLE_SLUGIFY', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
FILE_ENCODING = os.getenv('FILE_ENCODING', 'utf-8')

# ======================
# БИЗНЕС-НАСТРОЙКИ
# ======================

# Настройки обработки CSV
CSV_DELIMITER = ','
CSV_QUOTECHAR = '"'

# Паттерны для очистки цены
PRICE_CLEAN_PATTERNS = ['руб.', ' ', '₽', 'рублей', 'RUB']

# Разделитель категорий для WooCommerce
CATEGORY_SEPARATOR = ' > '
CATEGORY_INPUT_SEPARATOR = ' - '

# Удалять дублирующиеся части в категориях?
REMOVE_DUPLICATE_CATEGORIES = True

# ======================
# ГРУППИРОВКА ХАРАКТЕРИСТИК
# ======================

# Правила группировки характеристик
# Формат: (ключевые_слова, название_группы)
CHARACTERISTIC_GROUPS = [
    # Приоритет 1: Габариты и вес
    (['габарит', 'размер', 'вес', 'масса', 'ширина', 'высота', 'глубина', 'длина', 'толщина'], 
     'Габариты и вес'),
    
    # Приоритет 2: Технические характеристики
    (['мощность', 'напряжение', 'ток', 'частота', 'потребление', 'энергопотребление', 
      'ампер', 'вольт', 'ватт', 'квт', 'ква'], 
     'Технические характеристики'),
    
    # Приоритет 3: Управление
    (['управление', 'термостат', 'таймер', 'дисплей', 'сенсор', 'кнопк', 'пульт', 
      'регулятор', 'переключатель'], 
     'Управление'),
    
    # Приоритет 4: Безопасность
    (['защита', 'безопасность', 'ip', 'влагозащита', 'пылезащита', 'аварийное', 
      'перегрев', 'опрокидывание', 'заземление', 'изоляция'], 
     'Безопасность'),
    
    # Приоритет 5: Монтаж
    (['установка', 'крепление', 'монтаж', 'кабель', 'вилка', 'подключение', 
      'кронштейн', 'крепёж', 'анкер', 'дюбель'], 
     'Монтаж и подключение'),
    
    # Приоритет 6: Комплектация
    (['комплект', 'в комплекте', 'крепеж', 'аксессуар', 'комплектация', 
      'дополнительно', 'принадлежность'], 
     'Комплектация'),
    
    # Приоритет 7: Внешний вид
    (['цвет', 'материал', 'отделка', 'поверхность', 'дизайн', 'форма', 
      'внешний вид', 'оттенок', 'фактура'], 
     'Внешний вид'),
    
    # Приоритет 8: Эксплуатация
    (['применение', 'назначение', 'область', 'площадь', 'эффективен', 
      'использование', 'эксплуатация', 'помещение'], 
     'Эксплуатация'),
    
    # Приоритет 9: Общие сведения
    (['гарантия', 'срок', 'служба', 'производство', 'страна', 'серия', 
      'бренд', 'артикул', 'модель', 'тип'], 
     'Общие сведения'),
]

# Группа по умолчанию (если не попали в другие)
DEFAULT_GROUP = 'Другие характеристики'

# ======================
# АТРИБУТЫ WOOCOMMERCE
# ======================

# Ключевые характеристики, которые станут атрибутами WC (для фильтров)
WC_ATTRIBUTES = {
    'Цвет корпуса': 'pa_color',
    'Материал корпуса': 'pa_material',
    'Мощность': 'pa_power',
    'Страна производства': 'pa_country', 
    'Тип установки': 'pa_installation-type',
    'Область применения': 'pa_application',
    'Габариты': 'pa_dimensions',
}

# Значения для преобразования "Да/Нет"
BOOLEAN_VALUES = {
    'да': 'yes',
    'нет': 'no',
    'yes': 'yes',
    'no': 'no',
    'true': 'yes',
    'false': 'no',
}

# ======================
# ИКОНКИ ДЛЯ ДОКУМЕНТАЦИИ
# ======================

# Соответствие расширений файлов и иконок
FILE_ICONS = {
    '.pdf': 'pdf-icon.png',
    '.doc': 'word-icon.png',
    '.docx': 'word-icon.png',
    '.xls': 'excel-icon.png',
    '.xlsx': 'excel-icon.png',
    '.rar': 'archive-icon.png',
    '.zip': 'archive-icon.png',
    '.7z': 'archive-icon.png',
    '.mp4': 'video-icon.png',
    '.avi': 'video-icon.png',
    '.mov': 'video-icon.png',
}

# Тексты для типов файлов
FILE_TYPE_TEXTS = {
    '.pdf': ' (PDF)',
    '.doc': ' (DOC)',
    '.docx': ' (DOCX)',
    '.xls': ' (XLS)',
    '.xlsx': ' (XLS)',
    '.rar': ' (Архив RAR)',
    '.zip': ' (Архив ZIP)',
    '.7z': ' (Архив 7Z)',
    '.mp4': ' (Видео MP4)',
    '.avi': ' (Видео AVI)',
    '.mov': ' (Видео MOV)',
}

# ======================
# НАСТРОЙКИ ИМЕНОВАНИЯ ФАЙЛОВ
# ======================

# Расширения изображений
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# Максимальная длина имени файла
MAX_FILENAME_LENGTH = 100

# ======================
# ДЕФОЛТНЫЕ ЗНАЧЕНИЯ ДЛЯ WC
# ======================

WC_DEFAULTS = {
    'post_status': DEFAULT_STATUS,
    'product_type': DEFAULT_TYPE,
    'stock_status': DEFAULT_STOCK_STATUS,
    'manage_stock': MANAGE_STOCK,
    'stock': '',  # пусто = неограниченно
    'backorders': 'no',
    'sold_individually': 'no',
    'visibility': 'visible',
    'tax_class': '',
    'tax_status': 'taxable',
}

# ======================
# ВАЛИДАЦИЯ ДАННЫХ
# ======================

# Обязательные поля (должны быть заполнены)
REQUIRED_FIELDS = ['Наименование', 'Артикул', 'Цена']

# Минимальная/максимальная цена (для валидации)
MIN_PRICE = 0
MAX_PRICE = 10000000

# ======================
# УТИЛИТЫ
# ======================

def get_log_file_path():
    """Получить путь к файлу лога"""
    from datetime import datetime
    log_filename = f"conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return os.path.join(LOG_DIR, log_filename)

def get_report_file_path():
    """Получить путь к файлу отчета"""
    from datetime import datetime
    report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return os.path.join(LOG_DIR, report_filename)

# Проверяем существование директорий
os.makedirs(IMAGES_DOWNLOAD_DIR, exist_ok=True)
os.makedirs(DOCS_DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)