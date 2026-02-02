"""
ContentHandler - обработчик текстового контента для B2B-WC Converter v2.0.
Обрабатывает: HTML описание, характеристики, документы, видео.
"""
import re
import logging
from typing import Dict, Any, List, Tuple, Callable
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
        
        # Все варианты неразрывных пробелов
        replacements = {
            '&nbsp;': ' ',
            '&#160;': ' ',
            '&#xA0;': ' ',
            '\xa0': ' ',
            '\u00A0': ' ',
            '\u202F': ' ',  # Narrow no-break space
            '\u2007': ' ',  # Figure space
            '\u2060': '',   # Word joiner (нулевая ширина)
            '\uFEFF': '',   # Zero-width no-break space
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
            # Очищаем ключ и значение от битых символов
            clean_key = self.text_cleaner.clean_html(key).strip()
            clean_value = self.text_cleaner.clean_html(value).strip()
            
            # Пропускаем пустые
            if clean_key and clean_value:
                normalized_value = normalize_yes_no(clean_value)
                normalized_specs[clean_key] = normalized_value
        
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
        
        # Блок 1: HTML из статьи (исправляем некорректный HTML)
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
        
        # Финальная очистка всего контента
        cleaned_html = self._clean_html_content(full_html)
        
        # ФИНАЛЬНАЯ ОЧИСТКА перед сохранением
        return self._final_html_cleanup(cleaned_html)
    
    def _final_html_cleanup(self, html: str) -> str:
        """
        Финальная очистка HTML перед сохранением.
        
        Args:
            html: HTML строка
            
        Returns:
            Очищенный HTML
        """
        if not html:
            return ""
        
        # 1. Исправляем битые заголовки (если остались)
        html = re.sub(r'</h([1-6])>\s*</p>', r'</h\1>', html)
        
        # 2. Исправляем некорректные закрывающие теги заголовков
        html = re.sub(r'</h\[1-6\]>', r'</h4>', html)
        
        # 3. Убираем лишние <br /> между блоками
        html = re.sub(r'</h[1-6]>\s*<br\s*/?>\s*', r'</h[1-6]>\n', html)
        html = re.sub(r'</(ul|ol)>\s*<br\s*/?>\s*', r'</\1>\n', html)
        html = re.sub(r'</p>\s*<br\s*/?>\s*', r'</p>\n', html)
        html = re.sub(r'</div>\s*<br\s*/?>\s*', r'</div>\n', html)
        
        # 4. Убираем <br /> в начале списков
        html = re.sub(r'<(ul|ol)>\s*<br\s*/?>\s*', r'<\1>\n', html)
        html = re.sub(r'<(ul|ol)>\s*<br\s*/?>\s*<li>', r'<\1>\n<li>', html)
        
        # 5. Убираем <br /> внутри списков
        html = re.sub(r'</li>\s*<br\s*/?>\s*<li>', r'</li>\n<li>', html)
        
        # 6. Убираем теги <p> внутри закрывающих </ul>
        html = self._remove_p_tags_inside_list_closing(html)
        
        # 7. Исправляем двойные кавычки в атрибутах class (если есть)
        html = re.sub(r'class=""([^""]+)""', r'class="\1"', html)
        
        # 8. Убираем множественные переносы строк
        html = re.sub(r'\n\s*\n+', '\n', html)
        
        # 9. Убираем лишние пробелы
        html = re.sub(r'\s+', ' ', html)
        html = re.sub(r'>\s+<', '><', html)
        
        # 10. Убираем пустые строки в начале/конце
        html = html.strip()
        
        return html

    def _remove_empty_paragraphs(self, html: str) -> str:
        """
        Удаляет полностью пустые параграфы.
        
        Args:
            html: HTML строка
            
        Returns:
            HTML без пустых параграфов
        """
        if not html:
            return html
        
        # ПЕРВОЕ: Исправляем слипшиеся теги перед удалением
        # Исправляем: </ul></p> → </ul>
        # Исправляем: </ol></p> → </ol>
        html = re.sub(r'</(ul|ol)>\s*</p>', r'</\1>', html, flags=re.IGNORECASE)
        
        # ВТОРОЕ: Убираем ВСЕ пустые параграфы
        patterns = [
            r'<p[^>]*>\s*</p>',                    # Пустые
            r'<p[^>]*>\s*&nbsp;\s*</p>',           # С &nbsp;
            r'<p[^>]*>\s*<br\s*/?>\s*</p>',        # С <br/>
            r'<p[^>]*>\s*\t*\s*</p>',              # С табуляциями
        ]
        
        for pattern in patterns:
            html = re.sub(pattern, '', html, flags=re.IGNORECASE)
        
        # Убираем множественные переносы строк
        html = re.sub(r'\n\s*\n\s*\n+', '\n\n', html)
        
        return html


        """
        Комплексное исправление всех типов некорректного HTML.
        
        Args:
            html: HTML строка для исправления
            
        Returns:
            Исправленная HTML строка
        """
        if not html:
            return html
        
        # Список исправлений в порядке приоритета
        fixes = [
            # 1. Исправляем слипшиеся теги: <ul></p> → <ul>
            (r'<(ul|ol)>\s*</p>', r'<\1>'),
            
            # 2. Убираем все теги <p> и </p> изнутри списков
            (r'<(ul|ol)[^>]*>(.*?)</\1>', 
            lambda m: f'<{m.group(1)}>' + re.sub(r'</?p[^>]*>', '', m.group(2)) + f'</{m.group(1)}>'),
            
            # 3. Исправляем: <ul></ul><p>></p><li> → <ul><li>
            (r'<(ul|ol)>\s*</\1>\s*<p[^>]*>>\s*</p>\s*<li>', r'<\1><li>'),
            
            # 4. Исправляем: <ul></ul><li> → <ul><li>
            (r'<(ul|ol)>\s*</\1>\s*<li>', r'<\1><li>'),
            
            # 5. Убираем теги <p> сразу после заголовков
            (r'(</h[1-6]>)\s*<p[^>]*>\s*</p>', r'\1'),
            
            # 6. Убираем теги <p> перед списками
            (r'<p[^>]*>\s*</p>\s*<(ul|ol)', r'<\1'),
            
            # 7. Убираем теги <p> после списков
            (r'</(ul|ol)>\s*<p[^>]*>\s*</p>', r'</\1>'),
            
            # 8. Исправляем битые теги вроде <p>>
            (r'<p[^>]*>></p>', ''),
            (r'<p>></p>', ''),
            
            # 9. Исправляем незакрытые списки
            (r'<(ul|ol)(?![^>]*/>)(?!(.*?)</\1>)', 
            lambda m: f'<{m.group(1)}>{m.group(2) if m.group(2) else ""}</{m.group(1)}>'),
        ]
        
        for pattern, replacement in fixes:
            if callable(replacement):
                html = re.sub(pattern, replacement, html, flags=re.DOTALL | re.IGNORECASE)
            else:
                html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)
        
        return html

    def _fix_all_broken_html(self, html: str) -> str:
        """
        Комплексное исправление всех типов некорректного HTML.
        
        Args:
            html: HTML строка для исправления
            
        Returns:
            Исправленная HTML строка
        """
        if not html:
            return html
        
        # Список исправлений в порядке приоритета
        fixes = [
            # 1. Исправляем битые заголовки: </h[1-6]></p> → </h4>
            (r'</h([1-6])>\s*</p>', r'</h\1>'),
            
            # 2. Исправляем: <h4>...</h[1-6]></p> → <h4>...</h4>
            (r'<h([1-6])[^>]*>(.*?)</h[1-6]>\s*</p>', r'<h\1>\2</h\1>'),
            
            # 3. Исправляем слипшиеся теги: <ul></p> → <ul>
            (r'<(ul|ol)>\s*</p>', r'<\1>'),
            
            # 4. Убираем все теги <p> и </p> изнутри списков
            (r'<(ul|ol)[^>]*>(.*?)</\1>', 
            lambda m: f'<{m.group(1)}>' + re.sub(r'</?p[^>]*>', '', m.group(2)) + f'</{m.group(1)}>'),
            
            # 5. Убираем теги <p> сразу после заголовков
            (r'(</h[1-6]>)\s*<p[^>]*>\s*</p>', r'\1'),
            
            # 6. Убираем теги <p> перед списками
            (r'<p[^>]*>\s*</p>\s*<(ul|ol)', r'<\1'),
            
            # 7. Убираем теги <p> после списков
            (r'</(ul|ol)>\s*<p[^>]*>\s*</p>', r'</\1>'),
            
            # 8. Исправляем битые теги вроде <p>>
            (r'<p[^>]*>></p>', ''),
            (r'<p>></p>', ''),
            
            # 9. Убираем открывающие <p> без закрывающих внутри списков
            (r'<(ul|ol)>(.*?)<p>(?!.*</p>)(.*?)</\1>', 
            lambda m: f'<{m.group(1)}>{m.group(2)}{m.group(3)}</{m.group(1)}>'),
        ]
        
        for pattern, replacement in fixes:
            if callable(replacement):
                html = re.sub(pattern, replacement, html, flags=re.DOTALL | re.IGNORECASE)
            else:
                html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)
        
        # 10. Убираем лишние <p> теги внутри закрывающих </ul>
        html = self._remove_p_tags_inside_list_closing(html)
        
        return html

    def _remove_p_tags_inside_list_closing(self, html: str) -> str:
        """
        Убирает теги <p> внутри закрывающих тегов списков.
        Пример: </li><p></ul> → </li></ul>
        
        Args:
            html: HTML строка
            
        Returns:
            Исправленная HTML строка
        """
        if not html:
            return html
        
        # Исправляем: </li><p></ul> → </li></ul>
        html = re.sub(r'</li>\s*<p[^>]*>\s*</(ul|ol)>', r'</li></\1>', html, flags=re.IGNORECASE)
        
        # Исправляем: </li><p></p></ul> → </li></ul>
        html = re.sub(r'</li>\s*<p[^>]*>\s*</p>\s*</(ul|ol)>', r'</li></\1>', html, flags=re.IGNORECASE)
        
        # Исправляем: <p></ul> → </ul>
        html = re.sub(r'<p[^>]*>\s*</(ul|ol)>', r'</\1>', html, flags=re.IGNORECASE)
        
        return html

    def _clean_html_content(self, html: str) -> str:
        """
        Полная очистка HTML контента.
        
        Args:
            html: HTML строка
            
        Returns:
            Очищенная HTML строка
        """
        if not html:
            return ""
        
        # 1. Очищаем неразрывные пробелы
        html = self.text_cleaner.clean_html(html)
        
        # 2. Исправляем структуру HTML
        html = self._fix_all_broken_html(html)
        
        # 3. Убираем полностью пустые параграфы
        html = self._remove_empty_paragraphs(html)
        
        # 4. Исправляем остальные битые структуры
        # Исправляем: <ul></ul> с последующим содержимым
        html = self._fix_empty_lists_with_content(html)
        
        # 5. Убираем лишние пробелы между тегами
        html = re.sub(r'>\s+<', '><', html)
        
        # 6. Убираем множественные переносы строк
        html = re.sub(r'\n\s*\n+', '\n\n', html)
        
        return html.strip()

    def _fix_empty_lists_with_content(self, html: str) -> str:
        """
        Исправляет пустые списки с последующим содержимым.
        Пример: <ul></ul><li> → <ul><li>
        
        Args:
            html: HTML строка
            
        Returns:
            Исправленная HTML строка
        """
        if not html:
            return html
        
        # Исправляем пустые списки с последующими элементами
        patterns = [
            # <ul></ul><li>...</li> → <ul><li>...</li></ul>
            (r'<(ul|ol)>\s*</\1>\s*(<li>.*?</li>)', r'<\1>\2</\1>'),
            
            # <ul></ul> внутри блока с классами
            (r'(<div[^>]*>.*?)<(ul|ol)>\s*</\2>(.*?</div>)', 
            lambda m: f'{m.group(1)}<{m.group(2)}></{m.group(2)}>{m.group(3)}'),
        ]
        
        for pattern, replacement in patterns:
            if callable(replacement):
                html = re.sub(pattern, replacement, html, flags=re.DOTALL)
            else:
                html = re.sub(pattern, replacement, html, flags=re.DOTALL | re.IGNORECASE)
        
        return html

    def _process_article(self, article_html: str) -> str:
        """
        Обрабатывает HTML статью.
        
        Args:
            article_html: HTML текст статьи
            
        Returns:
            Очищенный и исправленный HTML
        """
        if not article_html or not article_html.strip():
            return ""
        
        # ОТЛАДКА: покажем что приходит
        logger.debug(f"Исходный HTML статьи (первые 500 символов): {article_html[:500]}")
        
        html = article_html.strip()
        
        # 1. Очищаем неразрывные пробелы
        html = self.text_cleaner.clean_html(html)
        
        # 2. Исправляем ВСЕ некорректные структуры списков (ОСНОВНОЕ ИСПРАВЛЕНИЕ)
        html = self._fix_all_broken_html(html)
        
        # 3. Исправляем битые заголовки
        html = self._fix_broken_headers(html)
        
        # 4. Убираем полностью пустые параграфы
        html = self._remove_empty_paragraphs(html)
        
        # 5. Если совсем нет HTML тегов, оборачиваем в параграф
        if not re.search(r'<[^>]+>', html):
            html = f"<p>{html}</p>"
        
        return html

    def _fix_broken_headers(self, html: str) -> str:
        """
        Исправляет битые заголовки.
        
        Args:
            html: HTML строка
            
        Returns:
            Исправленная HTML строка
        """
        if not html:
            return html
        
        # Исправляем: <h4>...</h[1-6]></p> → <h4>...</h4>
        patterns = [
            (r'<h([1-6])[^>]*>(.*?)</h\[1-6\]>\s*</p>', r'<h\1>\2</h\1>'),
            (r'<h([1-6])[^>]*>(.*?)</h[1-6]>\s*</p>', r'<h\1>\2</h\1>'),
            (r'<h([1-6])[^>]*>(.*?)</h[1-6]></p>', r'<h\1>\2</h\1>'),
        ]
        
        for pattern, replacement in patterns:
            html = re.sub(pattern, replacement, html, flags=re.DOTALL | re.IGNORECASE)
        
        return html

        """
        Обрабатывает HTML статью.
        
        Args:
            article_html: HTML текст статьи
            
        Returns:
            Очищенный и исправленный HTML
        """
        if not article_html or not article_html.strip():
            return ""
        
        html = article_html.strip()
        
        # 1. Очищаем неразрывные пробелы
        html = self.text_cleaner.clean_html(html)
        
        # 2. Исправляем ВСЕ некорректные структуры списков (ОСНОВНОЕ ИСПРАВЛЕНИЕ)
        html = self._fix_all_broken_html(html)
        
        # 3. Убираем полностью пустые параграфы
        html = self._remove_empty_paragraphs(html)
        
        # 4. Если совсем нет HTML тегов, оборачиваем в параграф
        if not re.search(r'<[^>]+>', html):
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
            if clean_brand:
                items.append(f'<li><strong>Бренд:</strong> {clean_brand}</li>')
        
        # Артикул
        if raw_product.Артикул:
            clean_art = self.text_cleaner.clean_html(raw_product.Артикул)
            if clean_art:
                items.append(f'<li><strong>Артикул производителя:</strong> {clean_art}</li>')
        
        # НС-код
        if raw_product.НС_код:
            clean_ns = self.text_cleaner.clean_html(raw_product.НС_код)
            if clean_ns:
                items.append(f'<li><strong>НС-код:</strong> {clean_ns}</li>')
        
        # Штрих-коды
        if raw_product.Штрих_код:
            barcodes = [b.strip() for b in raw_product.Штрих_код.split('/') if b.strip()]
            if barcodes:
                clean_barcodes = [self.text_cleaner.clean_html(b) for b in barcodes]
                clean_barcodes = [b for b in clean_barcodes if b]  # Фильтруем пустые
                if clean_barcodes:
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
        """
        Очищает кэш характеристик.
        """
        self.specs_cache.clear()
        logger.debug(f"ContentHandler: очищен кэш характеристик")
        super().cleanup()