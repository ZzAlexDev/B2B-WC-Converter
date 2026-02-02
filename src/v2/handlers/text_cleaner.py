"""
TextCleaner - минимальный очиститель только для неразрывных пробелов.
"""
import re

class TextCleaner:
    """Очищает только неразрывные пробелы, оставляя HTML нетронутым."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Убирает только неразрывные пробелы, сохраняя весь HTML.
        
        Args:
            text: Исходный текст
            
        Returns:
            Текст без &nbsp; и \xa0
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Только заменяем неразрывные пробелы на обычные
        # 1. HTML entity &nbsp;
        text = text.replace('&nbsp;', ' ')
        
        # 2. Unicode non-breaking space \xa0
        text = text.replace('\xa0', ' ')
        
        # 3. Другие варианты неразрывных пробелов (редкие)
        text = text.replace('\u202F', ' ')  # Narrow no-break space
        text = text.replace('\u2007', ' ')  # Figure space
        text = text.replace('\u2060', ' ')  # Word joiner
        
        # Убираем множественные пробелы (но не внутри тегов!)
        # Простой способ: заменяем "  " на " ", но не в атрибутах тегов
        text = re.sub(r'(?<=>|\s)\s{2,}(?=\s|<)', ' ', text)
        
        return text
    
    @staticmethod
    def clean_for_content(text: str) -> str:
        """Для полного описания - только убираем неразрывные пробелы."""
        return TextCleaner.clean_text(text)
    
    @staticmethod 
    def clean_for_excerpt(text: str, max_length: int = 160) -> str:
        """
        Для краткого описания - убираем HTML теги И неразрывные пробелы.
        """
        if not text:
            return ""
        
        # 1. Убираем неразрывные пробелы
        text = TextCleaner.clean_text(text)
        
        # 2. Удаляем HTML теги (для excerpt)
        text = re.sub(r'<[^>]+>', '', text)
        
        # 3. Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 4. Обрезаем до нужной длины
        if len(text) > max_length:
            text = text[:max_length - 3] + '...'
        
        return text