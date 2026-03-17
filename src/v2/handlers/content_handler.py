"""
ContentHandler - обработчик контента для B2B-WC Converter v2.0.
"""
import re
import sys
import json
import time
import random
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from urllib.parse import urlparse

# Пробуем импортировать
try:
    # Вариант 1: относительный импорт
    from .base_handler import BaseHandler
    from ..models import RawProduct
    from ..config_manager import ConfigManager
    from ..utils import (
        get_logger,
        extract_youtube_id,
        normalize_yes_no,
        parse_specifications
    )
except ImportError as e:
    print(f"❌ Ошибка импорта в ContentHandler (вариант 1): {e}")
    try:
        # Вариант 2: абсолютный импорт
        from src.v2.handlers.base_handler import BaseHandler
        from src.v2.models import RawProduct
        from src.v2.config_manager import ConfigManager
        from src.v2.utils import (
            get_logger,
            extract_youtube_id,
            normalize_yes_no,
            parse_specifications
        )
    except ImportError as e:
        print(f"❌ Ошибка импорта в ContentHandler (вариант 2): {e}")
        # Вариант 3: добавляем путь и импортируем напрямую
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent
        
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from src.v2.handlers.base_handler import BaseHandler
        from src.v2.models import RawProduct
        from src.v2.config_manager import ConfigManager
        from src.v2.utils import (
            get_logger,
            extract_youtube_id,
            normalize_yes_no,
            parse_specifications
        )

logger = get_logger(__name__)
load_dotenv()

# Если parse_specifications всё равно не найдена, создайте локальную версию
if 'parse_specifications' not in globals():
    print("⚠️ parse_specifications не найдена, создаём локальную версию")
    
    def parse_specifications(specs_string: str) -> Dict[str, str]:
        """Локальная версия парсера спецификаций"""
        if not specs_string or not specs_string.strip():
            return {}
        
        result = {}
        try:
            # Разные варианты разделителей
            if ';' in specs_string:
                pairs = specs_string.split(';')
            elif ',' in specs_string:
                pairs = specs_string.split(',')
            else:
                pairs = [specs_string]
            
            for pair in pairs:
                pair = pair.strip()
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    result[key.strip()] = value.strip()
                elif '=' in pair:
                    key, value = pair.split('=', 1)
                    result[key.strip()] = value.strip()
        except Exception as e:
            logger.warning(f"Ошибка парсинга спецификаций: {e}")
        
        return result

# Если normalize_yes_no не найдена
if 'normalize_yes_no' not in globals():
    print("⚠️ normalize_yes_no не найдена, создаём локальную версию")
    
    def normalize_yes_no(value: str) -> str:
        """Локальная версия нормализации Да/Нет"""
        if not value:
            return ""
        
        value_lower = value.lower().strip()
        if value_lower in ['да', 'yes', 'true', '1']:
            return "Да"
        elif value_lower in ['нет', 'no', 'false', '0']:
            return "Нет"
        else:
            return value

# Если extract_youtube_id не найдена
if 'extract_youtube_id' not in globals():
    print("⚠️ extract_youtube_id не найдена, создаём локальную версию")
    
    def extract_youtube_id(url: str) -> Optional[str]:
        """Локальная версия извлечения YouTube ID"""
        if not url:
            return None
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
            r'(?:v=)([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None


