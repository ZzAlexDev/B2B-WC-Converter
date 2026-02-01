"""
Aggregator - сборщик данных для B2B-WC Converter v2.0.
Объединяет фрагменты от всех обработчиков в готовый WooProduct.
"""
import logging
import re
from typing import Dict, Any, List
from .models import RawProduct, WooProduct
from .config_manager import ConfigManager
from .handlers import (
    CoreHandler, 
    SpecsHandler, 
    MediaHandler, 
    ContentHandler
)

logger = logging.getLogger(__name__)


class Aggregator:
    """
    Сборщик данных товара.
    Объединяет результаты обработчиков и применяет дефолтные значения.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует агрегатор и обработчики.
        
        Args:
            config_manager: Менеджер конфигураций
        """
        self.config_manager = config_manager
        
        # Инициализируем обработчики
        self.specs_handler = SpecsHandler(config_manager)  # ← СОХРАНИМ ДЛЯ ДОСТУПА
        self.handlers = [
            CoreHandler(config_manager),
            self.specs_handler,  # ← ИСПОЛЬЗУЕМ СОХРАНЕННЫЙ
            MediaHandler(config_manager),
            ContentHandler(config_manager)
        ]
        
        logger.info(f"Aggregator инициализирован с {len(self.handlers)} обработчиками")


    def process_product(self, raw_product: RawProduct) -> WooProduct:
        """
        Обрабатывает сырой продукт через все обработчики.
        """
        logger.debug(f"Обработка продукта: {raw_product.НС_код}")
        
        # === НОВЫЙ КОД: Извлекаем бренд ДО обработчиков ===
        brand = self._extract_brand_from_raw(raw_product)
        
        # Собираем данные от всех обработчиков
        handler_results = {}
        
        for handler in self.handlers:
            try:
                handler_name = handler.handler_name
                result = handler.handle(raw_product)
                
                if result:
                    handler_results[handler_name] = result
                    # ОТЛАДКА
                    if handler_name == 'SpecsHandler':
                        print(f"\n[DEBUG] === SpecsHandler вернул ===")
                        for key, val in result.items():
                            print(f"  '{key}': '{val}'")
                        print(f"=== Всего {len(result)} полей ===\n")
                else:
                    logger.warning(f"  {handler_name}: вернул пустой результат")
                    
            except Exception as e:
                logger.error(f"  {handler_name}: ошибка обработки - {e}")
                continue
        
        # Объединяем все результаты
        merged_data = self._merge_handler_results(handler_results)
        
        # Создаем WooProduct
        woo_product = self._create_woo_product(merged_data)
        
        # === НОВЫЙ КОД: Добавляем бренд и теги ===
        # 1. Извлекаем бренд
        brand = self._extract_brand_from_raw(raw_product)
        if brand:
            self._set_woo_product_field(woo_product, "tax:product_brand", brand)
        
        # 2. Генерируем теги (без бренда!)
        tags = self._generate_product_tags(raw_product, brand)
        if tags:
            self._set_woo_product_field(woo_product, "tax:product_tag", tags)
        
        # ОТЛАДКА
        print(f"\n[DEBUG] === Добавленные tax-поля ===")
        print(f"tax:product_brand: '{brand}'")
        print(f"tax:product_tag: '{tags}'")
        print(f"=== Конец tax-полей ===\n")
        
        # Применяем дефолтные значения
        self._apply_default_values(woo_product)
        
        # Устанавливаем пустые поля из ТЗ (БЕЗ tax:product_tag и tax:product_brand)
        self._set_empty_fields(woo_product)
        
        logger.debug(f"Продукт {raw_product.НС_код} агрегирован: {len(merged_data)} полей")
        return woo_product

        # В классе Aggregator добавим методы:

    def _extract_brand_from_raw(self, raw_product: RawProduct) -> str:
        """
        Извлекает бренд из RawProduct.
        
        Args:
            raw_product: Сырой продукт
            
        Returns:
            Значение бренда
        """
        # Прямое извлечение из поля Бренд
        if hasattr(raw_product, 'Бренд') and raw_product.Бренд:
            return raw_product.Бренд.strip()
        
        # Альтернативные поля
        brand_fields = ['brand', 'Brand', 'Производитель', 'manufacturer', 'vendor']
        for field in brand_fields:
            field_attr = field.replace(' ', '_').replace('-', '_')
            if hasattr(raw_product, field_attr):
                value = getattr(raw_product, field_attr)
                if value and str(value).strip():
                    return str(value).strip()
        
        # Попытка извлечь из названия
        if hasattr(raw_product, 'Наименование'):
            name = raw_product.Наименование
            # Простая логика: первое слово до пробела, если оно не слишком длинное
            first_word = name.split()[0] if name.split() else ""
            if len(first_word) <= 20 and not any(x in first_word for x in [' ', '-', ',', '(']):
                return first_word
        
        return ""  # Пустое значение

    def process_product(self, raw_product: RawProduct) -> WooProduct:
        """
        Обрабатывает сырой продукт через все обработчики.
        """
        logger.debug(f"Обработка продукта: {raw_product.НС_код}")
        
        # Собираем данные от всех обработчиков
        handler_results = {}
        
        for handler in self.handlers:
            try:
                handler_name = handler.handler_name
                result = handler.handle(raw_product)
                
                if result:
                    handler_results[handler_name] = result
                    # ОТЛАДКА
                    if handler_name == 'SpecsHandler':
                        print(f"\n[DEBUG] === SpecsHandler вернул ===")
                        for key, val in result.items():
                            print(f"  '{key}': '{val}'")
                        print(f"=== Всего {len(result)} полей ===\n")
                else:
                    logger.warning(f"  {handler_name}: вернул пустой результат")
                    
            except Exception as e:
                logger.error(f"  {handler_name}: ошибка обработки - {e}")
                continue
        
        # Объединяем все результаты
        merged_data = self._merge_handler_results(handler_results)
        
        # Создаем WooProduct
        woo_product = self._create_woo_product(merged_data)
        
        # === НОВЫЙ КОД: Добавляем бренд и теги ===
        # 1. Извлекаем бренд (ОДИН РАЗ)
        brand = self._extract_brand_from_raw(raw_product)
        if brand:
            self._set_woo_product_field(woo_product, "tax:product_brand", brand)
        
        # 2. Генерируем теги (без бренда!)
        tags = self._generate_product_tags_optimized(raw_product, brand, merged_data)
        if tags:
            self._set_woo_product_field(woo_product, "tax:product_tag", tags)
        
        # ОТЛАДКА
        print(f"\n[DEBUG] === Добавленные tax-поля ===")
        print(f"tax:product_brand: '{brand}'")
        print(f"tax:product_tag: '{tags}'")
        print(f"=== Конец tax-полей ===\n")
        
        # Применяем дефолтные значения
        self._apply_default_values(woo_product)
        
        # Устанавливаем пустые поля из ТЗ (БЕЗ tax:product_tag и tax:product_brand)
        self._set_empty_fields(woo_product)
        
        logger.debug(f"Продукт {raw_product.НС_код} агрегирован: {len(merged_data)} полей")
        return woo_product
    
    def _extract_brand_from_raw(self, raw_product: RawProduct) -> str:
        """
        Извлекает бренд из RawProduct.
        
        Args:
            raw_product: Сырой продукт
            
        Returns:
            Значение бренда
        """
        # Прямое извлечение из поля Бренд
        if hasattr(raw_product, 'Бренд') and raw_product.Бренд:
            brand = raw_product.Бренд.strip()
            if brand:
                print(f"[DEBUG] Бренд найден в поле 'Бренд': '{brand}'")
                return brand
        
        # Альтернативные поля
        brand_fields = ['brand', 'Brand', 'Производитель', 'manufacturer', 'vendor']
        for field in brand_fields:
            field_attr = field.replace(' ', '_').replace('-', '_')
            if hasattr(raw_product, field_attr):
                value = getattr(raw_product, field_attr)
                if value and str(value).strip():
                    brand = str(value).strip()
                    print(f"[DEBUG] Бренд найден в поле '{field}': '{brand}'")
                    return brand
        
        # Попытка извлечь из названия
        if hasattr(raw_product, 'Наименование'):
            name = raw_product.Наименование.strip()
            # Простая логика: первое слово до пробела, если оно не слишком длинное
            first_word = name.split()[0] if name.split() else ""
            if len(first_word) <= 20 and not any(x in first_word for x in [' ', '-', ',', '(']):
                print(f"[DEBUG] Бренд извлечен из названия: '{first_word}'")
                return first_word
        
        print(f"[DEBUG] Бренд не найден для продукта: {raw_product.НС_код}")
        return ""  # Пустое значение
    
    def _generate_product_tags_optimized(self, raw_product: RawProduct, brand: str, merged_data: Dict) -> str:
        """
        Генерирует теги на основе данных продукта.
        Бренд НЕ включаем в теги (он уже в отдельном поле).
        
        Args:
            raw_product: Сырой продукт
            brand: Извлеченный бренд
            merged_data: Объединенные данные от обработчиков
            
        Returns:
            Строка тегов через запятую
        """
        tags = []
        
        print(f"[DEBUG] Генерация тегов для продукта: {raw_product.НС_код}")
        
        # 1. Извлекаем тип товара из названия (убираем бренд)
        if hasattr(raw_product, 'Наименование') and raw_product.Наименование:
            product_type = self._extract_product_type_from_name(raw_product.Наименование, brand)
            if product_type:
                tags.append(product_type)
        
        # 2. Категория (последний уникальный элемент)
        if hasattr(raw_product, 'Название_категории') and raw_product.Название_категории:
            category_tag = self._extract_main_category(raw_product.Название_категории)
            if category_tag and category_tag not in tags:
                tags.append(category_tag)
        
        # 3. Характеристики через SpecsHandler (используем существующий парсер)
        if hasattr(raw_product, 'Характеристики') and raw_product.Характеристики:
            specs = self.specs_handler._parse_specifications(raw_product.Характеристики)
            spec_tags = self._extract_tags_from_specs(specs)
            tags.extend(spec_tags)
        
        # 4. Очистка и дедубликация
        clean_tags = self._clean_and_deduplicate_tags(tags)
        
        # 5. Преобразуем в строку
        result = ", ".join(clean_tags)
        print(f"[DEBUG] Итоговые теги ({len(clean_tags)}): '{result}'")
        
        return result
    
    def _extract_product_type_from_name(self, name: str, brand: str) -> str:
        """Извлекает тип товара из названия, убирая бренд."""
        name = name.strip()
        brand = brand.strip()
        
        # Убираем бренд из начала названия
        if brand and name.startswith(brand):
            clean_name = name[len(brand):].strip()
        else:
            clean_name = name
        
        # Убираем начальные разделители
        clean_name = clean_name.lstrip(' -–—')
        
        # Берем первые 2-3 слова до разделителей
        words = clean_name.split()
        type_words = []
        
        for word in words[:3]:  # Ограничиваем 3 словами
            if word in ['-', '–', '—', ',', '(', '[', '{']:
                break
            type_words.append(word)
        
        if type_words:
            product_type = ' '.join(type_words).strip()
            if product_type:
                print(f"[DEBUG] Извлечен тип товара: '{product_type}'")
                return product_type
        
        return ""
    
    def _extract_main_category(self, category_string: str) -> str:
        """Извлекает последний уникальный элемент категории."""
        category_string = category_string.strip()
        
        if not category_string:
            return ""
        
        # Разделители категорий
        separators = [' > ', ' - ', ' / ', ' | ']
        
        for sep in separators:
            if sep in category_string:
                parts = [p.strip() for p in category_string.split(sep)]
                # Ищем последний уникальный элемент (убираем дубли)
                for i in range(len(parts) - 1, -1, -1):
                    part = parts[i]
                    if part and (i == 0 or part != parts[i-1]):
                        print(f"[DEBUG] Извлечена категория: '{part}'")
                        return part
        
        # Если нет разделителей
        print(f"[DEBUG] Использована вся категория: '{category_string}'")
        return category_string
    
    def _extract_tags_from_specs(self, specs: Dict[str, str]) -> List[str]:
        """Извлекает теги из характеристик."""
        tags = []
        
        # Ключевые характеристики для тегов
        important_specs = {
            'Материал корпуса': None,
            'Цвет корпуса': None,
            'Тип сушилки': None,
            'Тип товара': None,
            'Вид управления': None,
            'Вид установки (крепления)': None,
            'Форма корпуса': None,
            'Область применения': None,
            'Серия': None,
            'Страна производства': None,
        }
        
        for spec_key in important_specs.keys():
            if spec_key in specs:
                value = specs[spec_key].strip()
                if value and value not in ['Нет', '']:
                    # Обработка специальных случаев
                    if value == 'Да' and 'Антивандальное' in spec_key:
                        tags.append('Антивандальное')
                        print(f"[DEBUG] Добавлен тег: 'Антивандальное' из '{spec_key}'")
                    elif value != 'Нет':
                        # Очищаем значение (убираем единицы измерения и т.д.)
                        clean_value = self._clean_spec_value(value)
                        if clean_value:
                            tags.append(clean_value)
                            print(f"[DEBUG] Добавлен тег: '{clean_value}' из '{spec_key}'")
        
        return tags
    
    def _clean_spec_value(self, value: str) -> str:
        """Очищает значение характеристики для тега."""
        value = value.strip()
        
        # Если значение слишком общее - пропускаем
        skip_values = {'Нет', 'Да', 'Не указано', '-', '—', ''}
        if value in skip_values:
            return ""
        
        # Убираем единицы измерения
        units = ['кг', 'г', 'см', 'мм', 'м', 'л', 'мл', 'Вт', 'кВт', 'В', '°С', 'дБ', 
                'ккал/ч', 'м/с', 'об/мин', 'Гц', 'бар', 'атм', 'Па', 'л/с', 'м³/ч']
        
        for unit in units:
            # Варианты: "10 кг", "10кг", "10 кг.", "10кг."
            patterns = [f' {unit}', f'{unit}', f' {unit}.', f'{unit}.']
            for pattern in patterns:
                if value.lower().endswith(pattern.lower()):
                    value = value[:-len(pattern)].strip()
                    break
        
        # Убираем всё в скобках и после них
        if '(' in value:
            value = value.split('(')[0].strip()
        
        # Убираем диапазоны (брать первое значение)
        if ' - ' in value or ' – ' in value or ' — ' in value:
            # Разделяем по разным типам тире
            for separator in [' - ', ' – ', ' — ', '-', '–', '—']:
                if separator in value:
                    parts = value.split(separator)
                    if parts[0].strip().isdigit() or len(parts[0].split()) <= 2:
                        value = parts[0].strip()
                    break
        
        # Убираем начальные "до ", "от ", "около "
        prefixes = ['до ', 'от ', 'около ', 'примерно ', '~', '≈']
        for prefix in prefixes:
            if value.lower().startswith(prefix):
                value = value[len(prefix):].strip()
                break
        
        # Ограничиваем длину (максимум 3 слова)
        words = value.split()
        if len(words) > 3:
            value = ' '.join(words[:3])
        
        # Убираем лишние символы
        value = value.strip(' ,;:.-')
        
        return value
    
    def _clean_and_deduplicate_tags(self, tags: List[str]) -> List[str]:
        """Очищает и удаляет дубликаты тегов."""
        clean_tags = []
        seen = set()
        
        for tag in tags:
            if tag:
                # Очистка
                tag_str = str(tag).strip()
                tag_str = re.sub(r'\s+', ' ', tag_str)  # Убираем лишние пробелы
                tag_str = tag_str.strip(' ,.-')  # Убираем разделители по краям
                
                # Убираем слишком длинные теги
                if len(tag_str) > 50:
                    continue
                
                # Дедубликация (case-insensitive)
                tag_lower = tag_str.lower()
                if tag_lower and tag_lower not in seen:
                    seen.add(tag_lower)
                    clean_tags.append(tag_str)
        
        # Ограничиваем количество тегов
        return clean_tags[:15]



    
    def _merge_handler_results(self, handler_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Объединяет результаты от всех обработчиков.
        
        Args:
            handler_results: Словарь {имя_обработчика: результат}
            
        Returns:
            Объединенный словарь данных
        """
        merged = {}
        
        print(f"[DEBUG Aggregator] Объединяю результаты от {len(handler_results)} обработчиков")
        
        for handler_name, result in handler_results.items():
            print(f"\n[DEBUG] Обработчик '{handler_name}' вернул {len(result)} полей:")
            
            for key, value in result.items():
                print(f"  '{key}': '{value}'")
                
                # Проверяем конфликты полей
                if key in merged and merged[key] != value:
                    logger.warning(f"Конфликт поля '{key}': "
                                  f"было '{merged[key]}', стало '{value}' "
                                  f"(обработчик: {handler_name})")
            
            # Объединяем
            merged.update(result)
        
        print(f"\n[DEBUG] Итого объединено {len(merged)} полей")
        return merged
    
    def _create_woo_product(self, data: Dict[str, Any]) -> WooProduct:
        """
        Создает объект WooProduct из объединенных данных.
        
        Args:
            data: Объединенные данные от обработчиков
            
        Returns:
            Экземпляр WooProduct
        """
        woo_product = WooProduct()
        
        print(f"[DEBUG _create_woo_product] Создаю WooProduct из {len(data)} полей")
        
        # Заполняем основные поля
        for key, value in data.items():
            self._set_woo_product_field(woo_product, key, value)
        
        return woo_product
    
    def _set_woo_product_field(self, woo_product: WooProduct, key: str, value: Any) -> None:
        """
        Устанавливает поле в WooProduct с учетом типа поля.
        
        Args:
            woo_product: Продукт WooCommerce
            key: Ключ поля
            value: Значение поля
        """
        print(f"[DEBUG _set_woo_product_field] Ключ: '{key}', Значение: '{value}'")
        
        # Определяем тип поля
        if key.startswith('tax:'):
            # Таксономии
            field_name = 'tax_' + key[4:].replace('-', '_')
        elif key.startswith('meta:'):
            # Мета-поля
            woo_product.meta_fields[key] = str(value) if value is not None else ""
            return
        elif key.startswith('attribute:'):
            # Атрибуты
            woo_product.attributes[key] = str(value) if value is not None else ""
            return
        else:
            # Обычные поля
            field_name = key
        
        # Проверяем, существует ли поле в WooProduct
        if hasattr(woo_product, field_name):
            setattr(woo_product, field_name, str(value) if value is not None else "")
        else:
            # Если поле не найдено, добавляем в мета-поля
            woo_product.meta_fields[key] = str(value) if value is not None else ""
    
    def _apply_default_values(self, woo_product: WooProduct) -> None:
        """
        Применяет значения по умолчанию из конфига.
        
        Args:
            woo_product: Продукт WooCommerce
        """
        default_values = self.config_manager.settings.get("default_values", {})
        
        for config_key, default_value in default_values.items():
            # Определяем поле WooProduct
            if config_key.startswith('tax:'):
                field_name = 'tax_' + config_key[4:].replace('-', '_')
                woo_field = config_key  # Сохраняем оригинальное имя для проверки
            else:
                field_name = config_key
                woo_field = config_key
            
            # Проверяем, установлено ли уже значение
            current_value = None
            
            if woo_field.startswith('tax:'):
                # Для таксономий проверяем поле с префиксом tax_
                woo_field_name = 'tax_' + woo_field[4:].replace('-', '_')
                if hasattr(woo_product, woo_field_name):
                    current_value = getattr(woo_product, woo_field_name)
            elif hasattr(woo_product, field_name):
                current_value = getattr(woo_product, field_name)
            
            # Если значение не установлено, применяем дефолтное
            if not current_value:
                self._set_woo_product_field(woo_product, config_key, default_value)
    
    def _set_empty_fields(self, woo_product: WooProduct) -> None:
        """
        Устанавливает пустые значения для полей из ТЗ п.4.2.
        
        Args:
            woo_product: Продукт WooCommerce
        """
        # Список полей, которые должны быть пустыми (из ТЗ п.4.2)
        empty_fields = [
            # Основные поля
            "ID", "post_parent", "parent_sku", "children",
            
            # Цены и наличие
            "sale_price", "stock", "low_stock_amount",
            
            # Таксономии и классы
            "tax_class", "visibility", "tax:product_visibility", "tax:product_shipping_class",
            
            # Связи
            "upsell_ids", "crosssell_ids",
            
            # Заметки и даты
            "purchase_note", "sale_price_dates_from", "sale_price_dates_to",
            
            # Ссылки
            "product_url", "button_text", "product_page_url",
            
            # Мета-поля WooCommerce
            "meta:total_sales",
            
            # SEO поля Yoast (кроме тех, что заполняются автоматически)
            "meta:_yoast_wpseo_bctitle",
            "meta:_yoast_wpseo_meta-robots-adv",
            "meta:_yoast_wpseo_is_cornerstone",
            "meta:_yoast_wpseo_linkdex",
            "meta:_yoast_wpseo_estimated-reading-time-minutes",
            "meta:_yoast_wpseo_content_score",
            "meta:_yoast_wpseo_metakeywords"
        ]
        
        for field in empty_fields:
            self._set_woo_product_field(woo_product, field, "")
    
    def cleanup(self) -> None:
        """
        Очищает ресурсы всех обработчиков.
        """
        for handler in self.handlers:
            try:
                handler.cleanup()
            except Exception as e:
                logger.warning(f"Ошибка при очистке {handler.handler_name}: {e}")
        
        logger.debug("Aggregator: очищены ресурсы всех обработчиков")