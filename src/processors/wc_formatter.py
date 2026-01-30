"""
Форматирование товара для WooCommerce CSV импорта
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from src.core.models.product import Product
from src.utils.logger import get_logger


class WCFormatter:
    """
    Форматирование данных товара для WooCommerce CSV
    """
    
    # Стандартные поля WooCommerce CSV
    WC_CSV_FIELDS = [
        "ID",
        "post_title",           # Название товара
        "post_name",            # Slug (URL)
        "post_content",         # Полное описание
        "post_excerpt",         # Короткое описание
        "post_status",          # Статус (publish/draft)
        "comment_status",       # Комментарии (closed)
        "sku",                  # Артикул
        "regular_price",        # Цена
        "sale_price",           # Цена со скидкой
        "tax:product_type",     # Тип товара (simple/variable)
        "tax:product_cat",      # Категория
        "tax:product_brand",    # Бренд
        "images",               # Изображения
        "stock_status",         # Наличие (instock/outofstock)
        "downloadable",         # Цифровой товар (no)
        "virtual",              # Виртуальный товар (no)
        "backorders",           # Предзаказ (no)
        "sold_individually",    # Продавать поштучно (no)
        "manage_stock",         # Управлять запасами (no)
        "stock_quantity",       # Количество
        "tax_status",           # Налоги (taxable)
        "weight",               # Вес
        "length",               # Длина
        "width",                # Ширина
        "height",               # Высота
        "post_date",            # Дата публикации
        "post_author",          # Автор
        "menu_order",           # Порядок
        "_barcode",             # Штрихкод
        "_exclusive",           # Эксклюзивный товар
    ]
    
    # Дополнительные атрибуты (будут добавлены динамически)
    ATTRIBUTE_FIELDS = [
        "attribute:pa_цвет-корпуса",
        "attribute:pa_страна-производства",
        "attribute:pa_гарантийный-срок",
        "attribute:pa_область-применения",
        "attribute:pa_макс-потреб-мощность",
        "attribute:pa_масса-товара-нетто",
        "attribute:pa_ширина-товара",
        "attribute:pa_глубина-товара",
        "attribute:pa_высота-товара",
        "attribute:pa_срок-службы",
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация форматтера
        
        Args:
            config: Конфигурация из settings.json
        """
        self.logger = get_logger()
        self.config = config or {}
        
        # Загружаем маппинг полей
        self.field_mapping = self._load_field_mapping()
    
    def _load_field_mapping(self) -> Dict[str, str]:
        """Загрузка маппинга полей из конфига"""
        try:
            with open("config/wc_fields.json", "r", encoding="utf-8") as f:
                wc_config = json.load(f)
                return wc_config.get("field_mapping", {})
        except:
            self.logger.warning("Не удалось загрузить wc_fields.json, используется маппинг по умолчанию")
            return {}
    
    def format_product(self, product: Product) -> Dict[str, str]:
        """
        Форматирование товара для WC CSV
        
        Args:
            product: Объект товара
        
        Returns:
            Словарь с полями для CSV строки
        """
        try:
            self.logger.debug(f"Форматирование товара #{product.id} для WC")
            
            # Начинаем с пустого словаря
            csv_row = {field: "" for field in self.WC_CSV_FIELDS}
            
            # 1. Заполняем основные поля из wc_fields товара
            for wc_field, value in product.wc_fields.items():
                if wc_field in csv_row:
                    csv_row[wc_field] = self._format_value(value)
                elif wc_field.startswith("attribute:pa_"):
                    # Атрибуты добавляем динамически
                    csv_row[wc_field] = self._format_value(value)
            
            # 2. Заполняем обязательные поля если их нет
            self._fill_required_fields(csv_row, product)
            
            # 3. Обрабатываем изображения
            self._process_images(csv_row, product)
            
            # 4. Обрабатываем категории
            self._process_categories(csv_row, product)
            
            # 5. Обрабатываем атрибуты
            self._process_attributes(csv_row, product)
            
            # 6. Обрабатываем даты
            self._process_dates(csv_row)
            
            # 7. Обрабатываем дополнительные поля
            self._process_extra_fields(csv_row, product)
            
            # 8. Убираем пустые атрибуты (чтобы не засорять CSV)
            self._clean_empty_attributes(csv_row)
            
            return csv_row
            
        except Exception as e:
            self.logger.error(f"Ошибка форматирования товара #{product.id}: {e}")
            raise
    
    # def _format_value(self, value: Any) -> str:
    #     """
    #     Форматирование значения для CSV
        
    #     Args:
    #         value: Любое значение
        
    #     Returns:
    #         Строка для CSV
    #     """
    #     if value is None:
    #         return ""
        
    #     # Приводим к строке
    #     value_str = str(value)
        
    #     # Экранируем кавычки для CSV
    #     if '"' in value_str or ',' in value_str or '\n' in value_str:
    #         value_str = f'"{value_str.replace("\"", "\"\"")}"'

        
    #     return value_str

    def _format_value(self, value: Any) -> str:
        """
        Форматирование значения для CSV.
        
        Args:
            value: Любое значение.
        
        Returns:
            Строка, безопасная для формата CSV.
        """
        if value is None:
            return ""
        
        value_str = str(value)
        
        # 1. Заменяем HTML-сущности на читаемые символы
        html_entities = {'&nbsp;': ' ', '&plusmn;': '±', '&deg;': '°'}
        for entity, replacement in html_entities.items():
            value_str = value_str.replace(entity, replacement)
        
        # 2. "Чистим" разрывы строк: заменяем 3+ подряд на 2
        import re
        value_str = re.sub(r'\n{3,}', '\n\n', value_str)
        
        # 3. Экранируем двойные кавычки (ПРАВИЛО CSV)
        value_str = value_str.replace('"', '""')
        
        # 4. Проверяем, нужно ли оборачивать ячейку в кавычки
        #    (если есть запятая, кавычка или перенос строки)
        if ',' in value_str or '"' in value_str or '\n' in value_str:
            value_str = f'"{value_str}"'
        
        return value_str    
    
    def _fill_required_fields(self, csv_row: Dict[str, str], product: Product):
        """Заполнение обязательных полей если они пустые"""
        # ID
        if not csv_row["ID"]:
            csv_row["ID"] = str(product.id)
        
        # Название
        if not csv_row["post_title"] and product.name:
            csv_row["post_title"] = product.name
        
        # Slug
        if not csv_row["post_name"] and product.wc_slug:
            csv_row["post_name"] = product.wc_slug
        
        # Описание
        if not csv_row["post_content"] and product.description_final:
            csv_row["post_content"] = product.description_final
        
        # Короткое описание
        if not csv_row["post_excerpt"] and product.wc_fields.get("post_excerpt"):
            csv_row["post_excerpt"] = product.wc_fields["post_excerpt"]
        
        # SKU
        if not csv_row["sku"] and product.sku:
            csv_row["sku"] = product.sku
        
        # Цена
        if not csv_row["regular_price"] and product.price:
            csv_row["regular_price"] = f"{product.price:.2f}"
        
        # Категория
        if not csv_row["tax:product_cat"] and product.category_hierarchy:
            csv_row["tax:product_cat"] = " > ".join(product.category_hierarchy)
        
        # Бренд
        if not csv_row["tax:product_brand"] and product.brand:
            csv_row["tax:product_brand"] = product.brand
    
    def _process_images(self, csv_row: Dict[str, str], product: Product):
        """Обработка изображений"""
        if product.images_wc_format:
            csv_row["images"] = product.images_wc_format
        elif product.images_local:
            # Форматируем локальные пути
            image_urls = []
            for i, img_path in enumerate(product.images_local):
                alt_text = f"{product.name} - фото {i+1}"
                image_urls.append(f"{img_path} ! alt: {alt_text}")
            
            if image_urls:
                csv_row["images"] = " | ".join(image_urls)
    
    def _process_categories(self, csv_row: Dict[str, str], product: Product):
        """Обработка категорий"""
        # Убедимся что категория в правильном формате
        if csv_row["tax:product_cat"]:
            # Заменяем разные разделители на стандартный " > "
            cat_str = csv_row["tax:product_cat"]
            separators = ['-', '–', '—', '/', '\\', '|']
            for sep in separators:
                cat_str = cat_str.replace(sep, ' > ')
            
            # Убираем множественные " > "
            while ' >  > ' in cat_str:
                cat_str = cat_str.replace(' >  > ', ' > ')
            
            csv_row["tax:product_cat"] = cat_str.strip()
    
    def _process_attributes(self, csv_row: Dict[str, str], product: Product):
        """Обработка атрибутов из характеристик"""
        if not product.main_attributes:
            return
        
        # Добавляем основные атрибуты
        for attr_name, attr_value in product.main_attributes.items():
            # Генерируем slug для имени атрибута
            attr_slug = self._slugify_attribute(attr_name)
            field_name = f"attribute:pa_{attr_slug}"
            
            # Добавляем поле если его еще нет
            if field_name not in csv_row:
                csv_row[field_name] = attr_value


    # Словарь для сокращения часто используемых слов
            
    
    def _slugify_attribute(self, text: str) -> str:
        """
        Генерация slug для имени атрибута с ограничением длины
        
        Args:
            text: Исходный текст
        
        Returns:
            Slug для использования в имени поля (макс 27 символов)
        """
        import re
        
        # Если текст пустой
        if not text or not text.strip():
            return f"attr_{hash(text) % 1000:04d}"
        
        # 1. Транслитерация кириллицы (упрощенная)
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        
        # Приводим к нижнему регистру
        text_lower = text.lower()
        
        # Транслитерируем
        transliterated = ""
        for char in text_lower:
            if char in translit_map:
                transliterated += translit_map[char]
            else:
                transliterated += char
        
        # 2. Убираем все кроме букв, цифр и дефиса
        slug = re.sub(r'[^\w\s-]', '', transliterated)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # 3. СОКРАЩАЕМ ДЛИННЫЕ SLUG (макс 27 символов!)
        MAX_SLUG_LENGTH = 27  # WooCommerce требует < 28
        
        if len(slug) > MAX_SLUG_LENGTH:
            # Пробуем сократить умно
            if '-' in slug:
                # Разбиваем по дефисам и берем первые буквы
                parts = slug.split('-')
                shortened_parts = []
                
                for part in parts:
                    if len(part) > 4:
                        # Берем первые 3-4 буквы длинных слов
                        shortened_parts.append(part[:4])
                    else:
                        shortened_parts.append(part)
                
                # Собираем обратно
                slug = '-'.join(shortened_parts)
                
                # Если все еще длинный - берем первые слова
                if len(slug) > MAX_SLUG_LENGTH:
                    # Берем только первые 3 слова
                    first_parts = slug.split('-')[:3]
                    slug = '-'.join(first_parts)
            
            # Если все еще длинный - жесткое обрезание
            if len(slug) > MAX_SLUG_LENGTH:
                slug = slug[:MAX_SLUG_LENGTH]
                # Убираем обрезанный дефис в конце
                if slug.endswith('-'):
                    slug = slug[:-1]
        
        # 4. Если slug пустой - генерируем короткий
        if not slug:
            # Создаем короткий slug на основе хеша
            import hashlib
            hash_obj = hashlib.md5(text.encode('utf-8'))
            hash_hex = hash_obj.hexdigest()[:6]
            slug = f"attr_{hash_hex}"
        
        # 5. Убеждаемся что нет двойных дефисов
        slug = re.sub(r'--+', '-', slug)
        
        return slug.lower()



    
    def _process_dates(self, csv_row: Dict[str, str]):
        """Обработка дат публикации"""
        # Дата публикации (по умолчанию из конфига или текущая)
        if not csv_row["post_date"]:
            default_dates = self.config.get("wc", {}).get("default_values", {})
            post_date_start = default_dates.get("post_date_start", "")
            
            if post_date_start:
                csv_row["post_date"] = post_date_start
            else:
                # Генерируем последовательные даты чтобы товары не публиковались все сразу
                import time
                base_timestamp = int(time.time())
                offset = int(csv_row.get("ID", 0)) * 60  # 1 минута между товарами
                publish_time = base_timestamp + offset
                
                from datetime import datetime
                csv_row["post_date"] = datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d %H:%M:%S")
    
    def _process_extra_fields(self, csv_row: Dict[str, str], product: Product):
        """Обработка дополнительных полей"""
        # Штрихкод
        if product.barcode_clean:
            csv_row["_barcode"] = product.barcode_clean
        elif product.barcode_raw:
            csv_row["_barcode"] = product.barcode_raw
        
        # Эксклюзивный товар
        csv_row["_exclusive"] = "Да" if product.exclusive else "Нет"
        
        # Вес и габариты из характеристик
        if product.main_attributes:
            weight = product.main_attributes.get("Масса товара (нетто)", "")
            width = product.main_attributes.get("Ширина товара", "")
            depth = product.main_attributes.get("Глубина товара", "")
            height = product.main_attributes.get("Высота товара", "")
            
            if weight:
                # Пытаемся извлечь число
                import re
                weight_match = re.search(r'(\d+\.?\d*)', weight)
                if weight_match:
                    csv_row["weight"] = weight_match.group(1)
            
            if width:
                width_match = re.search(r'(\d+\.?\d*)', width)
                if width_match:
                    csv_row["width"] = width_match.group(1)
            
            if height:
                height_match = re.search(r'(\d+\.?\d*)', height)
                if height_match:
                    csv_row["height"] = height_match.group(1)
            
            if depth:
                depth_match = re.search(r'(\d+\.?\d*)', depth)
                if depth_match:
                    csv_row["length"] = depth_match.group(1)  # В WC длина = глубина
    
    def _clean_empty_attributes(self, csv_row: Dict[str, str]):
        """Удаление пустых атрибутов из CSV строки"""
        # Находим все атрибуты
        attr_fields = [field for field in csv_row.keys() if field.startswith("attribute:pa_")]
        
        # Удаляем пустые
        for attr_field in attr_fields:
            if not csv_row[attr_field]:
                del csv_row[attr_field]
    
    def get_csv_headers(self, products: List[Product] = None) -> List[str]:
        """
        Получение заголовков для CSV файла
        
        Args:
            products: Список товаров для определения всех атрибутов
        
        Returns:
            Список заголовков CSV
        """
        # Базовые заголовки
        headers = list(self.WC_CSV_FIELDS)
        
        # Добавляем атрибуты из конфига
        headers.extend(self.ATTRIBUTE_FIELDS)
        
        # Если есть товары - добавляем их уникальные атрибуты
        if products:
            all_attributes = set()
            for product in products:
                for attr_name in product.main_attributes.keys():
                    attr_slug = self._slugify_attribute(attr_name)
                    field_name = f"attribute:pa_{attr_slug}"
                    all_attributes.add(field_name)
            
            # Добавляем уникальные атрибуты
            for attr_field in sorted(all_attributes):
                if attr_field not in headers:
                    headers.append(attr_field)
        
        return headers
    
    def format_products_batch(self, products: List[Product]) -> List[Dict[str, str]]:
        """
        Форматирование пачки товаров
        
        Args:
            products: Список товаров
        
        Returns:
            Список отформатированных строк для CSV
        """
        formatted_rows = []
        
        for product in products:
            try:
                # 1. Форматируем товар
                csv_row = self.format_product(product)
                
                # 2. Проверяем что получены данные
                if not csv_row or not isinstance(csv_row, dict):
                    self.logger.warning(f"Товар #{product.id}: пустой результат форматирования")
                    continue
                
                # 3. Убедимся что есть обязательные поля
                required_fields_present = all(
                    csv_row.get(field) for field in ["post_title", "sku", "regular_price"]
                )
                
                if not required_fields_present:
                    self.logger.warning(f"Товар #{product.id}: отсутствуют обязательные поля")
                    
                    # Заполняем недостающие поля из товара
                    if not csv_row.get("post_title") and product.name:
                        csv_row["post_title"] = product.name
                    if not csv_row.get("sku") and product.sku:
                        csv_row["sku"] = product.sku
                    if not csv_row.get("regular_price") and product.price:
                        csv_row["regular_price"] = f"{product.price:.2f}"
                
                # 4. Добавляем в результат
                formatted_rows.append(csv_row)
                
                self.logger.debug(f"Товар #{product.id} отформатирован для WC")
                
                # 5. Периодический прогресс (каждые 100 товаров)
                if len(formatted_rows) % 100 == 0:
                    self.logger.info(f"Отформатировано {len(formatted_rows)} товаров...")
                
            except Exception as e:
                self.logger.error(f"Ошибка форматирования товара #{product.id}: {e}")
                
                # Создаем минимальную строку для отладки
                fallback_row = {
                    "ID": str(product.id) if product.id else "",
                    "post_title": product.name[:100] if product.name else f"Ошибка товара #{product.id}",
                    "sku": product.sku[:50] if product.sku else "",
                    "regular_price": str(product.price) if product.price else "0",
                    "post_content": f"Ошибка при форматировании: {str(e)[:200]}",
                    "tax:product_type": "simple",
                    "stock_status": "instock"
                }
                
                # Добавляем категорию если есть
                if product.category_hierarchy:
                    fallback_row["tax:product_cat"] = " > ".join(product.category_hierarchy)
                
                formatted_rows.append(fallback_row)
                continue
        
        # Логирование итогов
        if formatted_rows:
            self.logger.info(f"✅ Форматирование завершено: {len(formatted_rows)}/{len(products)} товаров")
            
            # Анализ успешности
            success_rate = (len(formatted_rows) / len(products)) * 100 if products else 0
            if success_rate < 90:
                self.logger.warning(f"Низкий процент успеха: {success_rate:.1f}%")
        
        return formatted_rows



    def get_all_csv_headers(self) -> List[str]:
        """
        Получение всех возможных заголовков CSV (включая атрибуты)
        
        Returns:
            Полный список всех возможных полей
        """
        # Базовые поля
        all_headers = list(self.WC_CSV_FIELDS)
        
        # Добавляем предопределенные атрибуты
        all_headers.extend(self.ATTRIBUTE_FIELDS)
        
        return all_headers
    
    def get_dynamic_headers(self, products: List[Product]) -> List[str]:
        """
        Получение динамических заголовков на основе товаров
        
        Args:
            products: Список товаров для анализа
        
        Returns:
            Список дополнительных полей (атрибутов)
        """
        dynamic_headers = set()
        
        for product in products:
            # Добавляем атрибуты из main_attributes
            for attr_name in product.main_attributes.keys():
                attr_slug = self._slugify_attribute(attr_name)
                field_name = f"attribute:pa_{attr_slug}"
                dynamic_headers.add(field_name)
            
            # Добавляем атрибуты из wc_fields
            for field_name in product.wc_fields.keys():
                if field_name.startswith("attribute:pa_"):
                    dynamic_headers.add(field_name)
        
        return sorted(dynamic_headers)
    
    def merge_csv_rows(self, csv_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Объединение CSV строк с разными заголовками
        
        Args:
            csv_rows: Список строк CSV с разными полями
        
        Returns:
            Унифицированный список с одинаковыми полями
        """
        if not csv_rows:
            return []
        
        # Находим все уникальные поля
        all_fields = set()
        for row in csv_rows:
            all_fields.update(row.keys())
        
        # Сортируем поля (сначала базовые, потом атрибуты)
        base_fields = [f for f in self.WC_CSV_FIELDS if f in all_fields]
        attribute_fields = sorted([f for f in all_fields 
                                 if f.startswith("attribute:pa_") and f not in base_fields])
        other_fields = sorted([f for f in all_fields 
                             if f not in base_fields and f not in attribute_fields])
        
        all_fields_sorted = base_fields + attribute_fields + other_fields
        
        # Создаем новые строки с одинаковыми полями
        unified_rows = []
        for row in csv_rows:
            new_row = {}
            for field in all_fields_sorted:
                new_row[field] = row.get(field, "")
            unified_rows.append(new_row)
        
        return unified_rows
    
    def generate_field_mapping_report(self, products: List[Product]) -> Dict[str, Any]:
        """
        Генерация отчета о маппинге полей
        
        Args:
            products: Список товаров для анализа
        
        Returns:
            Отчет о полях и атрибутах
        """
        report = {
            "total_products": len(products),
            "base_fields": {},
            "dynamic_fields": {},
            "attribute_stats": {},
            "field_coverage": {}
        }
        
        # Анализируем базовые поля
        for field in self.WC_CSV_FIELDS:
            count = 0
            for product in products:
                if (field in product.wc_fields and product.wc_fields[field]) or \
                   (hasattr(product, field.replace("tax:", "").replace("attribute:pa_", "")) and 
                    getattr(product, field.replace("tax:", "").replace("attribute:pa_", ""), None)):
                    count += 1
            
            report["base_fields"][field] = {
                "count": count,
                "percentage": (count / len(products) * 100) if products else 0,
                "required": field in ["post_title", "sku", "regular_price", "post_content"]
            }
        
        # Анализируем динамические поля (атрибуты)
        all_attributes = {}
        for product in products:
            for attr_name, attr_value in product.main_attributes.items():
                attr_slug = self._slugify_attribute(attr_name)
                field_name = f"attribute:pa_{attr_slug}"
                
                if field_name not in all_attributes:
                    all_attributes[field_name] = {
                        "original_name": attr_name,
                        "count": 0,
                        "example_value": attr_value
                    }
                all_attributes[field_name]["count"] += 1
        
        report["dynamic_fields"] = all_attributes
        
        # Статистика по атрибутам
        if all_attributes:
            attr_counts = [data["count"] for data in all_attributes.values()]
            report["attribute_stats"] = {
                "total_unique": len(all_attributes),
                "avg_per_product": sum(attr_counts) / len(products) if products else 0,
                "most_common": sorted(all_attributes.items(), 
                                    key=lambda x: x[1]["count"], reverse=True)[:5]
            }
        
        # Покрытие полей (сколько товаров имеют определенные поля)
        required_fields = ["post_title", "sku", "regular_price", "post_content"]
        for field in required_fields:
            coverage = report["base_fields"].get(field, {}).get("percentage", 0)
            status = "✅ OK" if coverage == 100 else f"⚠️ {coverage:.1f}%"
            report["field_coverage"][field] = status
        
        return report
    
    def create_field_template_csv(self, output_path: str):
        """
        Создание CSV шаблона с заголовками
        
        Args:
            output_path: Путь для сохранения шаблона
        """
        import csv
        
        # Получаем все заголовки
        headers = self.get_all_csv_headers()
        
        # Создаем пример строки с комментариями
        example_row = {}
        for header in headers:
            if header == "ID":
                example_row[header] = "1"
            elif header == "post_title":
                example_row[header] = "Название товара"
            elif header == "sku":
                example_row[header] = "SKU-12345"
            elif header == "regular_price":
                example_row[header] = "9999.00"
            elif header == "post_content":
                example_row[header] = "<p>Описание товара</p>"
            elif header.startswith("attribute:pa_"):
                example_row[header] = "Значение атрибута"
            else:
                example_row[header] = ""
        
        # Записываем CSV
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, delimiter=',', quotechar='"')
            writer.writeheader()
            writer.writerow(example_row)
    
    def validate_product_for_wc(self, product: Product) -> Dict[str, Any]:
        """
        Валидация товара перед экспортом в WooCommerce
        
        Args:
            product: Товар для валидации
        
        Returns:
            Результаты валидации
        """
        validation = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "missing_fields": []
        }
        
        # Проверяем обязательные поля
        required_fields = [
            ("post_title", "Название товара"),
            ("sku", "SKU"),
            ("regular_price", "Цена"),
            ("post_content", "Описание"),
        ]
        
        for wc_field, desc in required_fields:
            value = product.wc_fields.get(wc_field, "")
            if not value or str(value).strip() == "":
                validation["missing_fields"].append(desc)
                validation["errors"].append(f"Отсутствует обязательное поле: {desc}")
        
        # Проверяем цену
        price = product.wc_fields.get("regular_price", "")
        if price:
            try:
                price_num = float(str(price).replace(',', '.'))
                if price_num <= 0:
                    validation["warnings"].append("Цена должна быть больше 0")
                elif price_num > 1000000:
                    validation["warnings"].append("Цена очень большая")
            except ValueError:
                validation["errors"].append("Некорректный формат цены")
        
        # Проверяем SKU
        sku = product.wc_fields.get("sku", "")
        if sku:
            if len(sku) < 2:
                validation["warnings"].append("SKU слишком короткий")
            elif len(sku) > 100:
                validation["warnings"].append("SKU слишком длинный")
        
        # Проверяем описание
        description = product.wc_fields.get("post_content", "")
        if description:
            if len(description) < 10:
                validation["warnings"].append("Описание слишком короткое")
            elif len(description) > 10000:
                validation["warnings"].append("Описание очень длинное")
        
        # Если нет ошибок - товар валиден
        if not validation["errors"]:
            validation["is_valid"] = True
        
        return validation


# Функции для быстрого использования
def format_product_for_wc(product: Product, config: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Быстрое форматирование товара для WC
    
    Args:
        product: Товар для форматирования
        config: Конфигурация
    
    Returns:
        Отформатированная строка CSV
    """
    formatter = WCFormatter(config)
    return formatter.format_product(product)


def get_wc_csv_headers(products: List[Product] = None, config: Dict[str, Any] = None) -> List[str]:
    """
    Быстрое получение заголовков CSV
    
    Args:
        products: Список товаров
        config: Конфигурация
    
    Returns:
        Список заголовков
    """
    formatter = WCFormatter(config)
    return formatter.get_csv_headers(products)