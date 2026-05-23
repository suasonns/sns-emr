import json
from pathlib import Path

LCD_CONFIG_PATH = Path("app/config/lcd/ca_hospice_lcds.json")

def load_ca_hospice_lcds():
    with open(LCD_CONFIG_PATH, "r") as f:
        return json.load(f)