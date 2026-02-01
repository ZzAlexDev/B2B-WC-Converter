"""
TagsHandler - обработчик тегов для B2B-WC Converter v2.0.
Извлекает и формирует теги на основе данных продукта.
"""
import re
import logging
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from ..models import RawProduct

logger = logging.getLogger(__name__)


@dataclass
class TagCandidate:
    """Кандидат на тег с оценкой качества."""
    text: str
    source: str  # 'name', 'category', 'specs', 'description'
    score: float = 0.0
    words_count: int = 0
    has_digits: bool = False
    is_technical: bool = False


class TagsHandler:
    """
    Обработчик тегов товаров.
    Использует сложные алгоритмы для выбора лучших тегов.
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.specs_handler = None  # Будет установлен извне
        
        # Конфигурация
        self.min_tag_length = 2
        self.max_tag_length = 30
        self.min_words = 1
        self.max_words = 3
        self.max_tags_count = 15
        
        # Словари для оценки
        self._load_dictionaries()
        
        logger.info("TagsHandler инициализирован")
    
    def set_specs_handler(self, specs_handler):
        """Устанавливает SpecsHandler для парсинга характеристик."""
        self.specs_handler = specs_handler
    
    def _load_dictionaries(self):
        """Загружает словари для оценки тегов."""
        # Стоп-слова (плохие теги)
        self.stop_words = {
            'нет', 'да', 'не указано', 'не указана', 'отсутствует',
            'стандартный', 'обычный', 'базовый', 'типовой', 'общий',
            'гарантийный', 'инструкция', 'руководство', 'талон',
            'в комплекте', 'комплект поставки', 'упаковка',
            'с вилкой', 'с кабелем', 'со шнуром', 'с документацией'
        }
        
        # Технические слова (не годятся для тегов)
        self.technical_words = {
            'см', 'мм', 'м', 'кг', 'г', 'л', 'мл', 'вт', 'квт', 'в',
            'а', 'гц', 'дб', '°с', 'мин', 'сек', 'ч', 'час', 'лет',
            'об/мин', 'м/с', 'л/с', 'м³/ч', 'ккал/ч', 'бар', 'атм'
        }
        
        # Качественные слова (увеличивают оценку)
        self.quality_words = {
            'уникальный', 'инновационный', 'энергоэффективный', 'эргономичный',
            'надежный', 'долговечный', 'качественный', 'профессиональный',
            'промышленный', 'бытовой', 'коммерческий', 'дизайнерский',
            'премиум', 'люкс', 'элитный', 'современный', 'классический'
        }
        
        # Категории товаров (для контекста)
        self.product_categories = {
            'оборудование', 'техника', 'прибор', 'устройство', 'инструмент',
            'материал', 'аксессуар', 'комплектующие', 'запчасть'
        }
    
    def generate_tags(self, raw_product: RawProduct, brand: str, specs_data: Dict = None) -> str:
        """
        Генерирует теги на основе данных продукта.
        
        Args:
            raw_product: Сырой продукт
            brand: Бренд товара
            specs_data: Уже распарсенные характеристики (опционально)
            
        Returns:
            Строка тегов через разделитель "|"
        """
        logger.debug(f"Генерация тегов для: {raw_product.НС_код}")
        
        # Собираем всех кандидатов
        candidates = []
        
        # 1. Теги из названия
        name_candidates = self._extract_from_name(raw_product, brand)
        candidates.extend(name_candidates)
        
        # 2. Теги из категории
        category_candidates = self._extract_from_category(raw_product)
        candidates.extend(category_candidates)
        
        # 3. Теги из характеристик (ОСНОВНОЙ ИСТОЧНИК)
        specs_candidates = self._extract_from_specs(raw_product, specs_data)
        candidates.extend(specs_candidates)
        
        # 4. Теги из бренда
        if brand:
            brand_candidate = TagCandidate(
                text=brand,
                source='brand',
                score=8.0,  # Высокий приоритет
                words_count=len(brand.split())
            )
            candidates.append(brand_candidate)
        
        # 5. Оцениваем всех кандидатов
        scored_candidates = self._score_candidates(candidates)
        
        # 6. Выбираем лучшие теги
        best_tags = self._select_best_tags(scored_candidates)
        
        # 7. Формируем строку
        result = "|".join(best_tags)
        
        logger.debug(f"Сгенерировано тегов: {len(best_tags)}")
        return result
    
    def _extract_from_name(self, raw_product: RawProduct, brand: str) -> List[TagCandidate]:
        """Извлекает кандидатов из названия товара."""
        candidates = []
        
        if not hasattr(raw_product, 'Наименование') or not raw_product.Наименование:
            return candidates
        
        name = raw_product.Наименование.strip()
        
        # Вариант 1: Полное название (без бренда и кода)
        clean_name = self._clean_product_name(name, brand)
        if clean_name and len(clean_name) >= 4:
            candidates.append(TagCandidate(
                text=clean_name,
                source='name',
                words_count=len(clean_name.split())
            ))
        
        # Вариант 2: Ключевые словосочетания из названия
        phrases = self._extract_key_phrases(name)
        for phrase in phrases:
            candidates.append(TagCandidate(
                text=phrase,
                source='name_phrase',
                words_count=len(phrase.split())
            ))
        
        return candidates
    
    def _clean_product_name(self, name: str, brand: str) -> str:
        """Очищает название товара."""
        # Убираем бренд
        if brand and name.lower().startswith(brand.lower()):
            name = name[len(brand):].strip()
        
        # Убираем коды и артикулы в скобках в конце
        name = re.sub(r'\s*[\(\[]([^\)\]]*[A-Z0-9\-_]+[^\)\]]*)[\)\]]$', '', name)
        
        # Убираем "арт.", "код" и подобное в конце
        name = re.sub(r'\s*(арт|код|art|code|model|модель)\.?\s*[A-Z0-9\-_]+\s*$', '', name, flags=re.IGNORECASE)
        
        # Убираем разделители в начале
        name = name.lstrip(' -–—,;.')
        
        # Убираем лишние пробелы
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()

    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Извлекает ключевые словосочетания из текста."""
        phrases = []
        
        # Сначала очищаем текст от лишнего
        clean_text = self._clean_text_for_phrase_extraction(text)
        words = clean_text.split()
        
        if len(words) <= 1:
            return phrases
        
        # Список стоп-слов, которые не должны разрывать фразы
        connecting_words = {'для', 'и', 'или', 'с', 'в', 'на', 'по', 'от', 'до', 'из', 'без'}
        
        # Извлекаем словосочетания из 2-4 слов
        for i in range(len(words)):
            # Начинаем с текущего слова
            current_word = words[i].lower()
            
            # Пропускаем слишком короткие или служебные слова как начало фразы
            if len(current_word) < 2 or current_word in connecting_words:
                continue
            
            # Пробуем фразы разной длины
            for length in range(2, min(5, len(words) - i + 1)):  # от 2 до 4 слов
                phrase_words = words[i:i+length]
                phrase = ' '.join(phrase_words)
                
                # Проверяем качество фразы
                if self._is_good_phrase(phrase):
                    phrases.append(phrase)
        
        # Убираем вложенные фразы (если есть "сушилка для рук", не нужна "сушилка для")
        return self._remove_nested_phrases(phrases)

    def _clean_text_for_phrase_extraction(self, text: str) -> str:
        """Очищает текст для извлечения фраз."""
        # Убираем специальные символы, но сохраняем пробелы
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Заменяем множественные пробелы на один
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем короткие слова (1 буква)
        words = text.split()
        filtered_words = [word for word in words if len(word) > 1]
        
        return ' '.join(filtered_words)
    
    def _remove_nested_phrases(self, phrases: List[str]) -> List[str]:
        """Убирает вложенные фразы (оставляет только самые длинные)."""
        if not phrases:
            return []
        
        # Сортируем по длине (от самых длинных к самым коротким)
        phrases_sorted = sorted(phrases, key=lambda x: (-len(x.split()), x))
        
        result = []
        seen_words = set()
        
        for phrase in phrases_sorted:
            phrase_words = frozenset(phrase.lower().split())
            
            # Проверяем, не является ли эта фраза частью уже добавленной
            is_nested = False
            for seen_phrase_words in seen_words:
                if phrase_words.issubset(seen_phrase_words):
                    is_nested = True
                    break
            
            if not is_nested:
                result.append(phrase)
                seen_words.add(phrase_words)
        
        # Возвращаем в оригинальном порядке (но без вложенных)
        return [p for p in phrases if any(p_words == frozenset(p.lower().split()) for p_words in seen_words)]



    def _extract_from_category(self, raw_product: RawProduct) -> List[TagCandidate]:
        """Извлекает кандидатов из категории."""
        candidates = []
        
        if not hasattr(raw_product, 'Название_категории') or not raw_product.Название_категории:
            return candidates
        
        category = raw_product.Название_категории.strip()
        
        # Разбиваем категорию на части
        separators = [' > ', ' / ', ' | ', ' » ', ' › ', ' - ']
        
        for sep in separators:
            if sep in category:
                parts = [p.strip() for p in category.split(sep)]
                # Берем 2-3 последних уровня (самые конкретные)
                for part in parts[-3:]:
                    if part and len(part) > 2:
                        # Оцениваем качество категории
                        if not self._is_generic_category(part):
                            candidates.append(TagCandidate(
                                text=part,
                                source='category',
                                words_count=len(part.split())
                            ))
                break
        
        return candidates
    
    def _is_generic_category(self, category: str) -> bool:
        """Проверяет, является ли категория слишком общей."""
        generic = {
            'товары', 'продукция', 'оборудование', 'техника',
            'каталог', 'магазин', 'главная', 'все товары'
        }
        return category.lower() in generic
    
    def _extract_from_specs(self, raw_product: RawProduct, specs_data: Dict = None) -> List[TagCandidate]:
        """Извлекает кандидатов из характеристик."""
        candidates = []
        
        if not hasattr(raw_product, 'Характеристики') or not raw_product.Характеристики:
            return candidates
        
        # Парсим характеристики, если не переданы
        if specs_data is None and self.specs_handler:
            try:
                specs_data = self.specs_handler._parse_specifications(raw_product.Характеристики)
            except Exception as e:
                logger.error(f"Ошибка парсинга характеристик: {e}")
                return candidates
        
        if not specs_data:
            return candidates
        
        # Анализируем характеристики
        for key, value in specs_data.items():
            if not isinstance(value, str):
                continue
            
            value = value.strip()
            if not value:
                continue
            
            # Оцениваем пару ключ-значение
            candidate = self._evaluate_spec_pair(key, value)
            if candidate:
                candidates.append(candidate)
        
        return candidates
    
    def _evaluate_spec_pair(self, key: str, value: str) -> TagCandidate:
        """Оценивает пару характеристика-значение для тега."""
        key_lower = key.lower()
        value_lower = value.lower()
        
        # Быстрая проверка: точно не тег
        if self._is_bad_value(value_lower):
            return None
        
        # Проверяем, является ли техническим параметром
        is_technical = self._is_technical_spec(key_lower, value)
        
        # Подсчитываем слова
        words = value.split()
        words_count = len(words)
        
        # Проверяем длину
        if len(value) < self.min_tag_length or len(value) > self.max_tag_length:
            return None
        
        # Проверяем количество слов
        if words_count < self.min_words or words_count > self.max_words:
            return None
        
        # Проверяем наличие цифр
        has_digits = any(char.isdigit() for char in value)
        
        # Базовая оценка
        score = 5.0  # Средняя
        
        # Корректировки оценки
        if has_digits:
            score -= 2.0  # Цифры снижают оценку
        
        if is_technical:
            score -= 3.0  # Технические параметры сильно снижают оценку
        
        # Ключевые характеристики повышают оценку
        if self._is_key_specification(key_lower):
            score += 3.0
        
        # Качественные слова повышают оценку
        for quality_word in self.quality_words:
            if quality_word in value_lower:
                score += 2.0
                break
        
        # Слишком низкая оценка - пропускаем
        if score < 3.0:
            return None
        
        # Создаем кандидата
        return TagCandidate(
            text=value,
            source='specs',
            score=score,
            words_count=words_count,
            has_digits=has_digits,
            is_technical=is_technical
        )
    
    def _is_bad_value(self, value: str) -> bool:
        """Проверяет, является ли значение плохим кандидатом."""
        # Стоп-слова
        if value in self.stop_words:
            return True
        
        # Слишком короткие
        if len(value) < 2:
            return True
        
        # Только цифры
        if value.isdigit():
            return True
        
        # Единицы измерения
        if any(unit in value for unit in self.technical_words):
            return True
        
        return False
    
    def _is_technical_spec(self, key: str, value: str) -> bool:
        """Проверяет, является ли характеристика технической."""
        technical_keys = {
            'напряжение', 'мощность', 'ток', 'частота', 'размер',
            'вес', 'габариты', 'объем', 'скорость', 'давление',
            'расход', 'температура', 'шум', 'влажность'
        }
        
        # Проверяем ключ
        if any(tech_key in key for tech_key in technical_keys):
            return True
        
        # Проверяем значение на технические паттерны
        technical_patterns = [
            r'\d+\s*[-–—]\s*\d+',  # Диапазоны
            r'\d+[\.,]\d+',  # Дробные числа
            r'\d+\s*[xх×]\s*\d+',  # Размеры
            r'[<>≤≥≈±~]',  # Математические символы
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, value):
                return True
        
        return False
    
    def _is_key_specification(self, key: str) -> bool:
        """Проверяет, является ли характеристика ключевой."""
        key_specs = {
            'цвет', 'материал', 'отделка', 'дизайн', 'форма',
            'тип', 'вид', 'назначение', 'категория',
            'управление', 'регулировка', 'контроль',
            'установка', 'монтаж', 'расположение',
            'защита', 'класс защиты', 'степень защиты',
            'страна', 'производство', 'гарантия',
            'особенность', 'функция', 'режим', 'технология'
        }
        
        return any(key_spec in key for key_spec in key_specs)
    
    def _is_good_phrase(self, phrase: str) -> bool:
        """Проверяет, является ли фраза хорошей для тега."""
        phrase_lower = phrase.lower()
        
        # Длина
        if len(phrase) < 4 or len(phrase) > 30:
            return False
        
        words = phrase_lower.split()
        
        # Не должно быть обрывков фраз
        if len(words) == 1:
            return False
        
        # Проверяем, чтобы не было "оборванных" фраз типа "для рук"
        if words[0] in {'для', 'и', 'или', 'с', 'без', 'в', 'на', 'по'}:
            return False
        
        # Проверяем, чтобы не было "оборванных" фраз в конце
        if words[-1] in {'для', 'и', 'или', 'с', 'без', 'в', 'на', 'по', 'от', 'до'}:
            return False

        # Слишком общие фразы
        common_phrases = {
            'высокое качество', 'низкая цена', 'удобное использование',
            'простота монтажа', 'легкая установка', 'быстрый монтаж'
        }
        
        if phrase_lower in common_phrases:
            return False
        
        # Не должно быть много служебных слов
        stop_words = {'для', 'и', 'или', 'с', 'без', 'в', 'на', 'по', 'от', 'до'}
        words = phrase_lower.split()
        stop_count = sum(1 for word in words if word in stop_words)
        
        if stop_count > 1:
            return False
        
        # Не должно быть только технических терминов
        tech_count = sum(1 for word in words if word in self.technical_words)
        if tech_count == len(words):
            return False
        
        return True
    
    def _score_candidates(self, candidates: List[TagCandidate]) -> List[TagCandidate]:
        """Оценивает всех кандидатов и возвращает отсортированный список."""
        if not candidates:
            return []
        
        scored = []
        
        for candidate in candidates:
            # Базовая оценка
            final_score = candidate.score
            
            # Корректировки на основе источника
            if candidate.source == 'name':
                final_score += 4.0  # Название - самый важный
            elif candidate.source == 'brand':
                final_score += 3.0  # Бренд - очень важный
            elif candidate.source == 'category':
                final_score += 2.0  # Категория - важный
            elif candidate.source == 'name_phrase':
                final_score += 1.5  # Фразы из названия
            
            # Корректировка на количество слов
            if candidate.words_count == 2:
                final_score += 1.0  # Идеальное количество
            elif candidate.words_count == 3:
                final_score += 0.5  # Хорошо, но длинновато
            
            # Корректировка на наличие цифр
            if candidate.has_digits:
                final_score -= 1.5  # Цифры обычно не нужны в тегах
            
            # Корректировка на техничность
            if candidate.is_technical:
                final_score -= 2.0  # Технические параметры редко хороши как теги
            
            # Обновляем оценку
            candidate.score = max(0.0, final_score)  # Не ниже 0
            scored.append(candidate)
        
        # Сортируем по оценке (убывание)
        scored.sort(key=lambda x: x.score, reverse=True)
        
        return scored
    
    def _select_best_tags(self, candidates: List[TagCandidate]) -> List[str]:
        """Выбирает лучшие теги из кандидатов."""
        if not candidates:
            return []
        
        selected = []
        selected_texts = set()
        
        for candidate in candidates:
            if len(selected) >= self.max_tags_count:
                break
            
            # Проверяем, не дублирует ли уже выбранные
            candidate_lower = candidate.text.lower()
            is_duplicate = False
            
            for selected_text in selected_texts:
                # Простая проверка на дубли
                if (candidate_lower == selected_text.lower() or
                    candidate_lower in selected_text.lower() or
                    selected_text.lower() in candidate_lower):
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue
            
            # Добавляем
            selected.append(candidate.text)
            selected_texts.add(candidate.text)
        
        return selected
    
    def cleanup(self):
        """Очистка ресурсов."""
        logger.debug("TagsHandler: ресурсы очищены")