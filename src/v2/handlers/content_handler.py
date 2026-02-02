"""
ContentHandler - обработчик текстового контента для B2B-WC Converter v2.0.
Обрабатывает: HTML описание, характеристики, документы, видео.
"""
import re
from typing import Dict, Any, List, Tuple
import logging
from urllib.parse import urlparse

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


class TextCleaner:
    """Минимальный очиститель только для неразрывных пробелов."""
    
    @staticmethod
    def clean_html(html: str) -> str:
        """
        Убирает только &nbsp; и \xa0 из HTML.
        ВСЕ теги и структура остаются нетронутыми.
        
        Args:
            html: HTML строка
            
        Returns:
            Очищенная HTML строка
        """
        if not html:
            return ""
        
        # Простые замены - только неразрывные пробелы
        replacements = {
            '&nbsp;': ' ',
            '\xa0': ' ',
            '\u202F': ' ',  # Narrow no-break space
            '\u2007': ' ',  # Figure space
            '\u2060': '',   # Word joiner (нулевая ширина)
        }
        
        result = html
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Для обычного текста - удаляем HTML теги и неразрывные пробелы.
        
        Args:
            text: Текст для очистки
            
        Returns:
            Очищенный текст
        """
        if not text:
            return ""
        
        # 1. Убираем неразрывные пробелы
        text = TextCleaner.clean_html(text)
        
        # 2. Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # 3. Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text


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
        
        # Минимальный очиститель текста
        self.text_cleaner = TextCleaner()
        
        # Поля с документами (тип, русское название, английское название)
        self.doc_fields: List[Tuple[str, str, str]] = [
            ("Чертежи", "чертеж", "drawing"),
            ("Сертификаты", "сертификат", "certificate"),
            ("Промоматериалы", "промо-материал", "promo-material"),
            ("Инструкции", "инструкция", "instruction")
        ]
    
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
        
        # 3. ОЧИЩАЕМ только &nbsp; и \xa0, сохраняя ВЕСЬ HTML
        result["post_content"] = self.text_cleaner.clean_html(html_content)
        
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
    
    def _build_html_content(self, raw_product: RawProduct, 
                           specs: Dict[str, str], article_html: str) -> str:
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
            Очищенный HTML (только &nbsp; и \xa0)
        """
        if not article_html or not article_html.strip():
            return ""
        
        html = article_html.strip()
        
        # Проверяем, есть ли теги HTML
        if not re.search(r'<[^>]+>', html):
            # Если нет HTML тегов, оборачиваем в параграф
            html = f"<p>{html}</p>"
        
        # Очищаем только неразрывные пробелы, сохраняя теги
        return self.text_cleaner.clean_html(html)
    
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
        
        html_parts = ['<div class="specifications">',
                      '<h2>Технические характеристики</h2>', 
                      '<ul>']
        
        for key, value in sorted(specs.items()):
            # Очищаем значения от &nbsp; перед добавлением
            clean_key = self.text_cleaner.clean_html(key)
            clean_value = self.text_cleaner.clean_html(value)
            html_parts.append(f'<li><strong>{clean_key}:</strong> {clean_value}</li>')
        
        html_parts.append('</ul></div>')
        
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
            html_parts.append('<div class="documentation">')
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
                    # Каждая ссылка в отдельном параграфе
                    html_parts.append(f'<p>{doc_html}</p>')
            
            html_parts.append('</div>')
        
        # Видео
        video_url = raw_product.Видео.strip() if raw_product.Видео else ""
        if video_url:
            video_html = self._build_video_html(video_url, raw_product)
            if video_html:
                html_parts.append('<div class="video">')
                if docs:
                    html_parts.append('<h3>Видеообзор</h3>')
                else:
                    html_parts.append('<h3>Документация и видео</h3>')
                html_parts.append(f'<p>{video_html}</p>')
                html_parts.append('</div>')
        
        if not html_parts:
            return ""
        
        return "\n".join(html_parts)
    
    def _collect_documents(self, raw_product: RawProduct) -> List[Tuple[str, str]]:
        """
        Собирает все документы товара.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Список кортежей (тип_документа, URL)
        """
        documents = []
        
        for field_name, doc_type_ru, _ in self.doc_fields:
            doc_urls = getattr(raw_product, field_name, "").strip()
            
            if not doc_urls:
                continue
                
            # Разделяем URL по разным разделителям
            # Регулярное выражение для разделения: запятые, точки с запятой, пробелы
            urls_list = re.split(r'[,\s;]+', doc_urls)
            
            # Очищаем и фильтруем URL
            for url in urls_list:
                url = url.strip()
                if url and self._is_valid_url(url):
                    documents.append((doc_type_ru, url))
        
        # Убираем дубликаты, сохраняя порядок
        unique_docs = []
        seen = set()
        for doc_type, url in documents:
            key = (doc_type, url)
            if key not in seen:
                seen.add(key)
                unique_docs.append((doc_type, url))
        
        return unique_docs
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Проверяет, является ли строка валидным URL.
        
        Args:
            url: Строка для проверки
            
        Returns:
            True если валидный URL, иначе False
        """
        if not url or len(url) < 8:  # Минимальная длина для http://
            return False
        
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except:
            return False
    
    def _build_doc_link_html(self, doc_type: str, doc_url: str, 
                            raw_product: RawProduct) -> str:
        """
        Строит HTML ссылку на документ.
        
        Args:
            doc_type: Тип документа (русский)
            doc_url: URL документа
            raw_product: Сырые данные продукта
            
        Returns:
            HTML ссылка
        """
        # Получаем английское название типа документа
        doc_type_en = ""
        for _, ru_type, en_type in self.doc_fields:
            if ru_type == doc_type:
                doc_type_en = en_type
                break
        
        # Получаем шаблон из конфига
        template = self.config_manager.get_setting(
            'templates.doc_link_item',
            '<img style="vertical-align: middle; margin-right: 8px;" '
            'src="{icon_url}" alt="{doc_type_en} icon" width="32" height="32" />'
            '<a href="{doc_url}" target="_blank" rel="noopener noreferrer" '
            'title="{doc_type} {product_title}">'
            '{doc_type} {product_title} (PDF)'
            '</a>'
        )
        
        # URL иконки PDF
        icon_url = self.config_manager.get_setting(
            'paths.pdf_icon_url',
            'https://cdn-icons-png.freepik.com/512/299/299378.png'
        )
        
        # Название продукта
        product_title = raw_product.Наименование or "Товар"
        clean_title = self.text_cleaner.clean_html(product_title)
        
        # Заменяем плейсхолдеры
        html = template.format(
            icon_url=icon_url,
            doc_url=doc_url,
            doc_type=doc_type.capitalize(),
            doc_type_en=doc_type_en,
            product_title=clean_title
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
            clean_title = self.text_cleaner.clean_html(product_title)
            return (f'<a href="{video_url}" target="_blank" rel="noopener noreferrer" '
                   f'title="Видеообзор: {clean_title}">Видеообзор: {clean_title}</a>')
        
        # Если есть YouTube ID, создаем iframe для встраивания
        iframe_template = self.config_manager.get_setting(
            'templates.video_iframe',
            '<div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">'
            '<iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" '
            'src="https://www.youtube.com/embed/{youtube_id}" '
            'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            'allowfullscreen title="Видеообзор: {product_title}"></iframe>'
            '</div>'
        )
        
        # Альтернативный вариант с превью
        thumbnail_template = self.config_manager.get_setting(
            'templates.video_link_item',
            '<a href="{video_url}" target="_blank" rel="noopener noreferrer" '
            'title="Видеообзор: {product_title}">'
            '<img src="{thumbnail_url}" alt="Видеообзор: {product_title}" '
            'style="max-width: 300px; border: 1px solid #ddd; border-radius: 4px;" />'
            '</a>'
        )
        
        # Генерируем URL превью
        thumbnail_url = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
        
        # Название продукта
        product_title = raw_product.Наименование or "Товар"
        clean_title = self.text_cleaner.clean_html(product_title)
        
        # Выбираем шаблон в зависимости от настройки
        use_iframe = self.config_manager.get_setting(
            'features.use_video_iframe', True
        )
        
        if use_iframe:
            html = iframe_template.format(
                youtube_id=youtube_id,
                product_title=clean_title
            )
        else:
            html = thumbnail_template.format(
                video_url=video_url,
                thumbnail_url=thumbnail_url,
                product_title=clean_title
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
        items = []
        
        # Бренд
        if raw_product.Бренд:
            clean_brand = self.text_cleaner.clean_html(raw_product.Бренд)
            items.append(f'<li><strong>Бренд:</strong> {clean_brand}</li>')
        
        # Артикул
        if raw_product.Артикул:
            clean_art = self.text_cleaner.clean_html(raw_product.Артикул)
            items.append(f'<li><strong>Артикул производителя:</strong> {clean_art}</li>')
        
        # НС-код
        if raw_product.НС_код:
            clean_ns = self.text_cleaner.clean_html(raw_product.НС_код)
            items.append(f'<li><strong>НС-код:</strong> {clean_ns}</li>')
        
        # Штрих-коды
        if raw_product.Штрих_код:
            barcodes = [b.strip() for b in raw_product.Штрих_код.split('/') if b.strip()]
            if barcodes:
                clean_barcodes = [self.text_cleaner.clean_html(b) for b in barcodes]
                barcodes_str = ', '.join(clean_barcodes)
                items.append(f'<li><strong>Штрих-коды:</strong> {barcodes_str}</li>')
        
        # Эксклюзив
        if raw_product.Эксклюзив:
            # Извлекаем значение после "Эксклюзив - "
            if " - " in raw_product.Эксклюзив:
                exclusive_value = raw_product.Эксклюзив.split(" - ", 1)[1]
            else:
                exclusive_value = raw_product.Эксклюзив
            
            # Используем утилиту для нормализации
            exclusive_display = normalize_yes_no(exclusive_value)
            clean_exclusive = self.text_cleaner.clean_html(exclusive_display)
            
            items.append(f'<li><strong>Эксклюзив:</strong> {clean_exclusive}</li>')
        
        if not items:
            return ""
        
        html_parts = ['<div class="additional-info">',
                      '<h3>Дополнительная информация</h3>', 
                      '<ul>']
        html_parts.extend(items)
        html_parts.append('</ul></div>')
        
        return "\n".join(html_parts)
    
    def cleanup(self) -> None:
        """
        Очищает кэш характеристик.
        """
        self.specs_cache.clear()
        logger.debug(f"ContentHandler: очищен кэш характеристик")
        super().cleanup()