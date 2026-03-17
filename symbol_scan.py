import re

def show_words_with_glyphs(filepath):
    """Выводит слова, содержащие иероглифы, построчно"""
    glyph_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Разбиваем на слова (по пробелам и знакам препинания)
        words = re.findall(r'\b\w+\b', content)
        
        print(f"📌 Слова с иероглифами в файле {filepath}:")
        print("-" * 40)
        
        found = False
        for word in words:
            if glyph_pattern.search(word):
                print(f"   {word}")
                found = True
        
        if not found:
            print("   ❌ Слова с иероглифами не найдены")
            
    except FileNotFoundError:
        print(f"❌ Файл не найден: {filepath}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


# Проверяем ваш файл
show_words_with_glyphs('./data/output/converted_20260317_001017.csv')