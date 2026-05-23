import hashlib
from pathlib import Path

LCD_CONFIG_PATH = Path("app/config/lcd/ca_hospice_lcds.json")

def compute_lcd_config_hash() -> str:
    data = LCD_CONFIG_PATH.read_bytes()
    return hashlib.sha256(data).hexdigest()