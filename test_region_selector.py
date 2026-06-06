#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Простой тест селектора области
Без интеграции с GUI - просто для тестирования
"""
import sys
import json


def test_simple_selector():
    """Test SimpleScreenSelector"""
    print("\n" + "="*60)
    print("ТЕСТ ПРОСТОГО СЕЛЕКТОРА (OpenCV)")
    print("="*60)
    
    from utils.simple_screen_selector import SimpleScreenSelector
    
    selector = SimpleScreenSelector()
    region = selector.select_region()
    
    if region:
        print("\n✓ УСПЕХ! Область выбрана:")
        print(json.dumps(region, indent=2))
        return region
    else:
        print("\n⚠️  Выбор отменён")
        return None


def test_tkinter_selector():
    """Test TkinterScreenSelector"""
    print("\n" + "="*60)
    print("ТЕСТ TKINTER СЕЛЕКТОРА")
    print("="*60)
    
    from utils.screen_selector import ScreenSelector
    
    region_result = {'region': None}
    
    def callback(region):
        region_result['region'] = region
    
    selector = ScreenSelector(callback)
    selector.select_region()
    
    region = region_result['region']
    
    if region:
        print("\n✓ УСПЕХ! Область выбрана:")
        print(json.dumps(region, indent=2))
        return region
    else:
        print("\n⚠️  Выбор отменён")
        return None


def save_region_to_config(region):
    """Save region to config.json"""
    if not region:
        return False
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['detection_region'] = region
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("\n✓ Регион сохранён в config.json")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка при сохранении: {e}")
        return False


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("🎯 ТЕСТ СЕЛЕКТОРА ОБЛАСТИ")
    print("="*60)
    print("\nВыбери метод:")
    print("1. OpenCV (рекомендуется)")
    print("2. Tkinter")
    print("3. Выход")
    
    choice = input("\nВведи номер (1-3): ").strip()
    
    region = None
    
    if choice == '1':
        region = test_simple_selector()
    elif choice == '2':
        region = test_tkinter_selector()
    elif choice == '3':
        print("Выход")
        return
    else:
        print("❌ Неверный выбор")
        return
    
    if region:
        save = input("\nСохранить регион в config.json? (y/n): ").strip().lower()
        if save == 'y':
            if save_region_to_config(region):
                print("✓ Готово! Можно запускать бота")
            else:
                print("❌ Ошибка сохранения")
        else:
            print("Отменено")
            print(f"\nДля сохранения вручную используй эти координаты:")
            print(json.dumps(region, indent=2))
    else:
        print("Выбор отменён")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
