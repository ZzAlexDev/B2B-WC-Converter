"""
Парсер для обработки документов (5 колонок)
Видео, Чертежи, Сертификаты, Промоматериалы, Инструкции
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

from .base_parser import BaseParser, ParseResult
from src.utils.logger import log_info, log_warning


class DocsParser(BaseParser):
    """
    Парсер для обработки документов
    
    Обрабатывает 5 колонок:
    1. Видео (Video)
    2. Чертежи (Drawings) 
    3. Сертификаты (Certificates)
    4. Промоматериалы (Promo)
    5. Инструкции (Manuals)
    """
    
    # Соответствие колонок типам документов
    COLUMN_MAPPING = {
        "Видео": "video",
        "Чертежи": "drawing", 
        "Сертификаты": "certificate",
        "Промоматериалы": "promo",
        "Инструкции": "manual"
    }
    
    # Иконки для каждого типа (из вашего .env)
    ICON_URLS = {
        "video": "https://kvanta42.ru/wp-content/uploads/2026/02/video-icon.png",
        "drawing": "https://kvanta42.ru/wp-content/uploads/2026/02/drawing-icon.png",
        "certificate": "https://kvanta42.ru/wp-content/uploads/2026/02/certificate-icon.png", 
        "promo": "https://kvanta42.ru/wp-content/uploads/2026/02/promo-icon.png",
        "manual": "https://kvanta42.ru/wp-content/uploads/2026/02/manual-icon.png"
    }
    
    # Русские названия для заголовков
    TYPE_NAMES = {
        "video": "Видео",
        "drawing": "Чертежи",
        "certificate": "Сертификаты", 
        "promo": "Промоматериалы",
        "manual": "Инструкции"
    }
    
    # Форматы файлов для определения типа
    FILE_EXTENSIONS = {
        ".pdf": "PDF",
        ".doc": "DOC",
        ".docx": "DOCX",
        ".xls": "XLS", 
        ".xlsx": "XLSX",
        ".jpg": "JPG",
        ".jpeg": "JPG",
        ".png": "PNG",
        ".mp4": "MP4",
        ".avi": "AVI",
        ".mov": "MOV"
    }
    
    def __init__(self):
        """Инициализация парсера документов"""
        super().__init__(column_name="Документы")
    
    def parse_all_documents(
        self,
        videos: str = "",
        drawings: str = "", 
        certificates: str = "",
        promo: str = "",
        manuals: str = "",
        product_name: str = "",
        product_type: str = ""
    ) -> ParseResult:
        """
        Парсинг всех типов документов
        
        Args:
            videos: Строка с URL видео (через запятую)
            drawings: Строка с URL чертежей (через запятую)
            certificates: Строка с URL сертификатов (через запятую)
            promo: Строка с URL промоматериалов (через запятую)
            manuals: Строка с URL инструкций (через запятую)
            product_name: Название товара (для именования документов)
            product_type: Тип товара (для именования документов)
        
        Returns:
            ParseResult с HTML документами
        """
        errors = []
        warnings = []
        
        # Собираем все документы в словарь
        all_docs = {
            "video": self.clean_value(videos),
            "drawing": self.clean_value(drawings),
            "certificate": self.clean_value(certificates),
            "promo": self.clean_value(promo),
            "manual": self.clean_value(manuals)
        }
        
        try:
            # Обрабатываем каждый тип документов
            processed_docs = {}
            total_links = 0
            
            for doc_type, doc_string in all_docs.items():
                if doc_string:
                    # Парсим строку с документами
                    urls = self._parse_doc_string(doc_string)
                    
                    if urls:
                        # Генерируем HTML для этого типа документов
                        html = self._generate_docs_html(
                            urls=urls,
                            doc_type=doc_type,
                            product_name=product_name,
                            product_type=product_type
                        )
                        
                        processed_docs[doc_type] = {
                            "urls": urls,
                            "html": html,
                            "count": len(urls)
                        }
                        total_links += len(urls)
                    
                    log_info(f"Обработано {len(urls)} документов типа '{doc_type}'")
            
            # Генерируем полный HTML блок
            full_html = self._generate_full_html_block(processed_docs)
            
            # Собираем статистику
            doc_stats = {
                doc_type: data.get("count", 0) 
                for doc_type, data in processed_docs.items()
            }
            
            # Подготовка данных
            data = {
                "all_docs": processed_docs,  # Все документы по типам
                "full_html": full_html,      # Полный HTML блок
                "stats": doc_stats,          # Статистика по типам
                "total_links": total_links,  # Всего ссылок
                "has_documents": total_links > 0
            }
            
            # Логирование
            if total_links == 0:
                warnings.append("Нет документов для обработки")
            else:
                log_info(f"Обработано всего документов: {total_links}")
            
            return self.create_result(
                data=data,
                original_value=f"Видео: {videos[:50]}..., Чертежи: {drawings[:50]}...",
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Ошибка при обработке документов: {str(e)}")
            return self.create_result(
                data={"all_docs": {}, "full_html": "", "error": str(e)},
                original_value="",
                errors=errors,
                warnings=warnings
            )
    
    def _parse_doc_string(self, doc_string: str) -> List[str]:
        """
        Разбор строки с документами (URL через запятую)
        
        Args:
            doc_string: Строка с URL через запятую
        
        Returns:
            Список очищенных URL
        """
        if not doc_string:
            return []
        
        # Разделяем по запятой
        urls = [url.strip() for url in doc_string.split(',') if url.strip()]
        
        # Фильтруем валидные URL
        valid_urls = []
        for url in urls:
            if self._is_valid_url(url):
                valid_urls.append(url)
            else:
                log_warning(f"Невалидный URL документа: {url}")
        
        return valid_urls
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Проверка валидности URL
        
        Args:
            url: URL для проверки
        
        Returns:
            True если URL валидный
        """
        if not url:
            return False
        
        # Проверяем что это HTTP/HTTPS URL
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Проверяем парсинг URL
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _generate_docs_html(
        self, 
        urls: List[str], 
        doc_type: str,
        product_name: str,
        product_type: str
    ) -> str:
        """
        Генерация HTML для одного типа документов
        
        Args:
            urls: Список URL документов
            doc_type: Тип документа (video, drawing, certificate, promo, manual)
            product_name: Название товара
            product_type: Тип товара
        
        Returns:
            HTML код
        """
        if not urls:
            return ""
        
        # Получаем иконку и название типа
        icon_url = self.ICON_URLS.get(doc_type, "")
        type_name = self.TYPE_NAMES.get(doc_type, doc_type)
        
        # Генерируем ссылки
        links_html = []
        for i, url in enumerate(urls):
            # Определяем тип файла
            file_type = self._get_file_type(url)
            
            # Генерируем название документа
            doc_name = self._generate_doc_name(
                doc_type=doc_type,
                product_name=product_name,
                product_type=product_type,
                file_type=file_type,
                index=i
            )
            
            # Генерируем HTML ссылку
            link_html = self._generate_link_html(
                url=url,
                icon_url=icon_url,
                doc_name=doc_name,
                doc_type=doc_type
            )
            
            links_html.append(link_html)
        
        # Собираем полный HTML для этого типа
        return f'''
        <h4>{type_name}</h4>
        {"".join(links_html)}
        '''
    
    def _get_file_type(self, url: str) -> str:
        """
        Определение типа файла по URL
        
        Args:
            url: URL файла
        
        Returns:
            Тип файла (PDF, DOCX, JPG и т.д.)
        """
        # Извлекаем расширение
        path = urlparse(url).path
        _, ext = path.rsplit('.', 1) if '.' in path else ('', '')
        
        ext = f".{ext.lower()}" if ext else ""
        return self.FILE_EXTENSIONS.get(ext, "Файл")
    
    def _generate_doc_name(
        self,
        doc_type: str,
        product_name: str,
        product_type: str,
        file_type: str,
        index: int
    ) -> str:
        """
        Генерация названия документа
        
        Args:
            doc_type: Тип документа
            product_name: Название товара
            product_type: Тип товара
            file_type: Тип файла
            index: Индекс документа
        
        Returns:
            Название документа
        """
        # Русские названия для типов
        type_names_ru = {
            "video": "Видеообзор",
            "drawing": "Чертеж", 
            "certificate": "Сертификат",
            "promo": "Промо",
            "manual": "Инструкция"
        }
        
        doc_name_ru = type_names_ru.get(doc_type, "Документ")
        
        # Если несколько документов одного типа - добавляем номер
        if index > 0:
            doc_name_ru = f"{doc_name_ru} {index + 1}"
        
        # Формируем полное название
        # Берем первые 3 слова из названия товара чтобы не было слишком длинно
        name_parts = product_name.split()[:3]
        short_name = " ".join(name_parts)
        
        return f"{doc_name_ru} {short_name} ({file_type})"
    
    def _generate_link_html(
        self,
        url: str,
        icon_url: str,
        doc_name: str,
        doc_type: str
    ) -> str:
        """
        Генерация HTML ссылки на документ
        
        Args:
            url: URL документа
            icon_url: URL иконки
            doc_name: Название документа
            doc_type: Тип документа
        
        Returns:
            HTML код ссылки
        """
        # Для видео - специальная обработка
        if doc_type == "video" and "youtube.com" in url or "youtu.be" in url:
            # Извлекаем ID видео для YouTube
            video_id = self._extract_youtube_id(url)
            if video_id:
                # Создаем iframe для видео
                return f'''
                <div class="video-document">
                    <iframe width="560" height="315" 
                            src="https://www.youtube.com/embed/{video_id}" 
                            title="{doc_name}"
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                    </iframe>
                    <p><a href="{url}" target="_blank" rel="noopener noreferrer">{doc_name}</a></p>
                </div>
                '''
        
        # Обычная ссылка с иконкой
        return f'''
        <a href="{url}" target="_blank" rel="noopener noreferrer">
            <img style="vertical-align: middle; margin-right: 8px;" 
                 src="{icon_url}" 
                 alt="{doc_type}" width="32" height="32" />
            {doc_name}
        </a><br>
        '''

    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Извлечение ID видео из YouTube URL
        
        Args:
            url: YouTube URL
        
        Returns:
            ID видео или None
        """
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
    
    def _generate_full_html_block(self, processed_docs: Dict[str, Any]) -> str:
        """
        Генерация полного HTML блока со всеми документами
        
        Args:
            processed_docs: Обработанные документы по типам
        
        Returns:
            Полный HTML блок
        """
        if not processed_docs:
            return ""
        
        # Собираем HTML для каждого типа который есть
        docs_html_parts = []
        
        # Порядок вывода (как в шаблоне)
        output_order = ["certificate", "manual", "drawing", "promo", "video"]
        
        for doc_type in output_order:
            if doc_type in processed_docs and processed_docs[doc_type]["html"]:
                docs_html_parts.append(processed_docs[doc_type]["html"])
        
        if docs_html_parts:
            return f'''
            <h3>Документация</h3>
            {"".join(docs_html_parts)}
            '''
        
        return ""
    
    def parse_single_column(
        self,
        doc_string: str,
        column_name: str,
        product_name: str = "",
        product_type: str = ""
    ) -> ParseResult:
        """
        Парсинг одной колонки документов
        
        Args:
            doc_string: Строка с документами
            column_name: Название колонки (Видео, Чертежи и т.д.)
            product_name: Название товара
            product_type: Тип товара
        
        Returns:
            ParseResult для одной колонки
        """
        # Определяем тип документа по названию колонки
        doc_type = self.COLUMN_MAPPING.get(column_name, "")
        
        if not doc_type:
            return self.create_result(
                data={"html": "", "urls": []},
                original_value=doc_string,
                errors=[f"Неизвестный тип колонки: {column_name}"],
                warnings=[]
            )
        
        # Парсим строку
        urls = self._parse_doc_string(doc_string)
        
        if not urls:
            return self.create_result(
                data={"html": "", "urls": []},
                original_value=doc_string,
                errors=[],
                warnings=[f"Нет документов в колонке {column_name}"]
            )
        
        # Генерируем HTML
        html = self._generate_docs_html(
            urls=urls,
            doc_type=doc_type,
            product_name=product_name,
            product_type=product_type
        )
        
        data = {
            "urls": urls,
            "html": html,
            "doc_type": doc_type,
            "count": len(urls)
        }
        
        return self.create_result(
            data=data,
            original_value=doc_string,
            errors=[],
            warnings=[]
        )
    
    def parse(self, value: str) -> ParseResult:
        """
        Реализация абстрактного метода parse из BaseParser
        (для обратной совместимости, но используем parse_all_documents)
        
        Args:
            value: Значение из колонки (не используется напрямую)
        
        Returns:
            ParseResult с пустыми данными
        """
        return self.create_result(
            data={
                "message": "Используйте parse_all_documents() для обработки документов",
                "has_documents": False
            },
            original_value=value,
            errors=["Используйте parse_all_documents() вместо parse()"],
            warnings=[]
        )    