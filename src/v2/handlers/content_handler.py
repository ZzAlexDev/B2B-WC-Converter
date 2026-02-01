"""
ContentHandler - обработчик текстового контента для B2B-WC Converter v2.0.
Обрабатывает: HTML описание, характеристики, документы, видео.
"""
import re
from typing import Dict, Any, List
import logging

# Используем относительные импорты
try:
    from .base_handler import BaseHandler
    from ..models import RawProduct
    from ..config_manager import ConfigManager
    from ..utils.logger import get_logger
    from ..utils.validators import (
        extract_youtube_id,
        normalize_yes_no,
        parse_specifications
    )
except ImportError:
    from base_handler import BaseHandler
    from models import RawProduct
    from config_manager import ConfigManager
    from utils.logger import get_logger
    from utils.validators import (
        extract_youtube_id,
        normalize_yes_no,
        parse_specifications
    )

logger = get_logger(__name__)


class ContentHandler(BaseHandler):
    """
    Обработчик текстового контента товара.
    Собирает полное HTML описание из различных источников.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует ContentHandler.
        
        Args:
            config_manager: Менеджер конфигураций
        """
        super().__init__(config_manager)
        
        # Кэш для разобранных характеристик
        self.specs_cache: Dict[str, Dict[str, str]] = {}
    
    def process(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает текстовый контент товара.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с полем post_content (HTML)
        """
        from ..utils.validators import safe_getattr
        
        result = {}

        
        # 1. Парсим характеристики для использования в контенте
        specs_str = safe_getattr(raw_product, "Характеристики")
        specs = self._parse_specifications(specs_str)
        
        # 2. Собираем HTML контент
        article_html = safe_getattr(raw_product, "Статья")
        html_content = self._build_html_content(raw_product, specs, article_html)
        
        result["post_content"] = html_content
        
        logger.debug(f"ContentHandler обработал продукт {raw_product.НС_код}: "
                    f"{len(html_content)} символов HTML")
        return result

    
    def _parse_specifications(self, specs_string: str) -> Dict[str, str]:
        """
        Парсит строку характеристик.
        
        Args:
            specs_string: Строка характеристик
            
        Returns:
            Словарь характеристик {ключ: значение}
        """
        if not specs_string or not specs_string.strip():
            return {}
        
        # Проверяем кэш
        cache_key = hash(specs_string)
        if cache_key in self.specs_cache:
            return self.specs_cache[cache_key].copy()
        
        # Используем утилиту для парсинга
        specs = parse_specifications(specs_string)
        
        # Нормализуем значения Да/Нет
        normalized_specs = {}
        for key, value in specs.items():
            normalized_value = normalize_yes_no(value)
            normalized_specs[key] = normalized_value
        
        # Сохраняем в кэш
        self.specs_cache[cache_key] = normalized_specs.copy()
        
        return normalized_specs
    
    def _build_html_content(self, raw_product: RawProduct, specs: Dict[str, str], article_html: str) -> str:
        """
        Собирает HTML контент из различных источников.
        
        Args:
            raw_product: Сырые данные продукта
            specs: Словарь характеристик
            article_html: HTML статьи
            
        Returns:
            HTML строка
        """
        html_parts = []
        
        # Блок 1: HTML из статьи
        processed_article = self._process_article(article_html)
        if processed_article:
            html_parts.append(processed_article)

        
        # Блок 2: Технические характеристики
        specs_html = self._build_specifications_html(specs)
        if specs_html:
            html_parts.append(specs_html)
        
        # Блок 3: Документация и видео
        docs_video_html = self._build_docs_video_html(raw_product)
        if docs_video_html:
            html_parts.append(docs_video_html)
        
        # Блок 4: Дополнительная информация
        additional_info_html = self._build_additional_info_html(raw_product)
        if additional_info_html:
            html_parts.append(additional_info_html)
        
        # Объединяем все блоки
        return "\n\n".join(html_parts)
    
    def _process_article(self, article_html: str) -> str:
        """
        Обрабатывает HTML статью.
        
        Args:
            article_html: HTML текст статьи
            
        Returns:
            Очищенный HTML
        """
        if not article_html or not article_html.strip():
            return ""
        
        html = article_html.strip()
        
        # Проверяем, есть ли теги HTML
        if not re.search(r'<[^>]+>', html):
            # Если нет HTML тегов, оборачиваем в параграф
            html = f"<p>{html}</p>"
        
        return html
    
    def _build_specifications_html(self, specs: Dict[str, str]) -> str:
        """
        Строит HTML для технических характеристик.
        
        Args:
            specs: Словарь характеристик
            
        Returns:
            HTML строка
        """
        if not specs:
            return ""
        
        html_parts = ['<h2>Технические характеристики</h2>', '<ul>']
        
        for key, value in sorted(specs.items()):
            html_parts.append(f'<li><strong>{key}:</strong> {value}</li>')
        
        html_parts.append('</ul>')
        
        return "\n".join(html_parts)
    
    def _build_docs_video_html(self, raw_product: RawProduct) -> str:
        """
        Строит HTML для документации и видео.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            HTML строка
        """
        html_parts = []
        
        # Документация
        docs = self._collect_documents(raw_product)
        if docs:
            html_parts.append('<h3>Документация</h3>')
            
            # Группируем документы по типам
            doc_types = {}
            for doc_type, doc_url in docs:
                if doc_type not in doc_types:
                    doc_types[doc_type] = []
                doc_types[doc_type].append(doc_url)
            
            # Добавляем документы с подзаголовками
            for doc_type, urls in doc_types.items():
                if len(urls) > 1:
                    html_parts.append(f'<h4>{doc_type.capitalize()}</h4>')
                
                for doc_url in urls:
                    doc_html = self._build_doc_link_html(doc_type, doc_url, raw_product)
                    html_parts.append(f'<p>{doc_html}</p>')
        
        # Видео
        video_url = raw_product.Видео.strip() if raw_product.Видео else ""
        if video_url:
            video_html = self._build_video_html(video_url, raw_product)
            if video_html:
                if docs:
                    html_parts.append('<h3>Видеообзор</h3>')
                else:
                    html_parts.append('<h3>Документация и видео</h3>')
                html_parts.append(f'<p>{video_html}</p>')
        
        if not html_parts:
            return ""
        
        return "\n".join(html_parts)
    
    def _collect_documents(self, raw_product: RawProduct) -> List[tuple]:
        """
        Собирает все документы товара.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Список кортежей (тип_документа, URL)
        """
        documents = []
        
        # Поля с документами
        doc_fields = [
            ("Чертежи", "чертеж"),
            ("Сертификаты", "сертификат"),
            ("Промоматериалы", "промо-материал"),
            ("Инструкции", "инструкция")
        ]
        
        for field_name, doc_type in doc_fields:
            doc_url = getattr(raw_product, field_name, "").strip()
            if doc_url:
                documents.append((doc_type, doc_url))
        
        return documents
    
    def _build_doc_link_html(self, doc_type: str, doc_url: str, raw_product: RawProduct) -> str:
        """
        Строит HTML ссылку на документ.
        
        Args:
            doc_type: Тип документа
            doc_url: URL документа
            raw_product: Сырые данные продукта
            
        Returns:
            HTML ссылка
        """
        # Получаем шаблон из конфига
        template = self.config_manager.get_setting(
            'templates.doc_link_item',
            '<img style="vertical-align: middle; margin-right: 8px;" src="{icon_url}" alt="PDF" width="32" height="32" /><a href="{doc_url}" target="_blank" rel="noopener noreferrer">{doc_type} {product_title} (PDF)</a>'
        )
        
        # URL иконки PDF
        icon_url = self.config_manager.get_setting(
            'paths.pdf_icon_url',
            'https://вашсайт.ru/wp-content/uploads/2026/02/pdf-icon.png'
        )
        
        # Название продукта
        product_title = raw_product.Наименование or "Товар"
        
        # Заменяем плейсхолдеры
        html = template.format(
            icon_url=icon_url,
            doc_url=doc_url,
            doc_type=doc_type.capitalize(),
            product_title=product_title
        )
        
        return html
    
    def _build_video_html(self, video_url: str, raw_product: RawProduct) -> str:
        """
        Строит HTML для видео.
        
        Args:
            video_url: URL видео
            raw_product: Сырые данные продукта
            
        Returns:
            HTML строка
        """
        # Используем утилиту для извлечения YouTube ID
        youtube_id = extract_youtube_id(video_url)
        
        if not youtube_id:
            # Простая ссылка, если не YouTube
            product_title = raw_product.Наименование or "Товар"
            return f'<a href="{video_url}" target="_blank" rel="noopener noreferrer">Видеообзор: {product_title}</a>'
        
        # Получаем шаблон из конфига
        template = self.config_manager.get_setting(
            'templates.video_link_item',
            '<a href="{video_url}" target="_blank" rel="noopener noreferrer"><img src="{thumbnail_url}" alt="Видеообзор: {product_title}" style="max-width: 300px;" /></a>'
        )
        
        # Генерируем URL превью
        thumbnail_template = self.config_manager.get_setting(
            'paths.video_thumbnail_template',
            'https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg'
        )
        
        thumbnail_url = thumbnail_template.format(youtube_id=youtube_id)
        
        # Название продукта
        product_title = raw_product.Наименование or "Товар"
        
        # Заменяем плейсхолдеры
        html = template.format(
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            product_title=product_title
        )
        
        return html
    
    def _build_additional_info_html(self, raw_product: RawProduct) -> str:
        """
        Строит HTML для дополнительной информации.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            HTML строка
        """
        html_parts = ['<h3>Дополнительная информация</h3>', '<ul>']
        
        # Бренд
        if raw_product.Бренд:
            html_parts.append(f'<li><strong>Бренд:</strong> {raw_product.Бренд}</li>')
        
        # Артикул
        if raw_product.Артикул:
            html_parts.append(f'<li><strong>Артикул производителя:</strong> {raw_product.Артикул}</li>')
        
        # НС-код
        if raw_product.НС_код:
            html_parts.append(f'<li><strong>НС-код:</strong> {raw_product.НС_код}</li>')
        
        # Штрих-коды
        if raw_product.Штрих_код:
            barcodes = [b.strip() for b in raw_product.Штрих_код.split('/') if b.strip()]
            if barcodes:
                barcodes_str = ', '.join(barcodes)
                html_parts.append(f'<li><strong>Штрих-коды:</strong> {barcodes_str}</li>')
        
        # Эксклюзив
        if raw_product.Эксклюзив:
            # Извлекаем значение после "Эксклюзив - "
            if " - " in raw_product.Эксклюзив:
                exclusive_value = raw_product.Эксклюзив.split(" - ", 1)[1]
            else:
                exclusive_value = raw_product.Эксклюзив
            
            # Используем утилиту для нормализации
            exclusive_display = normalize_yes_no(exclusive_value)
            
            html_parts.append(f'<li><strong>Эксклюзив:</strong> {exclusive_display}</li>')
        
        html_parts.append('</ul>')
        
        return "\n".join(html_parts)
    
    def cleanup(self) -> None:
        """
        Очищает кэш характеристик.
        """
        self.specs_cache.clear()
        logger.debug(f"ContentHandler: очищен кэш характеристик")
        super().cleanup()