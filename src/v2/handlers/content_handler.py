"""
ContentHandler - обработчик текстового контента для B2B-WC Converter v2.0.
Обрабатывает: HTML описание, характеристики, документы, видео.
"""
import re
import logging
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
from html import unescape

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


class HtmlRepair:
    """Класс для ремонта поврежденного HTML."""
    
    @staticmethod
    def repair(html: str) -> str:
        """
        Ремонтирует ВСЕ повреждения HTML в один проход.
        
        Args:
            html: Поврежденная HTML строка
            
        Returns:
            Исправленная валидная HTML строка
        """
        if not html:
            return ""

        # 1. Декодируем HTML сущности ПЕРВЫМ делом!
        from html import unescape
        html = unescape(html)

        # 2. Теперь заменяем ВСЕ оставшиеся варианты
        # Универсальная замена &ndash с любыми пробелами
        html = re.sub(r'&(\s*|\u202F|\u2007|\u2060)?ndash(\s*|\u202F|\u2007|\u2060)?;?', '-', html, flags=re.IGNORECASE)

        # Универсальная замена &bull
        html = re.sub(r'&(\s*|\u202F|\u2007|\u2060)?bull(\s*|\u202F|\u2007|\u2060)?;?', '•', html, flags=re.IGNORECASE)

        # Универсальная замена &deg
        html = re.sub(r'&(\s*|\u202F|\u2007|\u2060)?deg(\s*|\u202F|\u2007|\u2060)?;?', '°', html, flags=re.IGNORECASE)

        # 3. Остальные замены (только один раз!)
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&ndash;', '-')
        html = html.replace('\xa0', ' ')

        # 4. Исправляем битые теги и <br> (как у вас)
        html = html.replace('</\x01>', '</ul>')
        html = re.sub(r'</p>\s*<br\s*/?\s*>\s*<h', '</p>\n<h', html, flags=re.IGNORECASE)
        # ... остальные исправления тегов

        # 5. Финальная чистка
        html = re.sub(r'\s+', ' ', html)
        html = re.sub(r'>\s+<', '><', html)
        return html.strip()

    
    @staticmethod
    def clean_text(text: str) -> str:
        """Для обычного текста - удаляем HTML теги."""
        if not text:
            return ""
        
        # Убираем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Убираем лишние пробелы
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
        
        # Ремонтник HTML
        self.html_repair = HtmlRepair
        
        # Поля с документами
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
        
        # 1. Парсим характеристики
        specs_str = safe_getattr(raw_product, "Характеристики")
        specs = self._parse_specifications(specs_str)
        
        # 2. Собираем HTML контент
        article_html = safe_getattr(raw_product, "Статья")
        html_content = self._build_html_content(raw_product, specs, article_html)
        
        # 3. ВАЖНО: НЕ чистим HTML здесь! Только сохраняем
        result["post_content"] = html_content
        
        logger.debug(f"ContentHandler обработал продукт {raw_product.НС_код}")
        return result
    
    def _parse_specifications(self, specs_string: str) -> Dict[str, str]:
        """Парсит строку характеристик."""
        if not specs_string or not specs_string.strip():
            return {}
        
        cache_key = hash(specs_string)
        if cache_key in self.specs_cache:
            return self.specs_cache[cache_key].copy()
        
        specs = parse_specifications(specs_string)
        
        normalized_specs = {}
        for key, value in specs.items():
            clean_key = self.html_repair.clean_text(key).strip()
            clean_value = self.html_repair.clean_text(value).strip()

            # 2. ЗАМЕНЯЕМ | на / в КЛЮЧЕ и ЗНАЧЕНИИ
            clean_key = clean_key.replace('|', '/')
            clean_value = clean_value.replace('|', '/')

            
            if clean_key and clean_value:
                normalized_value = normalize_yes_no(clean_value)
                normalized_specs[clean_key] = normalized_value
        
        self.specs_cache[cache_key] = normalized_specs.copy()
        return normalized_specs
    
    def _build_html_content(self, raw_product: RawProduct, specs: Dict[str, str], article_html: str) -> str:
        """
        Собирает HTML контент из различных источников.
        ВСЕ исправления HTML делаются ТОЛЬКО здесь!
        """
        html_parts = []
        
        # Блок 1: HTML из статьи (РЕМОНТИРУЕМ)
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
        full_html = "\n\n".join(html_parts)

        #     # ОТЛАДКА
        # print("="*80)
        # print(f"!!!DEBUG _build_html_content ДО repair: содержит '&ndash'? {'&ndash' in full_html}")
        
        # result = self.html_repair.repair(full_html)
        
        # print(f"!!!DEBUG _build_html_content ПОСЛЕ repair: содержит '&ndash'? {'&ndash' in result}")
        # print(f"!!!Первые 300 символов результата: {repr(result[:300])}")
        # print("="*80)
        
        # ФИНАЛЬНЫЙ РЕМОНТ всего HTML
        return self.html_repair.repair(full_html)
    
    def _process_article(self, article_html: str) -> str:
        """Обрабатывает HTML статью."""
        if not article_html or not article_html.strip():
            return ""
        
        # Ремонтируем HTML статьи
        html = self.html_repair.repair(article_html)
        
        # Если нет HTML тегов, оборачиваем в параграф
        if not re.search(r'<[^>]+>', html):
            html = f"<p>{html}</p>"
        
        return html
    
    def _build_specifications_html(self, specs: Dict[str, str]) -> str:
        """Строит HTML для технических характеристик."""
        if not specs:
            return ""
        
        html_parts = ['<div class="specifications">',
                      '<h2>Технические характеристики</h2>', 
                      '<ul>']
        
        for key, value in sorted(specs.items()):
            clean_key = self.html_repair.repair(key)
            clean_value = self.html_repair.repair(value)
            html_parts.append(f'<li><strong>{clean_key}:</strong> {clean_value}</li>')

            # Дополнительно: убираем HTML теги, если они есть
            clean_key = re.sub(r'<[^>]+>', '', clean_key)
            clean_value = re.sub(r'<[^>]+>', '', clean_value)
            
            html_parts.append(f'<li><strong>{clean_key}:</strong> {clean_value}</li>')

        
        html_parts.append('</ul></div>')
        
        return "\n".join(html_parts)
    
    def _build_docs_video_html(self, raw_product: RawProduct) -> str:
        """Строит HTML для документации и видео."""
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

                html_parts.append(f'<h4>{doc_type.capitalize()}</h4>')  # Подзаголовок ВСЕГДА
                
                for doc_url in urls:
                    doc_html = self._build_doc_link_html(doc_type, doc_url, raw_product)
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
        """Собирает все документы товара."""
        documents = []
        
        for field_name, doc_type_ru, _ in self.doc_fields:
            doc_urls = getattr(raw_product, field_name, "").strip()
            
            if not doc_urls:
                continue
                
            urls_list = re.split(r'[,\s;]+', doc_urls)
            
            for url in urls_list:
                url = url.strip()
                if url and self._is_valid_url(url):
                    documents.append((doc_type_ru, url))
        
        # Убираем дубликаты
        unique_docs = []
        seen = set()
        for doc_type, url in documents:
            key = (doc_type, url)
            if key not in seen:
                seen.add(key)
                unique_docs.append((doc_type, url))
        
        return unique_docs
    
    def _is_valid_url(self, url: str) -> bool:
        """Проверяет валидность URL."""
        if not url or len(url) < 8:
            return False
        
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except:
            return False
    
    def _build_doc_link_html(self, doc_type: str, doc_url: str, raw_product: RawProduct) -> str:
        """Строит HTML ссылку на документ."""
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
        clean_title = self.html_repair.clean_text(product_title)
        
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
        """Строит HTML для видео."""
        # Используем утилиту для извлечения YouTube ID
        youtube_id = extract_youtube_id(video_url)
        
        if not youtube_id:
            product_title = raw_product.Наименование or "Товар"
            clean_title = self.html_repair.clean_text(product_title)
            return (f'<a href="{video_url}" target="_blank" rel="noopener noreferrer" '
                   f'title="Видеообзор: {clean_title}">Видеообзор: {clean_title}</a>')
        
        # Если есть YouTube ID, создаем iframe
        iframe_template = self.config_manager.get_setting(
            'templates.video_iframe',
            '<div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">'
            '<iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" '
            'src="https://www.youtube.com/embed/{youtube_id}" '
            'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            'allowfullscreen title="Видеообзор: {product_title}"></iframe>'
            '</div>'
        )
        
        thumbnail_template = self.config_manager.get_setting(
            'templates.video_link_item',
            '<a href="{video_url}" target="_blank" rel="noopener noreferrer" '
            'title="Видеообзор: {product_title}">'
            '<img src="{thumbnail_url}" alt="Видеообзор: {product_title}" '
            'style="max-width: 300px; border: 1px solid #ddd; border-radius: 4px;" />'
            '</a>'
        )
        
        thumbnail_url = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
        
        product_title = raw_product.Наименование or "Товар"
        clean_title = self.html_repair.clean_text(product_title)
        
        use_iframe = self.config_manager.get_setting('features.use_video_iframe', True)
        
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
        """Строит HTML для дополнительной информации."""
        items = []
        
        # Бренд
        if raw_product.Бренд:
            clean_brand = self.html_repair.clean_text(raw_product.Бренд)
            if clean_brand:
                items.append(f'<li><strong>Бренд:</strong> {clean_brand}</li>')
        
        # Артикул
        if raw_product.Артикул:
            clean_art = self.html_repair.clean_text(raw_product.Артикул)
            if clean_art:
                items.append(f'<li><strong>Артикул производителя:</strong> {clean_art}</li>')
        
        # НС-код
        if raw_product.НС_код:
            clean_ns = self.html_repair.clean_text(raw_product.НС_код)
            if clean_ns:
                items.append(f'<li><strong>НС-код:</strong> {clean_ns}</li>')
        
        # Штрих-коды
        if raw_product.Штрих_код:
            barcodes = [b.strip() for b in raw_product.Штрих_код.split('/') if b.strip()]
            if barcodes:
                clean_barcodes = [self.html_repair.clean_text(b) for b in barcodes]
                clean_barcodes = [b for b in clean_barcodes if b]
                if clean_barcodes:
                    barcodes_str = ', '.join(clean_barcodes)
                    items.append(f'<li><strong>Штрих-коды:</strong> {barcodes_str}</li>')
        
        # Эксклюзив
        if raw_product.Эксклюзив:
            if " - " in raw_product.Эксклюзив:
                exclusive_value = raw_product.Эксклюзив.split(" - ", 1)[1]
            else:
                exclusive_value = raw_product.Эксклюзив
            
            exclusive_display = normalize_yes_no(exclusive_value)
            clean_exclusive = self.html_repair.clean_text(exclusive_display)
            
            if clean_exclusive:
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
        """Очищает кэш характеристик."""
        self.specs_cache.clear()
        logger.debug(f"ContentHandler: очищен кэш характеристик")
        super().cleanup()