import hashlib
import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "presence_threshold_minutes": 30,
    "roster_columns": {
        "acdid": "ACDID",
        "payroll": "Agent´s Payroll Number",
        "last_name": "Last Name",
        "first_name": "First Name",
        "mail": "Mail",
        "rut": "RUT / DNI",
        "site": "Site",
        "lob": "LOB",
        "skill": "Secondary Skill",
        "scheduled_hours": "Scheduled Hrs.",
        "Mon": "Mon Hrs.",
        "Tue": "Tue Hrs.",
        "Wed": "Wed Hrs.",
        "Thu": "Thu Hrs.",
        "Fri": "Fri Hrs.",
        "Sat": "Sat Hrs.",
        "Sun": "Sun Hrs."
    }
}

def load_config():
    """Carga la configuración desde un archivo JSON."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    """Guarda la configuración en un archivo JSON."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def generate_agent_id(last_name, first_name, mail):
    """Genera un ID único determinista para un agente."""
    input_str = f"{str(last_name).strip().lower()}|{str(first_name).strip().lower()}|{str(mail).strip().lower()}"
    return hashlib.md5(input_str.encode()).hexdigest()
