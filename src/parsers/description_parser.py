"""
Парсер для сборки полного HTML описания товара
"""

from typing import Dict, Any, List, Optional
from .base_parser import BaseParser, ParseResult
from src.utils.logger import log_info, log_warning


class DescriptionParser(BaseParser):
    """
    Парсер для сборки полного HTML описания товара
    
    Объединяет:
    1. Статью (из колонки "Статья")
    2. Характеристики (от SpecsParser)
    3. Документы (от DocsParser)
    4. Видео (из колонки "Видео")
    """
    
    def __init__(self):
        """Инициализация парсера описания"""
        super().__init__(column_name="Описание")
    
    def parse(
        self,
        article_html: str,
        specs_html: str = "",
        documents_html: str = "",
        video_url: str = "",
        product_name: str = ""
    ) -> ParseResult:
        """
        Сборка полного HTML описания
        
        Args:
            article_html: HTML статья из колонки "Статья"
            specs_html: HTML характеристики от SpecsParser
            documents_html: HTML документы от DocsParser
            video_url: URL видео из колонки "Видео"
            product_name: Название товара (для заголовков)
        
        Returns:
            ParseResult с HTML описанием
        """
        errors = []
        warnings = []
        
        # Очищаем входные данные
        article_html = self.clean_value(article_html) if article_html else ""
        specs_html = self.clean_value(specs_html) if specs_html else ""
        documents_html = self.clean_value(documents_html) if documents_html else ""
        video_url = self.clean_value(video_url) if video_url else ""
        
        try:
            # 1. Начинаем сборку описания
            html_parts = []
            
            # 2. Добавляем статью (если есть)
            if article_html:
                # Очищаем от возможных дублирующихся тегов body/html
                article_html = self._clean_html(article_html)
                html_parts.append(article_html)
            
            # 3. Добавляем характеристики (если есть)
            if specs_html:
                html_parts.append(specs_html)
            elif not article_html:
                warnings.append("Нет ни статьи, ни характеристик для описания")
            
            # 4. Добавляем видео (если есть)
            if video_url:
                video_html = self._create_video_html(video_url, product_name)
                html_parts.append(video_html)
            
            # 5. Добавляем документы (если есть)
            if documents_html:
                html_parts.append(documents_html)
            
            # 6. Собираем полное описание
            if html_parts:
                full_description = "\n\n".join(html_parts)
                
                # Проверяем длину
                if len(full_description) > 10000:
                    warnings.append(f"Описание очень длинное: {len(full_description)} символов")
                
                data = {
                    "html": full_description,
                    "has_article": bool(article_html),
                    "has_specs": bool(specs_html),
                    "has_video": bool(video_url),
                    "has_documents": bool(documents_html),
                    "length": len(full_description),
                    "parts_count": len(html_parts)
                }
            else:
                data = {
                    "html": "",
                    "has_article": False,
                    "has_specs": False,
                    "has_video": False,
                    "has_documents": False,
                    "length": 0,
                    "parts_count": 0
                }
                warnings.append("Создано пустое описание")
            
            return self.create_result(
                data=data,
                original_value=f"Статья: {len(article_html)} chars, Спецификации: {len(specs_html)} chars",
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Ошибка при сборке описания: {str(e)}")
            return self.create_result(
                data={"html": "", "error": str(e)},
                original_value="",
                errors=errors,
                warnings=warnings
            )
    
    def _clean_html(self, html: str) -> str:
        """
        Очистка HTML от лишних тегов
        
        Args:
            html: Исходный HTML
        
        Returns:
            Очищенный HTML
        """
        if not html:
            return ""
        
        # Убираем теги <html>, <body>, <head> если они есть
        # Но оставляем контент внутри
        replacements = [
            ('<html>', ''),
            ('</html>', ''),
            ('<body>', ''),
            ('</body>', ''),
            ('<head>', ''),
            ('</head>', ''),
            ('<!DOCTYPE html>', ''),
            ('<?xml version="1.0" encoding="UTF-8"?>', '')
        ]
        
        for old, new in replacements:
            html = html.replace(old, new)
        
        # Убираем множественные переводы строк
        import re
        html = re.sub(r'\n{3,}', '\n\n', html)
        
        return html.strip()
    
    def _create_video_html(self, video_url: str, product_name: str) -> str:
        """
        Создание HTML для видео (YouTube или другое)
        
        Args:
            video_url: URL видео
            product_name: Название товара
        
        Returns:
            HTML код для вставки видео
        """
        # Извлекаем ID видео для YouTube
        video_id = self._extract_youtube_id(video_url)
        
        if video_id:
            # YouTube iframe
            return f'''
            <h2>Видеообзор</h2>
            <div class="video-container">
                <iframe width="560" height="315" 
                        src="https://www.youtube.com/embed/{video_id}" 
                        title="Видеообзор: {product_name}"
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                </iframe>
            </div>
            '''
        else:
            # Простая ссылка на видео
            return f'''
            <h2>Видео</h2>
            <p><a href="{video_url}" target="_blank">Смотреть видеообзор</a></p>
            '''
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Извлечение ID видео из YouTube URL
        
        Args:
            url: YouTube URL
        
        Returns:
            ID видео или None
        """
        import re
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def create_short_description(self, article_html: str, max_length: int = 200) -> str:
        """
        Создание короткого описания (для post_excerpt в WC)
        
        Args:
            article_html: HTML статья
            max_length: Максимальная длина
        
        Returns:
            Короткое текстовое описание
        """
        if not article_html:
            return ""
        
        # Убираем HTML теги
        import re
        text_only = re.sub(r'<[^>]+>', '', article_html)
        
        # Убираем лишние пробелы
        text_only = " ".join(text_only.split())
        
        # Обрезаем до максимальной длины
        if len(text_only) > max_length:
            text_only = text_only[:max_length].rsplit(' ', 1)[0] + "..."
        
        return text_only