# B2B → WooCommerce Converter

Конвертер каталога товаров из XLSX в формат импорта WooCommerce.

## Установка

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Скопируйте `.env.example` в `.env`
4. Настройте переменные окружения

## Использование

```bash
python main.py convert data/input/catalog.xlsx

**4. `.env.example`:**

```env
# Пути к файлам
INPUT_PATH=data/input/catalog.xlsx
OUTPUT_PATH=data/output/wc_import.csv
TEMP_PATH=data/temp
DOWNLOADS_PATH=data/downloads

# Пути для скачивания
IMAGES_PATH=data/downloads/images

# Настройки сайта
WC_SITE_URL=https://ваш-сайт.ru
WC_UPLOAD_URL=https://ваш-сайт.ru/wp-content/uploads

# Иконки документов
ICON_VIDEO=https://kvanta42.ru/wp-content/uploads/2026/02/video-icon.png
ICON_CERTIFICATE=https://kvanta42.ru/wp-content/uploads/2026/02/certificate-icon.png
ICON_MANUAL=https://kvanta42.ru/wp-content/uploads/2026/02/manual-icon.png
ICON_DRAWING=https://kvanta42.ru/wp-content/uploads/2026/02/drawing-icon.png
ICON_PROMO=https://kvanta42.ru/wp-content/uploads/2026/02/promo-icon.png

# Настройки парсинга
BATCH_SIZE=50
MAX_IMAGE_DOWNLOAD=5
DEFAULT_CURRENCY=RUB

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/converter.log