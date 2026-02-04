# test_ftp_naming.py
import sys
sys.path.insert(0, "src")

def test_naming():
    print("🔍 Тест именования файлов:")
    print("="*50)
    
    # Пример из вашего кода
    ns_code = "ns-1632905"
    slug = "pushka-dizelnaya-pryamogo-nagreva-ballu-bhdp-20l"
    
    for i in range(3):  # 0, 1, 2
        # Текущий (неправильный)
        current_ftp = f"{ns_code}-{slug}-{i}.webp"
        
        # Исправленный
        fixed_ftp = f"{ns_code}-{slug}-{i+1}.webp"
        
        # URL (как должно быть)
        url = f"https://сайт.ru/uploads/{ns_code}-{slug}-{i+1}.webp"
        
        print(f"Изображение {i}:")
        print(f"  Было (FTP): {current_ftp} ← НЕПРАВИЛЬНО")
        print(f"  Стало (FTP): {fixed_ftp}")
        print(f"  URL: {url}")
        print(f"  Совпадает? {'✅' if fixed_ftp in url else '❌'}")
        print()

if __name__ == "__main__":
    test_naming()