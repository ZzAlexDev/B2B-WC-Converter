"""
Базовый класс для обработчиков B2B-WC Converter v2.0.
Все обработчики наследуются от этого класса.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from pathlib import Path

# Абсолютные импорты внутри пакета v2
from v2.models import RawProduct
from v2.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """
    Абстрактный базовый класс для всех обработчиков.
    Каждый обработчик получает сырые данные и возвращает свой фрагмент результата.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализирует обработчик.
        
        Args:
            config_manager: Менеджер конфигураций
        """
        self.config_manager = config_manager
        self.handler_name = self.__class__.__name__
        logger.debug(f"Инициализирован обработчик: {self.handler_name}")
    
    @abstractmethod
    def process(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Обрабатывает сырой продукт и возвращает фрагмент данных для WooProduct.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с обработанными данными для WooProduct
            
        Raises:
            HandlerError: Если произошла ошибка обработки
        """
        pass
    
    def handle(self, raw_product: RawProduct) -> Dict[str, Any]:
        """
        Основной метод для обработки продукта с обработкой ошибок.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            Словарь с обработанными данными или пустой словарь при ошибке
        """
        try:
            result = self.process(raw_product)
            logger.debug(f"Обработчик {self.handler_name} успешно обработал продукт {raw_product.НС_код}")
            return result
            
        except Exception as e:
            error_msg = f"Ошибка в обработчике {self.handler_name} для продукта {raw_product.НС_код}: {e}"
            logger.error(error_msg)
            
            # Если настроено пропускать ошибки, возвращаем пустой словарь
            if self.config_manager.get_setting('processing.skip_on_error', True):
                return {}
            else:
                raise HandlerError(error_msg) from e
    
    def validate_input(self, raw_product: RawProduct) -> bool:
        """
        Проверяет, достаточно ли данных для обработки этим обработчиком.
        
        Args:
            raw_product: Сырые данные продукта
            
        Returns:
            True если данных достаточно, False если обработку нужно пропустить
        """
        # Базовая реализация - всегда возвращает True
        # Наследники могут переопределить этот метод
        return True
    
    def get_required_fields(self) -> list:
        """
        Возвращает список обязательных полей для этого обработчика.
        
        Returns:
            Список имен обязательных полей
        """
        return []
    
    def log_processing_stats(self, processed: int, skipped: int) -> None:
        """
        Логирует статистику обработки.
        
        Args:
            processed: Количество успешно обработанных продуктов
            skipped: Количество пропущенных продуктов
        """
        if processed > 0 or skipped > 0:
            logger.info(f"Обработчик {self.handler_name}: обработано {processed}, пропущено {skipped}")
    
    def cleanup(self) -> None:
        """
        Выполняет очистку ресурсов после завершения обработки.
        Может быть переопределен в наследниках.
        """
        logger.debug(f"Очистка ресурсов обработчика: {self.handler_name}")


class HandlerError(Exception):
    """
    Исключение для ошибок обработчиков.
    """
    
    def __init__(self, message: str, product_sku: str = "", handler_name: str = ""):
        super().__init__(message)
        self.product_sku = product_sku
        self.handler_name = handler_name
        self.message = message
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.product_sku:
            base_msg += f" (Продукт: {self.product_sku})"
        if self.handler_name:
            base_msg += f" (Обработчик: {self.handler_name})"
        return base_msg


class HandlerContext:
    """
    Контекст для передачи данных между обработчиками.
    Может использоваться для кэширования и обмена данными.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._shared_data: Dict[str, Any] = {}
    
    def set_cache(self, key: str, value: Any) -> None:
        """Устанавливает значение в кэш."""
        self._cache[key] = value
    
    def get_cache(self, key: str, default: Any = None) -> Any:
        """Получает значение из кэша."""
        return self._cache.get(key, default)
    
    def clear_cache(self) -> None:
        """Очищает кэш."""
        self._cache.clear()
    
    def set_shared(self, key: str, value: Any) -> None:
        """Устанавливает общие данные."""
        self._shared_data[key] = value
    
    def get_shared(self, key: str, default: Any = None) -> Any:
        """Получает общие данные."""
        return self._shared_data.get(key, default)
