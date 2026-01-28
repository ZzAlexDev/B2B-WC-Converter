"""
data_processors/description_builder.py
Генератор полного описания товара для WooCommerce
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import urlparse
import os

# Настройка логгера
logger = logging.getLogger(__name__)


class DescriptionBuilder:
    """
    Класс для сборки полного описания товара
    """
    
    def __init__(self):
        """
        Инициализация генератора описаний
        """
        # Загружаем настройки
        self._load_settings()
        
        # Инициализируем парсер характеристик
        try:
            from data_processors.attribute_parser import AttributeParser
            self.attribute_parser = AttributeParser()
        except ImportError:
            logger.error("Не удалось импортировать AttributeParser")
            self.attribute_parser = None
        
        self.stats = {
            'descriptions_built': 0,
            'total_length': 0,
            'errors': []
        }
        
        logger.info("Инициализирован генератор описаний")
    
    def _load_settings(self):
        """
        Загрузка настроек из конфигурации
        """
        try:
            from config import settings
            
            # Настройки путей
            self.icons_path = settings.ICONS_PATH
            self.file_icons = settings.FILE_ICONS
            self.file_type_texts = settings.FILE_TYPE_TEXTS
            
            logger.debug("Настройки загружены успешно")
            
        except ImportError as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            # Значения по умолчанию
            self.icons_path = "/wp-content/uploads/icons/"
            self.file_icons = {}
            self.file_type_texts = {}
    
    def clean_html_description(self, html_content: str) -> str:
        """
        Очистка и валидация HTML описания
        
        Args:
            html_content: Исходный HTML
            
        Returns:
            str: Очищенный HTML
        """
        if not html_content:
            return ""
        
        try:
            # Удаляем лишние пробелы и переносы строк
            cleaned = html_content.strip()
            
            # Заменяем множественные переносы строк на одинарные
            cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
            
            # Удаляем лишние пробелы в начале строк
            cleaned = re.sub(r'^\s+', '', cleaned, flags=re.MULTILINE)
            
            # Проверяем на наличие HTML тегов
            if '<' not in cleaned or '>' not in cleaned:
                # Если нет HTML тегов, оборачиваем в параграф
                cleaned = f'<p>{cleaned}</p>'
            
            # Заменяем <br> на <br /> для XHTML совместимости
            cleaned = cleaned.replace('<br>', '<br />')
            
            logger.debug(f"HTML очищен: {len(cleaned)} символов")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Ошибка очистки HTML: {e}")
            return html_content
    
    def extract_excerpt(self, html_content: str, max_length: int = 200) -> str:
        """
        Создание краткого описания (excerpt) из полного
        
        Args:
            html_content: Полное описание
            max_length: Максимальная длина excerpt
            
        Returns:
            str: Краткое описание
        """
        if not html_content:
            return ""
        
        try:
            # Удаляем HTML теги
            text_only = re.sub(r'<[^>]+>', ' ', html_content)
            
            # Удаляем лишние пробелы
            text_only = ' '.join(text_only.split())
            
            # Обрезаем до максимальной длины
            if len(text_only) > max_length:
                # Обрезаем до последнего полного слова
                truncated = text_only[:max_length]
                last_space = truncated.rfind(' ')
                if last_space > max_length * 0.7:  # Если есть разумное место для обрезания
                    text_only = truncated[:last_space] + '...'
                else:
                    text_only = truncated + '...'
            
            logger.debug(f"Excerpt создан: {len(text_only)} символов")
            
            return text_only
            
        except Exception as e:
            logger.error(f"Ошибка создания excerpt: {e}")
            return ""
    
    # В методе build_characteristics_section:
    def build_characteristics_section(self, characteristics_str: str) -> str:
        """
        Создание секции технических характеристик
        
        Args:
            characteristics_str: Строка характеристик
            
        Returns:
            str: HTML секция характеристик
        """
        if not characteristics_str or not self.attribute_parser:
            return ""
        
        try:
            # ИСПРАВЛЕНИЕ: используем format_for_description
            html = self.attribute_parser.format_for_description(characteristics_str)
            
            if html:
                logger.debug(f"Секция характеристик создана: {len(html)} символов")
            
            return html
            
        except Exception as e:
            logger.error(f"Ошибка создания секции характеристик: {e}")
            return ""
    
    def parse_document_links(self, documents_str: str) -> List[Dict[str, str]]:
        """
        Парсинг строки с документами (URL через запятую)
        
        Args:
            documents_str: Строка с URL документов
            
        Returns:
            List[Dict[str, str]]: Список документов с метаданными
        """
        if not documents_str:
            return []
        
        documents = []
        
        try:
            # Разделяем URL
            urls = [url.strip() for url in documents_str.split(',') if url.strip()]
            
            for url in urls:
                # Получаем расширение файла
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                name, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                # Определяем тип файла
                icon = self.file_icons.get(ext, 'document-icon.png')
                file_type = self.file_type_texts.get(ext, '')
                
                # Создаем читаемое название
                readable_name = self._create_readable_filename(name)
                
                documents.append({
                    'url': url,
                    'filename': filename,
                    'extension': ext,
                    'icon': icon,
                    'file_type': file_type,
                    'readable_name': readable_name
                })
            
            logger.debug(f"Парсинг документов: найдено {len(documents)}")
            
        except Exception as e:
            logger.error(f"Ошибка парсинга документов: {e}")
        
        return documents
    
    def _create_readable_filename(self, filename: str, doc_type: str = "", product_name: str = "") -> str:
        """
        Создание читаемого имени файла
        
        Args:
            filename: Исходное имя файла
            doc_type: Тип документа (Чертежи, Инструкции и т.д.)
            product_name: Название товара для включения в имя документа
            
        Returns:
            str: Читаемое имя
        """
        # Базовое название по типу документа
        base_name = self._get_default_doc_name(doc_type)
        
        # Если есть название товара - добавляем его
        if product_name:
            # Очищаем название товара для использования в имени файла
            clean_product_name = self._clean_product_name_for_docs(product_name)
            return f"{base_name} {clean_product_name}"
        
        return base_name

    def _clean_product_name_for_docs(self, product_name: str) -> str:
        """
        Очистка названия товара для использования в именах документов
        
        Args:
            product_name: Название товара
            
        Returns:
            str: Очищенное название
        """
        if not product_name:
            return ""
        
        clean = product_name.strip()
        
        # 1. Заменяем / на - (как в SKU)
        clean = clean.replace('/', '-')
        
        # 2. Удаляем специальные символы, но сохраняем дефисы и пробелы
        # Разрешаем: буквы (включая кириллицу), цифры, пробелы, дефисы
        clean = re.sub(r'[^\w\s\-]', ' ', clean, flags=re.UNICODE)
        
        # 3. Заменяем множественные пробелы на одинарные
        clean = re.sub(r'\s+', ' ', clean)
        
        # 4. Удаляем пробелы в начале и конце
        clean = clean.strip()
        
        # 5. Ограничиваем длину (60 символов - разумный предел)
        if len(clean) > 60:
            truncated = clean[:60]
            # Пытаемся обрезать до последнего пробела
            last_space = truncated.rfind(' ')
            if last_space > 40:  # Если есть разумное место для обрезания
                clean = truncated[:last_space]
            else:
                clean = truncated
        
        return clean

    def _get_default_doc_name(self, doc_type: str) -> str:
        """
        Получение стандартного имени документа по типу
        
        Args:
            doc_type: Тип документа
            
        Returns:
            str: Стандартное имя
        """
        defaults = {
            'Чертежи': 'Чертеж',
            'Инструкции': 'Инструкция',
            'Сертификаты': 'Сертификат',
            'Промоматериалы': 'Промо-материал',
            'Видео': 'Видео',
            '': 'Документ',
        }
        
        return defaults.get(doc_type, 'Документ')
    
    def build_documents_section(self, documents_data: Dict[str, str], product_name: str = "") -> str:
        """
        Создание секции документации
        
        Args:
            documents_data: Словарь с документами по типам
            product_name: Название товара для имен документов
            
        Returns:
            str: HTML секция документации
        """
        if not documents_data:
            return ""
        
        html_parts = []
        html_parts.append('<h3>Документация</h3>')
        
        try:
            # Типы документов и их отображаемые названия
            doc_type_display = {
                'Чертежи': 'Чертежи и схемы',
                'Сертификаты': 'Сертификаты',
                'Инструкции': 'Инструкции по эксплуатации',
                'Промоматериалы': 'Промо-материалы',
                'Видео': 'Видеоматериалы',
            }
            
            # Обрабатываем каждый тип документов
            for doc_type, doc_urls in documents_data.items():
                if not doc_urls:
                    continue
                
                # Парсим URL
                documents = self.parse_document_links(doc_urls)
                
                if documents:
                    # Добавляем подзаголовок для типа документа
                    display_name = doc_type_display.get(doc_type, doc_type)
                    html_parts.append(f'<h4>{display_name}</h4>')
                    html_parts.append('<ul>')
                    
                    for doc in documents:
                        # Создаем название с именем товара
                        doc_name = self._create_readable_filename(
                            doc['filename'], 
                            doc_type, 
                            product_name
                        )
                        
                        # Определяем расширение для текста типа файла
                        file_type_text = self.file_type_texts.get(doc['extension'], '')
                        
                        # Формируем полное название
                        link_text = f'{doc_name}{file_type_text}'
                        
                        html_parts.append(
                            f'<li>'
                            f'<img src="{self.icons_path}{doc["icon"]}" width="32" height="32" alt="{doc["extension"][1:].upper()}" style="vertical-align: middle; margin-right: 8px;">'
                            f'<a href="{doc["url"]}" target="_blank" rel="noopener noreferrer">{link_text}</a>'
                            f'</li>'
                        )
                    
                    html_parts.append('</ul>')
            
            html = '\n'.join(html_parts)
            
            if len(html_parts) > 1:  # Если есть больше чем просто заголовок
                logger.debug(f"Секция документации создана: {len(html)} символов")
                return html
            else:
                return ""
            
        except Exception as e:
            logger.error(f"Ошибка создания секции документации: {e}")
            return ""
            
        except Exception as e:
            logger.error(f"Ошибка создания секции документации: {e}")
            return ""
    
    def build_additional_info_section(self, additional_info: Dict[str, str]) -> str:
        """
        Создание секции дополнительной информации
        
        Args:
            additional_info: Словарь с дополнительной информацией
            
        Returns:
            str: HTML секция с дополнительной информацией
        """
        if not additional_info:
            return ""
        
        html_parts = []
        
        try:
            # Информация о кодах товара
            if 'НС-код' in additional_info and additional_info['НС-код']:
                ns_code = additional_info['НС-код']
                html_parts.append(f'<p><strong>Код товара:</strong> {ns_code}</p>')
            
            # Штрих-коды
            if 'Штрих код' in additional_info and additional_info['Штрих код']:
                barcodes = additional_info['Штрих код']
                # Разделяем несколько штрих-кодов (разделитель может быть "/" или пробел+"/"+пробел)
                barcode_list = [code.strip() for code in re.split(r'\s*/\s*', barcodes) if code.strip()]
                
                if barcode_list:
                    # Форматируем через запятую
                    formatted_barcodes = ', '.join(barcode_list)
                    html_parts.append(f'<p><strong>Штрих-коды:</strong> {formatted_barcodes}</p>')
            
            # Эксклюзивность
            if 'Эксклюзив' in additional_info and additional_info['Эксклюзив']:
                exclusive = additional_info['Эксклюзив']
                if exclusive.lower() == 'да':
                    html_parts.append('<p><strong>Эксклюзивный товар</strong></p>')
            
            html = '\n'.join(html_parts)
            
            if html:
                logger.debug(f"Секция доп. информации создана: {len(html)} символов")
            
            return html
            
        except Exception as e:
            logger.error(f"Ошибка создания секции доп. информации: {e}")
            return ""
    
    def build_full_description(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Сборка полного описания товара
        
        Args:
            product_data: Данные товара из парсера XLSX
            
        Returns:
            Dict[str, str]: Полное описание и excerpt
        """
        result = {
            'post_content': '',
            'post_excerpt': '',
            'wc_attributes': {},
            'extracted_fields': {}
        }
        
        try:
            product_name = product_data.get('name', '')
            
            # 1. Основное описание
            main_description = self.clean_html_description(
                product_data.get('description_raw', '')
            )
            
            # 2. Технические характеристики
            characteristics_section = self.build_characteristics_section(
                product_data.get('characteristics_raw', '')
            )
            
            # 3. Документация (передаем название товара)
            documents_section = self.build_documents_section(
                product_data.get('documents', {}),
                product_name
            )
            
            # 4. Дополнительная информация
            additional_info_section = self.build_additional_info_section(
                product_data.get('additional_info', {})
            )
            
            # 5. Собираем все части
            description_parts = []
            
            if main_description:
                description_parts.append(main_description)
            
            if characteristics_section:
                description_parts.append(characteristics_section)
            
            if documents_section:
                description_parts.append(documents_section)
            
            if additional_info_section:
                description_parts.append(additional_info_section)
            
            # Объединяем все части
            full_description = '\n\n'.join(description_parts)
            
            # 6. Создаем краткое описание
            excerpt = self.extract_excerpt(full_description)
            
            # 7. Извлекаем атрибуты WC и поля
            if self.attribute_parser:
                # Атрибуты WooCommerce
                wc_attrs = self.attribute_parser.extract_wc_attributes(
                    product_data.get('characteristics_raw', '')
                )
                result['wc_attributes'] = wc_attrs
                
                # Конкретные поля (вес, габариты)
                extracted = self.attribute_parser.extract_specific_fields(
                    product_data.get('characteristics_raw', '')
                )
                result['extracted_fields'] = extracted
            
            # Сохраняем результаты
            result['post_content'] = full_description
            result['post_excerpt'] = excerpt
            
            # Статистика
            self.stats['descriptions_built'] += 1
            self.stats['total_length'] += len(full_description)
            
            logger.debug(f"Описание построено: {len(full_description)} символов, excerpt: {len(excerpt)} символов")
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка сборки описания для товара {product_data.get('sku', 'N/A')}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            
            # Возвращаем хотя бы основное описание
            result['post_content'] = self.clean_html_description(
                product_data.get('description_raw', '')
            )
            result['post_excerpt'] = self.extract_excerpt(result['post_content'])
            
            return result
    
    def process_batch(self, products_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обработка партии товаров
        
        Args:
            products_data: Список данных товаров
            
        Returns:
            List[Dict[str, Any]]: Товары с добавленными описаниями
        """
        processed_products = []
        
        logger.info(f"Начало обработки {len(products_data)} товаров")
        
        for i, product_data in enumerate(products_data, 1):
            try:
                # Собираем описание
                description_result = self.build_full_description(product_data)
                
                # Добавляем результаты к данным товара
                enhanced_product = product_data.copy()
                enhanced_product.update({
                    'post_content': description_result['post_content'],
                    'post_excerpt': description_result['post_excerpt'],
                    'wc_attributes': description_result['wc_attributes'],
                    'extracted_fields': description_result['extracted_fields']
                })
                
                processed_products.append(enhanced_product)
                
                if i % 10 == 0:
                    logger.info(f"Обработано {i}/{len(products_data)} товаров")
                
            except Exception as e:
                error_msg = f"Ошибка обработки товара {i}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
        
        logger.info(f"Обработка завершена: {len(processed_products)} успешно, ошибок: {len(self.stats['errors'])}")
        
        return processed_products
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики
        
        Returns:
            Dict[str, Any]: Статистика обработки
        """
        avg_length = self.stats['total_length'] / self.stats['descriptions_built'] if self.stats['descriptions_built'] > 0 else 0
        
        return {
            **self.stats,
            'average_length': round(avg_length, 1)
        }


# Функции для быстрого использования
def build_product_description(product_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Быстрая сборка описания товара
    
    Args:
        product_data: Данные товара
        
    Returns:
        Dict[str, str]: Описание и excerpt
    """
    builder = DescriptionBuilder()
    return builder.build_full_description(product_data)


def process_products_descriptions(products_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Быстрая обработка партии товаров
    
    Args:
        products_data: Список данных товаров
        
    Returns:
        List[Dict[str, Any]]: Обработанные товары
    """
    builder = DescriptionBuilder()
    return builder.process_batch(products_data)