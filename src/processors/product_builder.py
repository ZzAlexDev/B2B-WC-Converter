"""
Сборщик товара - объединение данных от всех парсеров
"""

from typing import Dict, Any, List, Optional
from dataclasses import asdict
import json

from src.core.models.product import Product
from src.core.models.category import Category
from src.parsers.name_parser import NameParser
from src.parsers.sku_parser import SKUParser
from src.parsers.category_parser import CategoryParser
from src.parsers.brand_parser import BrandParser
from src.parsers.price_parser import PriceParser
from src.parsers.specs_parser import SpecsParser
from src.parsers.images_parser import ImagesParser
from src.parsers.docs_parser import DocsParser
from src.parsers.description_parser import DescriptionParser

from src.utils.logger import get_logger, log_info, log_error, log_product_processed


class ProductBuilder:
    """
    Сборщик товара - координатор всех парсеров
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация сборщика товара
        
        Args:
            config: Конфигурация из settings.json
        """
        self.logger = get_logger()
        self.config = config or {}
        
        # Инициализируем все парсеры
        self.parsers = {
            "name": NameParser(),
            "sku": SKUParser(use_ns_code_as_sku=True),
            "category": CategoryParser(),
            "brand": BrandParser(),
            "price": PriceParser(currency="RUB"),
            "specs": SpecsParser(),
            "images": ImagesParser(
                download_path="data/downloads/images",
                max_images=5,
                skip_download=True  # Пока пропускаем скачивание для тестов
            ),
            "docs": DocsParser(),
            "description": DescriptionParser()
        }
        
        # Статистика
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
    
    def build_from_row(self, row: Dict[str, Any], row_index: int) -> Optional[Product]:
        """
        Сборка товара из строки XLSX
        
        Args:
            row: Словарь с данными строки (колонка: значение)
            row_index: Индекс строки для логов
        
        Returns:
            Объект Product или None при ошибке
        """
        self.logger.info(f"🔨 Сборка товара из строки #{row_index}")
        
        try:
            # 1. Инициализируем базовый объект товара
            product = Product(id=row_index, source_row=row_index)
            
            # 2. Парсим основные поля
            self._parse_basic_fields(product, row)
            
            # 3. Парсим категорию
            self._parse_category(product, row)
            
            # 4. Парсим бренд
            self._parse_brand(product, row)
            
            # 5. Парсим цену
            self._parse_price(product, row)
            
            # 6. Парсим характеристики
            self._parse_specs(product, row)
            
            # 7. Парсим SKU/артикул
            self._parse_sku(product, row)
            
            # 8. Парсим изображения
            self._parse_images(product, row)
            
            # 9. Парсим документы
            self._parse_documents(product, row)
            
            # 10. Собираем полное описание
            self._build_description(product, row)
            
            # 11. Генерируем WC поля
            self._prepare_wc_fields(product)
            
            # 12. Валидация
            errors = product.validate()
            if errors:
                self.logger.error(f"Ошибки валидации товара #{row_index}: {errors}")
                for error in errors:
                    self.stats["errors"].append(f"Строка {row_index}: {error}")
                self.stats["failed"] += 1
                return None
            
            # Успех!
            self.stats["successful"] += 1
            self.stats["total_processed"] += 1
            
            log_product_processed(row_index, product.name, success=True)
            
            return product
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сборки товара из строки #{row_index}: {e}", exc_info=True)
            self.stats["failed"] += 1
            self.stats["total_processed"] += 1
            self.stats["errors"].append(f"Строка {row_index}: {str(e)}")
            return None
    
    def _parse_basic_fields(self, product: Product, row: Dict[str, Any]):
        """Парсинг основных полей"""
        # Наименование
        if "Наименование" in row:
            name_result = self.parsers["name"].parse(row["Наименование"])
            if name_result.success:
                product.name = name_result.data["name"]
                product.wc_slug = name_result.data["slug"]
            else:
                raise ValueError(f"Ошибка парсинга наименования: {name_result.errors}")
        
        # Штрихкод
        if "Штрих код" in row:
            product.barcode_raw = str(row["Штрих код"]).strip()
        
        # Эксклюзив
        if "Эксклюзив" in row:
            exclusive_val = str(row["Эксклюзив"]).strip().lower()
            product.exclusive = exclusive_val in ["да", "yes", "true", "1", "есть"]
    
    def _parse_category(self, product: Product, row: Dict[str, Any]):
        """Парсинг категории"""
        if "Название категории" in row:
            category_result = self.parsers["category"].parse(row["Название категории"])
            if category_result.success and category_result.data:
                product.category_hierarchy = category_result.data["hierarchy"]
                
                # Сохраняем объекты категорий
                if "categories" in category_result.data:
                    product.wc_fields["tax:product_cat"] = category_result.data["wc_format"]
            else:
                self.logger.warning(f"Не удалось распарсить категорию: {category_result.errors}")
    
    def _parse_brand(self, product: Product, row: Dict[str, Any]):
        """Парсинг бренда"""
        brand_value = row.get("Бренд", "")
        name_value = row.get("Наименование", "")
        
        brand_result = self.parsers["brand"].parse(brand_value, name_value)
        if brand_result.success and brand_result.data.get("brand"):
            product.brand = brand_result.data["brand"]
            # Для WC используем slug бренда
            product.wc_fields["tax:product_brand"] = brand_result.data["slug"]
    
    def _parse_price(self, product: Product, row: Dict[str, Any]):
        """Парсинг цены"""
        if "Цена" in row:
            price_result = self.parsers["price"].parse(row["Цена"])
            if price_result.success:
                product.price = price_result.data["price"]
                product.wc_fields["regular_price"] = price_result.data["price_formatted"]
            else:
                raise ValueError(f"Ошибка парсинга цены: {price_result.errors}")
    
    def _parse_specs(self, product: Product, row: Dict[str, Any]):
        """Парсинг характеристик"""
        if "Характеристики" in row:
            specs_result = self.parsers["specs"].parse(row["Характеристики"])
            if specs_result.success:
                product.specs_raw = row["Характеристики"]
                product.specs_dict = specs_result.data["specs_dict"]
                product.main_attributes = specs_result.data["main_attributes"]
                
                # Сохраняем штрихкод если нашли в характеристиках
                if specs_result.data["barcode_info"]["found"]:
                    product.barcode_clean = specs_result.data["barcode_info"]["clean"]
                
                # Сохраняем HTML характеристик для описания
                product.wc_fields["specs_html"] = specs_result.data["html_ready"]
            else:
                self.logger.warning(f"Не удалось распарсить характеристики: {specs_result.errors}")
    
    def _parse_sku(self, product: Product, row: Dict[str, Any]):
        """Парсинг SKU и артикула"""
        article_value = row.get("Артикул", "")
        ns_code_value = row.get("НС-код", "")
        
        sku_result = self.parsers["sku"].parse(article_value, ns_code_value)
        if sku_result.success:
            product.article = sku_result.data["article"]
            product.sku = sku_result.data["sku"]
            product.wc_fields["sku"] = sku_result.data["sku"]
        else:
            self.logger.warning(f"Не удалось распарсить SKU: {sku_result.errors}")
    
    def _parse_images(self, product: Product, row: Dict[str, Any]):
        """Парсинг изображений"""
        if "Изображение" in row:
            images_result = self.parsers["images"].parse(
                value=row["Изображение"],
                sku=product.sku or str(product.id),
                slug=product.wc_slug,
                category_hierarchy=product.category_hierarchy,
                product_name=product.name
            )
            
            if images_result.success:
                product.images_raw = row["Изображение"]
                product.images_local = images_result.data["local_paths"]
                product.images_wc_format = images_result.data["wc_format"]
                product.wc_fields["images"] = images_result.data["wc_format"]
    
    def _parse_documents(self, product: Product, row: Dict[str, Any]):
        """Парсинг документов"""
        docs_result = self.parsers["docs"].parse_all_documents(
            videos=row.get("Видео", ""),
            drawings=row.get("Чертежи", ""),
            certificates=row.get("Сертификаты", ""),
            promo=row.get("Промоматериалы", ""),
            manuals=row.get("Инструкции", ""),
            product_name=product.name,
            product_type=product.category_hierarchy[-1] if product.category_hierarchy else ""
        )
        
        if docs_result.success and docs_result.data["has_documents"]:
            product.documents = docs_result.data["all_docs"]
            product.documents_html = docs_result.data["full_html"]
    
    def _build_description(self, product: Product, row: Dict[str, Any]):
        """Сборка полного описания"""
        # Получаем статью из колонки
        article_html = row.get("Статья", "")
        
        # Получаем HTML характеристик
        specs_html = product.wc_fields.get("specs_html", "")
        
        # Получаем HTML документов
        docs_html = product.documents_html
        
        # Получаем видео (первое из колонки Видео)
        video_url = ""
        if "Видео" in row and row["Видео"]:
            video_parts = str(row["Видео"]).split(',')
            if video_parts:
                video_url = video_parts[0].strip()
        
        # Собираем описание
        description_result = self.parsers["description"].parse(
            article_html=article_html,
            specs_html=specs_html,
            documents_html=docs_html,
            video_url=video_url,
            product_name=product.name
        )
        
        if description_result.success:
            product.description_raw = article_html
            product.description_final = description_result.data["html"]
            
            # Сохраняем для WC
            product.wc_fields["post_content"] = description_result.data["html"]
            
            # Создаем короткое описание
            short_desc = self.parsers["description"].create_short_description(article_html)
            product.wc_fields["post_excerpt"] = short_desc
    
    def _prepare_wc_fields(self, product: Product):
        """Подготовка полей для WooCommerce"""
        # Основные поля
        product.wc_fields["post_title"] = product.name
        product.wc_fields["post_name"] = product.wc_slug
        
        # Статусы и типы (из конфига)
        default_values = self.config.get("wc", {}).get("default_values", {})
        for key, value in default_values.items():
            if key not in product.wc_fields:  # Не перезаписываем установленные поля
                product.wc_fields[key] = value
        
        # Категория и бренд уже установлены
        # SKU и цена уже установлены
        
        # Изображения уже установлены
        
        # Атрибуты из характеристик
        for attr_key, attr_value in product.main_attributes.items():
            wc_attr_key = f"attribute:pa_{self._slugify(attr_key)}"
            product.wc_fields[wc_attr_key] = attr_value
        
        # Штрихкод
        if product.barcode_clean:
            product.wc_fields["_barcode"] = product.barcode_clean
    
    def _slugify(self, text: str) -> str:
        """Простая генерация slug"""
        import re
        slug = text.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики обработки"""
        return {
            **self.stats,
            "success_rate": (self.stats["successful"] / self.stats["total_processed"] * 100 
                           if self.stats["total_processed"] > 0 else 0)
        }
    
    def reset_stats(self):
        """Сброс статистики"""
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }


# Функция для быстрого использования
def build_product_from_dict(row_data: Dict[str, Any], config: Dict[str, Any] = None) -> Optional[Product]:
    """
    Быстрая сборка товара из словаря данных
    
    Args:
        row_data: Словарь с данными строки
        config: Конфигурация
    
    Returns:
        Объект Product или None
    """
    builder = ProductBuilder(config)
    return builder.build_from_row(row_data, 0)