class DeepSeekGenerator:
    """Генератор SEO-текстов через DeepSeek API"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        self.model = os.getenv('DEEPSEEK_MODEL', 'stepfun/step-3.5-flash:free')
        self.temperature = float(os.getenv('SEO_AI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('SEO_AI_MAX_TOKENS', '2000'))  # Увеличили для 4 текстов
        self.enabled = os.getenv('SEO_AI_ENABLED', 'false').lower() == 'true'
        self.timeout = int(os.getenv('SEO_AI_TIMEOUT', '60'))
        self.max_retries = int(os.getenv('SEO_AI_MAX_RETRIES', '5'))
        self.base_delay = int(os.getenv('SEO_AI_BASE_DELAY', '2'))
        
        # ⭐ ЗАГРУЗКА ПРОМТА ИЗ .ENV
        self.prompt_template = os.getenv('SEO_PROMPT_TEMPLATE', self._get_default_prompt())
        
        # Флаги управления
        self.generate_enabled = os.getenv('SEO_GENERATE_ENABLED', 'true').lower() == 'true'
        self.update_intro = os.getenv('SEO_UPDATE_INTRO', 'true').lower() == 'true'
        self.update_outro = os.getenv('SEO_UPDATE_OUTRO', 'true').lower() == 'true'
        self.update_b2b = os.getenv('SEO_UPDATE_B2B', 'true').lower() == 'true'
        self.update_excerpt = os.getenv('SEO_UPDATE_EXCERPT', 'true').lower() == 'true'
        self.skip_if_min_length = os.getenv('SEO_SKIP_IF_MIN_LENGTH', 'true').lower() == 'true'
        self.min_intro_length = int(os.getenv('SEO_MIN_INTRO_LENGTH', '400'))
        self.min_outro_length = int(os.getenv('SEO_MIN_OUTRO_LENGTH', '180'))
        self.min_b2b_length = int(os.getenv('SEO_MIN_B2B_LENGTH', '300'))
        self.min_excerpt_length = int(os.getenv('SEO_MIN_EXCERPT_LENGTH', '150'))
        self.force_regenerate = os.getenv('SEO_FORCE_REGENERATE', 'false').lower() == 'true'
        
        if self.enabled and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            print(f"✅ AI инициализирован (модель: {self.model})")
            print(f"📝 Промт загружен из .env, длина: {len(self.prompt_template)} символов")
            print(f"🎯 Режим: {'ПРИНУДИТЕЛЬНЫЙ' if self.force_regenerate else 'УМНЫЙ'}")
        else:
            self.client = None
            if self.enabled:
                print("⚠️ AI отключен: нет API ключа")
    
    def _get_default_prompt(self) -> str:
        """Возвращает промт по умолчанию, если в .env ничего нет"""
        return """
        Напиши ЧЕТЫРЕ текста для товара: EXCERPT, INTRO, B2B-блок и OUTRO.
        
        ДАННЫЕ О ТОВАРЕ:
        - Название: {product_name}
        - Бренд: {brand}
        - Категория: {category}
        
        КЛЮЧЕВЫЕ ХАРАКТЕРИСТИКИ:
        {specs_text}
        
        ТРЕБОВАНИЯ К EXCERPT (КРАТКОЕ ОПИСАНИЕ ДЛЯ КАТАЛОГА):
        - Длина: 150-200 символов
        - Обязательно использовать мощность и площадь из характеристик
        - Упомянуть, что подходит для бизнеса
        - Формат: просто текст, БЕЗ тегов
        
        ТРЕБОВАНИЯ К INTRO (ВСТУПЛЕНИЕ):
        - Длина: 450-550 символов (ОДИН абзац)
        - Стиль: деловой, информативный
        - Использовать 3-4 ключевые характеристики
        - Акцент на надежности и эффективности для бизнеса
        
        ТРЕБОВАНИЯ К B2B-БЛОКУ:
        - Заголовок H3: для офисов, гостиниц и госучреждений
        - Длина: 300-400 символов + список из 5 пунктов
        - Структура: вводный текст + список + призыв
        - Пункты списка должны опираться на характеристики
        
        ТРЕБОВАНИЯ К OUTRO:
        - Длина: 150-200 символов
        - Формат: заголовок H3 + 1 абзац
        - Заголовок: вопрос о сотрудничестве
        - Текст: призыв запросить КП или консультацию
        
        ОТВЕТ ДАЙ В СТРОГОМ ФОРМАТЕ:
        EXCERPT: [текст]
        
        INTRO: [текст]
        
        B2B:
        <h3>[заголовок]</h3>
        <div class="b2b-block">
        <p>[вводный текст]</p>
        <ul>
        <li>[пункт 1]</li>
        <li>[пункт 2]</li>
        <li>[пункт 3]</li>
        <li>[пункт 4]</li>
        <li>[пункт 5]</li>
        </ul>
        <p class="b2b-cta">[призыв]</p>
        </div>
        
        OUTRO:
        <h3>[заголовок]</h3>
        <p>[текст]</p>
        """
    
    def generate_all(self, product_name: str, brand: str = "", category: str = "", specs_text: str = "") -> tuple[str, str, str, str]:
        """
        Генерирует все четыре текста: excerpt, intro, b2b, outro
        Возвращает (excerpt, intro, b2b, outro)
        """
        if not self.client:
            return "", "", "", ""
        
        # Базовая задержка перед запросом
        time.sleep(random.uniform(0.5, 1.5))
        
        # Формируем промт с подстановкой данных
        prompt = self.prompt_template.format(
            product_name=product_name,
            brand=brand if brand else "не указан",
            category=category if category else "не указана",
            specs_text=specs_text if specs_text else "нет данных"
        )
        
        print(f"\n{'='*60}")
        print(f"🤖 ГЕНЕРАЦИЯ ТЕКСТОВ ДЛЯ ТОВАРА:")
        print(f"📦 {product_name}")
        print(f"🏷️ Бренд: {brand if brand else 'не указан'}")
        print(f"📊 Категория: {category if category else 'не указана'}")
        print(f"{'='*60}")
        
        # Расширенный список моделей для fallback (оставляем ваш)
        fallback_models = [
            self.model,
            "stepfun/step-3.5-flash:free",
            "deepseek/deepseek-r1-0528:free",
            # ... остальные модели из вашего списка
        ]
        
        for model in fallback_models:
            for attempt in range(self.max_retries):
                try:
                    print(f"\n🔄 Пробую модель: {model} (попытка {attempt+1}/{self.max_retries})")
                    
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Ты SEO-копирайтер для B2B. Пиши деловым стилем. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать любые языки, кроме русского. Если нужно написать 'свяжитесь с нами' — пиши ТОЛЬКО по-русски. НИКАКИХ китайских, японских, корейских и других иероглифов. ВЕСЬ ОТВЕТ ТОЛЬКО НА РУССКОМ."},
                            {"role": "user", "content": prompt}
                            ],


                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        timeout=self.timeout
                    )
                    
                    text = response.choices[0].message.content.strip()
                    
                    print(f"\n📥 СЫРОЙ ОТВЕТ AI:")
                    print(f"{text if text else '⚠️ ПУСТОЙ ОТВЕТ'}")
                    print(f"\n{'─'*40}")
                    
                    if not text:
                        print("⚠️ AI вернул пустой ответ, пробую снова...")
                        continue
                    
                    # Парсим ответ
                    excerpt = self._extract_part(text, "EXCERPT:")
                    intro = self._extract_part(text, "INTRO:")
                    b2b = self._extract_part(text, "B2B:")
                    outro = self._extract_part(text, "OUTRO:")
                    
                    # Проверка на обрыв
                    def is_truncated(text: str) -> bool:
                        if not text:
                            return False
                        # Убираем HTML теги для проверки
                        clean_text = re.sub(r'<[^>]+>', '', text)
                        if not clean_text:
                            return False
                        last_char = clean_text.strip()[-1]
                        return last_char not in '.!?…'
                    
                    if excerpt and is_truncated(excerpt):
                        print(f"⚠️ Excerpt оборван, добавляю '...'")
                        excerpt = excerpt.rstrip() + "…"
                    
                    if intro and is_truncated(intro):
                        print(f"⚠️ Intro оборван, добавляю '...'")
                        intro = intro.rstrip() + "…"
                    
                    if b2b and is_truncated(b2b):
                        print(f"⚠️ B2B блок оборван, добавляю '...'")
                        b2b = b2b.rstrip() + "…"
                    
                    if outro and is_truncated(outro):
                        print(f"⚠️ Outro оборван, добавляю '...'")
                        outro = outro.rstrip() + "…"

                    # Проверка на иероглифы
                    if excerpt and not self._contains_only_russian(excerpt):
                        print(f"⚠️ EXCERPT содержит иероглифы, заменяю на заглушку")
                        excerpt = "Профессиональное оборудование для бизнеса. Подходит для офисов и госучреждений."

                    if intro and not self._contains_only_russian(intro):
                        print(f"⚠️ INTRO содержит иероглифы, заменяю на заглушку")
                        intro = "Надежное решение для отопления коммерческих помещений. Оборудование отличается высокой эффективностью и длительным сроком службы."

                    
                    # Вывод результатов
                    print(f"\n{'*'*10} РЕЗУЛЬТАТЫ {'*'*10}")
                    print(f"📌 EXCERPT: {excerpt[:100]}..." if excerpt else "❌ EXCERPT не получен")
                    print(f"📌 INTRO: {intro[:100]}..." if intro else "❌ INTRO не получен")
                    print(f"📌 B2B: {'получен' if b2b else 'не получен'}")
                    print(f"📌 OUTRO: {outro[:100]}..." if outro else "❌ OUTRO не получен")
                    print(f"{'*'*30}\n")
                    
                    if excerpt and intro and b2b and outro:
                        return excerpt, intro, b2b, outro
                    else:
                        print("⚠️ Не все тексты получены, пробую снова...")
                        continue
                    
                except Exception as e:
                    if "429" in str(e):
                        wait_time = (self.base_delay ** attempt) + random.uniform(0, 1)
                        print(f"⚠️ Модель {model} перегружена, жду {wait_time:.1f}с...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ Ошибка с моделью {model}: {e}")
                        break
        
        print("⚠️ Не удалось получить ответ от AI")
        return "", "", "", ""
    
    def _extract_part(self, text: str, marker: str) -> str:
        """Извлекает часть ответа по маркеру"""
        if marker not in text:
            return ""
        
        parts = text.split(marker)
        if len(parts) < 2:
            return ""
        
        result = parts[1].strip()
        
        # Ищем следующий маркер
        next_markers = ["EXCERPT:", "INTRO:", "B2B:", "OUTRO:"]
        for next_marker in next_markers:
            if next_marker != marker and next_marker in result:
                result = result.split(next_marker)[0].strip()
                break
        
        return result
    
    # Для обратной совместимости
    def generate_both(self, product_name: str, brand: str = "") -> tuple[str, str]:
        """Старый метод для совместимости"""
        excerpt, intro, b2b, outro = self.generate_all(product_name, brand)
        return intro, outro
    
    def generate_intro(self, product_name: str, brand: str = "") -> str:
        excerpt, intro, b2b, outro = self.generate_all(product_name, brand)
        return intro
    
    def generate_outro(self, product_name: str, brand: str = "") -> str:
        excerpt, intro, b2b, outro = self.generate_all(product_name, brand)
        return outro

    def _contains_only_russian(self, text: str) -> bool:
        """
        Проверяет, содержит ли текст допустимые символы для русского языка.
        """
        if not text:
            return True
        
        # Убираем HTML теги для проверки
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Разрешаем:
        # - русские буквы (включая ё)
        # - латиницу (может быть в брендах)
        # - цифры
        # - пробелы и переносы строк
        # - стандартные знаки препинания . , ! ? : ; ( )
        # - спецсимволы для русского языка: — – « » ° №
        # - знак валюты ₽
        allowed_pattern = re.compile(
            r'^[а-яА-ЯёЁa-zA-Z0-9\s\.,!?\-—–«»:;°№₽\(\)\n\r]+$'
        )
        
        # Проверяем
        if not allowed_pattern.match(clean_text):
            # Если не прошло проверку, покажем проблемные символы для отладки
            bad_chars = set()
            for char in clean_text:
                if not allowed_pattern.match(char):
                    bad_chars.add(char)
            if bad_chars:
                print(f"⚠️ Найдены неподдерживаемые символы: {bad_chars}")
            return False
        
        return True




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

        # 4. Исправляем битые теги
        html = html.replace('</\x01>', '</ul>')
        html = re.sub(r'</p>\s*<br\s*/?\s*>\s*<h', '</p>\n<h', html, flags=re.IGNORECASE)
        html = re.sub(r'<h([1-6])[^>]*>(.*?)</h\[1-6\]>', r'<h\1>\2</h\1>', html, flags=re.IGNORECASE)
        html = re.sub(r'<ul>\s*<br\s*/?\s*>', '<ul>\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</li>\s*<br\s*/?\s*>\s*<li>', '</li>\n<li>', html, flags=re.IGNORECASE)
        
        # 5. Исправляем двойные кавычки в class
        html = re.sub(r'class=""([^""]+)""', r'class="\1"', html)

        # 6. Финальная чистка
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
        
        # ⭐ Инициализируем AI генератор
        try:
            self.ai_generator = DeepSeekGenerator()
            print(f"🤖 AI-генератор: {'ВКЛЮЧЕН' if self.ai_generator.enabled else 'ВЫКЛЮЧЕН'}")
            
            # Если AI отключен, предупреждаем
            if not self.ai_generator.enabled:
                print("⚠️ AI генератор отключен в .env (SEO_AI_ENABLED=false)")
                
        except Exception as e:
            print(f"⚠️ Ошибка инициализации AI-генератора: {e}")
            self.ai_generator = None
    
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
        html_content, excerpt = self._build_html_content(raw_product, specs, article_html)
        
        # ⭐ Сохраняем excerpt в raw_product для CoreHandler
        if excerpt:
            raw_product._ai_excerpt = excerpt
            print(f"✅ AI- excerpt сохранен в raw_product: {excerpt[:50]}...")
        
        # 3. Сохраняем результаты
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

            # ЗАМЕНЯЕМ | на / в КЛЮЧЕ и ЗНАЧЕНИИ
            clean_key = clean_key.replace('|', '/')
            clean_value = clean_value.replace('|', '/')
            
            if clean_key and clean_value:
                normalized_value = normalize_yes_no(clean_value)
                normalized_specs[clean_key] = normalized_value
        
        self.specs_cache[cache_key] = normalized_specs.copy()
        return normalized_specs
    
    def _build_html_content(self, raw_product: RawProduct, specs: Dict[str, str], article_html: str) -> Tuple[str, Optional[str]]:
        """
        Собирает HTML контент из различных источников.
        Возвращает (html, excerpt)
        """
        html_parts = []

        # ⭐ ДОБАВЛЯЕМ H2 ЗАГОЛОВОК
        h2_title = self._get_h2_title_from_category(raw_product)
        html_parts.append(f'<h2>{h2_title}</h2>')
        html_parts.append('')  # Пустая строка для отступа
        
        # ⭐ ПОЛУЧАЕМ ВСЕ 4 ТЕКСТА ОДНИМ ЗАПРОСОМ
        excerpt = None
        intro = None
        b2b = None
        outro = None
        
        if hasattr(self, 'ai_generator') and self.ai_generator and self.ai_generator.enabled:
            # Формируем текст характеристик для промта
            specs_text = self._format_specs_for_prompt(specs)
            
            # Получаем категорию
            category = self._get_category(raw_product)
            
            # ОДИН запрос на ВСЕ тексты!
            excerpt, intro, b2b, outro = self.ai_generator.generate_all(
                product_name=raw_product.Наименование or "",
                brand=raw_product.Бренд or "",
                category=category,
                specs_text=specs_text
            )
            
            print(f"\n🔍 ОТЛАДКА _build_html_content:")
            print(f"   EXCERPT получен: {excerpt[:50] if excerpt else 'None'}...")
            print(f"   INTRO получен: {intro[:50] if intro else 'None'}...")
            print(f"   B2B получен: {'да' if b2b else 'нет'}")
            print(f"   OUTRO получен: {outro[:50] if outro else 'None'}...")
        
        # AI уже сгенерировал все тексты выше
        # Если AI не сработал, просто логируем это - шаблонов больше нет
        if not intro:
            print("⚠️ INTRO не сгенерирован AI, страница будет без вступления")

        if not outro:
            print("⚠️ OUTRO не сгенерирован AI, страница будет без заключения")

        # Для excerpt и b2b аналогично - они уже получены от AI

        
        # Для excerpt и b2b шаблонов пока нет, но можно добавить позже
        
        # ⭐ EXCERPT - НЕ добавляем в HTML! Он пойдет в отдельное поле
        # Сохраняем в результат для woocommerce
        if excerpt:
            print(f"✅ EXCERPT сохранен для WooCommerce (длина: {len(excerpt)})")

        
        # Вставляем intro в начало (ЕСЛИ ОН ЕСТЬ)
        if intro:
            html_parts.append(intro)
            html_parts.append('')
            print(f"✅ INTRO добавлен в html_parts")
        
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
        
        # ⭐ B2B-БЛОК (вставляем перед outro)
        if b2b:
            html_parts.append('')
            html_parts.append(b2b)
            print(f"✅ B2B-блок добавлен в html_parts")
        
        # Вставляем outro в конец
        if outro:
            html_parts.append('')
            html_parts.append(outro)
            print(f"✅ OUTRO добавлен в html_parts")
        
        # Объединяем все блоки
        full_html = "\n\n".join(html_parts)
        
        # 🚨 ПРОВЕРКА ФИНАЛЬНОГО HTML
        print(f"\n🔍 ФИНАЛЬНЫЙ HTML (первые 600 символов):")
        print(full_html[:600])
        print("="*80)
        
        # ФИНАЛЬНЫЙ РЕМОНТ всего HTML
        return self.html_repair.repair(full_html), excerpt

    def _format_specs_for_prompt(self, specs: Dict[str, str]) -> str:
        """Форматирует характеристики для вставки в промт"""
        important_fields = [
            "Макс. тепловая мощность", "Мощность", 
            "Площадь обогрева", "Эффективен для помещ. площадью до",
            "Количество секций", "Вид управления",
            "Защита от перегрева", "Автоматическое отключение",
            "Срок службы", "Материал корпуса",
            "Класс пылевлагозащищенности", "Тип нагревательного элемента"
        ]
        
        lines = []
        for field in important_fields:
            if field in specs:
                lines.append(f"- {field}: {specs[field]}")
        
        return "\n".join(lines) if lines else "нет данных"

    def _get_category(self, raw_product: RawProduct) -> str:
        """Определяет категорию товара"""
        # Пробуем получить из атрибутов
        if hasattr(raw_product, 'Категория') and raw_product.Категория:
            return raw_product.Категория
        
        # Или из названия
        name = raw_product.Наименование or ""
        if "радиатор" in name.lower():
            return "отопительное оборудование"
        elif "сушилка" in name.lower():
            return "сантехническое оборудование"
        elif "пушка" in name.lower():
            return "тепловое оборудование"
        
        return "бытовая техника"

    def _set_excerpt_for_product(self, product_id: str, excerpt: str):
        """Сохраняет excerpt для WooCommerce"""
        # Здесь нужно добавить логику сохранения в результат
        # Например, через self.result["excerpt"] = excerpt
        # Но это должно быть в process(), а не здесь
        pass

    def _get_random_region_phrase(self) -> str:
        """
        Возвращает случайную фразу с регионом.
        """
        regions = [
            "в Сибири",
            "в Кузбассе",
            "в Кемерово",
            "в Кемеровской области"
        ]
        return random.choice(regions)

    def _parse_category(self, category_string: str) -> str:
        """
        Парсит строку категории, возвращает последний сегмент с очисткой.
        
        Пример: "Тепловое оборудование - Сушилки для рук - Сушилки для рук" 
        → "Сушилки для рук"
        """
        if not category_string:
            return ""
        
        # Разбиваем по дефису и берем последнюю часть
        parts = [p.strip() for p in category_string.split('-')]
        last_part = parts[-1] if parts else ""
        
        # Убираем возможные дублирования (если последняя часть совпадает с предпоследней)
        if len(parts) >= 2 and last_part == parts[-2]:
            # Уже нормально, оставляем как есть
            pass
        
        return last_part

    def _get_h2_title_from_category(self, raw_product: RawProduct) -> str:
        """
        Генерирует H2 заголовок на основе категории, бренда и случайного региона.
        """
        category_string = getattr(raw_product, 'Категория', '')
        brand = getattr(raw_product, 'Бренд', '').strip()
        product_name = getattr(raw_product, 'Наименование', '').lower()
        
        # Парсим категорию - берем последний сегмент
        clean_category = self._parse_category(category_string)
        category_lower = clean_category.lower() if clean_category else ""
        
        # Если категория пустая — пробуем из названия
        if not category_lower:
            if "сушилк" in product_name or "рукосушилк" in product_name:
                category_lower = "сушилки для рук"
            elif "пушк" in product_name:
                category_lower = "тепловые пушки"
            # ... остальные условия ...
        
        # Выбираем случайный регион
        region_phrase = self._get_random_region_phrase()
        
        # Базовая часть заголовка
        base_title = ""
        
        # Теперь проверяем очищенную категорию
        if "сушилки для рук" in category_lower:
            base_title = "Профессиональные сушилки для рук"
        elif "маслонаполненные радиаторы" in category_lower or "радиаторы" in category_lower:
            base_title = "Маслонаполненные радиаторы"
        elif "тепловые пушки" in category_lower:
            if "газовые" in category_lower:
                base_title = "Газовые тепловые пушки"
            elif "дизельные" in category_lower:
                base_title = "Дизельные тепловые пушки"
            elif "электрические" in category_lower:
                base_title = "Электрические тепловые пушки"
            else:
                base_title = "Промышленные тепловые пушки"
        elif "электрические конвекторы" in category_lower or "конвекторы" in category_lower:
            base_title = "Электрические конвекторы"
        elif "тепловые завесы" in category_lower or "воздушные завесы" in category_lower:
            if "интерьерные" in category_lower:
                base_title = "Интерьерные воздушные завесы"
            elif "коммерческие" in category_lower:
                base_title = "Коммерческие тепловые завесы"
            elif "промышленные" in category_lower:
                base_title = "Промышленные воздушные завесы"
            else:
                base_title = "Воздушные и тепловые завесы"
        elif "инфракрасные" in category_lower:
            if "газовые" in category_lower:
                base_title = "Газовые инфракрасные обогреватели"
            else:
                base_title = "Электрические инфракрасные обогреватели"
        elif "камины" in category_lower:
            if "биокамины" in category_lower:
                base_title = "Биокамины"
            elif "электрические" in category_lower:
                base_title = "Электрические камины"
            else:
                base_title = "Камины"
        elif "водяные" in category_lower:
            if "тепловентиляторы" in category_lower:
                base_title = "Водяные тепловентиляторы"
            elif "дестратификаторы" in category_lower:
                base_title = "Дестратификаторы"
            else:
                base_title = "Водяное отопительное оборудование"
        elif "термостаты" in category_lower:
            base_title = "Защитные термостаты"
        else:
            # Если ничего не подошло — используем очищенную категорию
            if clean_category:
                base_title = clean_category
            elif brand:
                return f"Профессиональное оборудование {brand} для бизнеса {region_phrase}"
            else:
                return f"Профессиональное оборудование для бизнеса {region_phrase}"
        
        # Добавляем бренд (если есть)
        if brand and brand.lower() not in base_title.lower():
            base_title = f"{base_title} {brand}"
        
        # Формируем финальный заголовок
        return f"{base_title} для бизнеса {region_phrase}"
    
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
            # Сначала ремонтируем
            clean_key = self.html_repair.repair(key)
            clean_value = self.html_repair.repair(value)
            
            # ПОТОМ убираем HTML теги
            clean_key = re.sub(r'<[^>]+>', '', clean_key)
            clean_value = re.sub(r'<[^>]+>', '', clean_value)
            
            # И только ОДИН РАЗ добавляем
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
                html_parts.append(f'<h4>{doc_type.capitalize()}</h4>')
                
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