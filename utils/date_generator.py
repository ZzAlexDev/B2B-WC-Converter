"""
utils/date_generator.py
Генератор дат для товаров WooCommerce
"""

from datetime import datetime, timedelta


class DateGenerator:
    """
    Генератор последовательных дат для товаров
    """
    
    def __init__(self, base_date: str = "01.02.2026 12:22"):
        """
        Инициализация генератора дат
        
        Args:
            base_date: Базовая дата в формате "дд.мм.гггг чч:мм"
        """
        self.base_datetime = datetime.strptime(base_date, "%d.%m.%Y %H:%M")
        self.current_datetime = self.base_datetime
        self.product_count = 0
        
    def get_next_date(self) -> str:
        """
        Получить следующую дату с увеличением на 10 секунд
        
        Returns:
            str: Дата в формате "дд.мм.гггг чч:мм:сс"
        """
        # Для первого товара используем базовую дату
        if self.product_count == 0:
            date_str = self.base_datetime.strftime("%d.%m.%Y %H:%M")
        else:
            # Добавляем 10 секунд для каждого следующего товара
            self.current_datetime += timedelta(seconds=10)
            date_str = self.current_datetime.strftime("%d.%m.%Y %H:%M:%S")
        
        self.product_count += 1
        return date_str
    
    def reset(self):
        """Сброс генератора к начальному состоянию"""
        self.current_datetime = self.base_datetime
        self.product_count = 0


# Синглтон для использования во всем проекте
_date_generator = DateGenerator()


def get_next_product_date() -> str:
    """
    Получить следующую дату для товара
    
    Returns:
        str: Дата в формате WooCommerce
    """
    return _date_generator.get_next_date()


def reset_date_generator():
    """Сбросить генератор дат"""
    _date_generator.reset()