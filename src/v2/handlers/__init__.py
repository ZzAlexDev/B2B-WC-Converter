"""
Пакет обработчиков для B2B-WC Converter v2.0
"""

__all__ = [
    'BaseHandler',
    'ProcessingResult',
    'MediaHandler',
    'ContentHandler',
    'FileHandler',
    'TextHandler',
    'MessageHandler',
    'TagsHandler',
    'CoreHandler',
    'SpecsHandler',  
]

# Сначала импортируем только базовые классы
try:
    from .base_handler import BaseHandler
    from .base_handler import ProcessingResult
except ImportError as e:
    print(f"❌ Ошибка импорта base_handler: {e}")
    # Создаем заглушки
    class ProcessingResult:
        def __init__(self, success=False, data=None, error=None, metadata=None):
            self.success = success
            self.data = data
            self.error = error
            self.metadata = metadata
    
    class BaseHandler:
        def __init__(self, config_manager=None):
            self.config_manager = config_manager

# Затем другие обработчики
try:
    from .media_handler import MediaHandler
    from .content_handler import ContentHandler
    from .tags_handler import TagsHandler
    
    # CoreHandler - проверяем существование
    try:
        from .core_handler import CoreHandler
    except ImportError:
        # Если нет core_handler.py, создаем заглушку
        print("⚠️ CoreHandler не найден, создаем заглушку")
        class CoreHandler(BaseHandler):
            """Заглушка для CoreHandler"""
            def __init__(self, config_manager=None):
                super().__init__(config_manager)
            
            def process(self, *args, **kwargs):
                return ProcessingResult(success=False, error="CoreHandler not implemented")
            
            def validate(self, *args, **kwargs):
                return False
        
        CoreHandler = CoreHandler
    
    # SpecsHandler - проверяем существование
    try:
        from .specs_handler import SpecsHandler
    except ImportError:
        # Если нет specs_handler.py, создаем заглушку
        print("⚠️ SpecsHandler не найден, создаем заглушку")
        class SpecsHandler(BaseHandler):
            """Заглушка для SpecsHandler"""
            def __init__(self, config_manager=None):
                super().__init__(config_manager)
            
            def process(self, *args, **kwargs):
                return ProcessingResult(success=False, error="SpecsHandler not implemented")
            
            def validate(self, *args, **kwargs):
                return False
        
        SpecsHandler = SpecsHandler
    
    # Другие обработчики (если нужны)
    try:
        from .file_handler import FileHandler
    except ImportError:
        print("⚠️ FileHandler не найден, создаем заглушку")
        class FileHandler(BaseHandler):
            def __init__(self, config_manager=None):
                super().__init__(config_manager)
        FileHandler = FileHandler
    
    try:
        from .text_handler import TextHandler
    except ImportError:
        print("⚠️ TextHandler не найден, создаем заглушку")
        class TextHandler(BaseHandler):
            def __init__(self, config_manager=None):
                super().__init__(config_manager)
        TextHandler = TextHandler
    
    try:
        from .message_handler import MessageHandler
    except ImportError:
        print("⚠️ MessageHandler не найден, создаем заглушку")
        class MessageHandler(BaseHandler):
            def __init__(self, config_manager=None):
                super().__init__(config_manager)
        MessageHandler = MessageHandler
    
except ImportError as e:
    print(f"⚠️ Ошибка импорта обработчиков: {e}")
    # Создаем заглушки для всех
    MediaHandler = BaseHandler
    ContentHandler = BaseHandler
    TagsHandler = BaseHandler
    CoreHandler = BaseHandler
    SpecsHandler = BaseHandler
    FileHandler = BaseHandler
    TextHandler = BaseHandler
    MessageHandler = BaseHandler