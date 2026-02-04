import os
import json

def load_config(filename="config.txt"):
    # Get the directory where config.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, filename)
    
    config_dict = {}
    if not os.path.exists(full_path):
        print(f"⚠️ Warning: Config file not found at {full_path}")
        return config_dict
    
    with open(full_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                val = value.strip()
                # Remove surrounding quotes if present
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1].strip()
                config_dict[key] = val

    # Safe debug info
    token = config_dict.get('SECRET_TOKEN')
    if token:
        if token == "TWÓJ_TOKEN_DISCORD":
            print("❌ Error: You are still using the placeholder 'TWÓJ_TOKEN_DISCORD' in config.txt!")
        else:
            print(f"✅ Token loaded (Length: {len(token)} chars, Start: {token[:4]}...{token[-4:]})")
    
    return config_dict

_config = load_config()

TOKEN = _config.get('SECRET_TOKEN')
SOURCE_ID = int(_config.get('SOURCE_ID', 0))
WEBHOOK_URL = _config.get('WEBHOOK_URL')
REPORT_WEBHOOK_URL = _config.get('REPORT_WEBHOOK_URL')
