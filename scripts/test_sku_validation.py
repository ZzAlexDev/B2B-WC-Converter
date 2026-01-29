"""
Тест валидации SKU с разными форматами
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.validators import validate_sku


def test_sku_validation():
    """Тестирование различных форматов SKU"""
    print("🧪 Тестирование валидации SKU...")
    
    test_cases = [
        # (SKU, должен_пройти_валидацию, описание)
        ("BIH-GSW-0.8 + BMT-1", True, "С пробелами и плюсом"),
        ("BHG-20М", True, "С кириллицей"),
        ("RTHD-1100 White", True, "С пробелом и английскими буквами"),
        ("NS-1183726", True, "Стандартный НС-код"),
        ("ART-001/2023", True, "Со слэшем"),
        ("BHC-U15A-PS", True, "С дефисами"),
        ("<script>alert()</script>", False, "Опасные символы"),
        ("", False, "Пустая строка"),
        ("A", False, "Слишком короткий"),
        ("A" * 150, False, "Слишком длинный"),
        ("Test.SKU_123", True, "С точкой и подчеркиванием"),
        ("ТЕСТ-123", True, "С кириллицей в начале"),
    ]
    
    passed = 0
    failed = 0
    
    for sku_str, should_pass, description in test_cases:
        result, errors = validate_sku(sku_str)
        
        if should_pass:
            if errors:
                print(f"❌ '{sku_str}' ({description}): ДОЛЖЕН пройти, но ошибки: {errors}")
                failed += 1
            else:
                print(f"✅ '{sku_str}' ({description}): прошел валидацию -> '{result}'")
                passed += 1
        else:
            if errors:
                print(f"✅ '{sku_str}' ({description}): правильно отклонил, ошибки: {errors}")
                passed += 1
            else:
                print(f"❌ '{sku_str}' ({description}): ДОЛЖЕН быть отклонен, но прошел")
                failed += 1
    
    print(f"\n📊 Итог: {passed}/{len(test_cases)} тестов пройдено")
    
    # Дополнительный тест - массовая проверка
    print("\n📋 Массовая проверка реальных SKU:")
    real_skus = [
        "BIH-GSW-0.8 + BMT-1",
        "BHG-20М", 
        "RTHD-1100 White",
        "Ballu BHC-U15A-PS",
        "Royal Thermo RTFP/P500MR",
        "НС-1183726",
        "BHC-U15A-PS",
        "RTFP/P500MR",
        "BEC/S-1000M",
        "EPTM-2000"
    ]
    
    for sku in real_skus:
        result, errors = validate_sku(sku)
        status = "✅" if not errors else "❌"
        print(f"   {status} '{sku}' -> {'Ошибки: ' + str(errors) if errors else 'OK'}")
    
    return failed == 0


if __name__ == "__main__":
    success = test_sku_validation()
    sys.exit(0 if success else 1)