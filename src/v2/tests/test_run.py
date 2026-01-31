"""
Тестовый скрипт для проверки работы конвертера
"""
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / "src"))

from v2.converter import ConverterV2


def create_test_csv():
    """Создаем тестовый CSV файл."""
    test_data = """Наименование;Артикул;НС-код;Бренд;Название категории;Характеристики;Изображение;Видео;Статья;Чертежи;Сертификаты;Промоматериалы;Инструкции;Штрих код;Цена;Эксклюзив
Пластиковый контейнер 10л;PC-10;NS001;PlasticPro;Тара - Контейнеры;Масса товара (нетто): 0.5 кг / Высота товара: 30 см / Ширина товара: 20 см / Глубина товара: 15 см / Область применения: Хранение / Цвет корпуса: Белый / Страна производства: Россия;https://example.com/image1.jpg,https://example.com/image2.jpg;https://youtube.com/watch?v=dQw4w9WgXcQ;<p>Отличный контейнер для хранения</p>;https://example.com/drawing.pdf;https://example.com/certificate.pdf;;https://example.com/instructions.pdf;1234567890123/2345678901234;"14990 руб.";"Эксклюзив - Нет"
Металлический шкаф;MS-200;NS002;MetalWorks;Мебель - Шкафы - Офисные;Масса товара (нетто): 15 кг / Высота товара: 180 см / Ширина товара: 60 см / Глубина товара: 40 см / Область применения: Офис / Цвет корпуса: Серый / Гарантийный срок: 2 года;https://example.com/cabinet.jpg;;<p>Прочный металлический шкаф</p>;;;;;9876543210987;"24500 руб.";"Эксклюзив - Да"
"""
    
    input_path = Path("data/input/test_products.csv")
    input_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path, "w", encoding="utf-8") as f:
        f.write(test_data)
    
    return input_path


def main():
    """Тестируем конвертер."""
    print("Создаем тестовый CSV файл...")
    input_path = create_test_csv()
    
    print(f"Файл создан: {input_path}")
    
    try:
        # Инициализируем конвертер
        converter = ConverterV2(config_path="config/v2")
        
        # Запускаем конвертацию
        result = converter.convert(
            input_path=input_path,
            output_path="data/output/test_output.csv",
            skip_errors=True
        )
        
        print(f"\n✅ Тест пройден успешно!")
        print(f"Результат: {result}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()