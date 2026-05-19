import os
import json

def get_api_key():
    # Стандартный путь в Linux для пользовательских конфигов
    config_path = os.path.expanduser("~/.config/agetha/config.json")
    
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            return data.get("api_key")
    except Exception as e:
        print(f"Ошибка чтения конфига: {e}")
        return None