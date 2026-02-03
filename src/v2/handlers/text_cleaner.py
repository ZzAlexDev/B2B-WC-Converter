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
        
        
        # 1. СНАЧАЛА заменяем HTML-сущности (самое важное!)
        # Ищем &ndash в ЛЮБОМ виде, даже с необычными пробелами
        text = re.sub(r'&(\s*|\u202F|\u2007|\u2060)?ndash(\s*|\u202F|\u2007|\u2060)?', '-', text)
        text = re.sub(r'&(\s*|\u202F|\u2007|\u2060)?bull(\s*|\u202F|\u2007|\u2060)?', '•', text)
        text = re.sub(r'&(\s*|\u202F|\u2007|\u2060)?deg(\s*|\u202F|\u2007|\u2060)?', '°', text)
        
        # 2. Только ПОТОМ убираем специальные пробелы
        text = text.replace('\u202F', ' ')  # Narrow no-break space
        text = text.replace('\u2007', ' ')  # Figure space  
        text = text.replace('\u2060', ' ')  # Word joiner
        
        # 3. Обычные неразрывные пробелы
        text = text.replace('&nbsp;', ' ')
        text = text.replace('\xa0', ' ')
       
        
        # 4. Убираем множественные пробелы
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
