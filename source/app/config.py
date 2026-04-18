"""
config.py — Configurações centrais do sistema.

Todas as variáveis de ambiente são carregadas aqui uma única vez.
Outros módulos importam as constantes diretamente deste arquivo.
"""

import os

from dotenv import load_dotenv

# Carrega o arquivo .env da mesma pasta que este script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ── Banco de dados MySQL ────────────────────────────────────────────────────────
DB = {
    "host":     os.getenv("DB_HOST", "127.0.0.1"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "vaccine_transport"),
}

# ── MQTT Broker ─────────────────────────────────────────────────────────────────
MQTT_BROKER   = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT     = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CA_CERT  = os.getenv("MQTT_CA_CERT", "")        # caminho para CA cert (TLS)
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# Chave compartilhada entre ESP32 e Flask para verificação HMAC-SHA256
HMAC_KEY = os.getenv("HMAC_KEY", "v@ccine-hmac-key-2026-xK9mP7qR!")

# Tópicos MQTT assinados pelo subscriber Flask
TOPIC_READINGS  = "vaccines/readings"
TOPIC_HEARTBEAT = "vaccines/heartbeat"

# ── RBAC — Permissões por role ──────────────────────────────────────────────────
# Cada role possui um conjunto de permissões. O decorator require_permission()
# em models.py verifica se a role do usuário logado contém a permissão exigida.
PERMISSIONS = {
    "superadmin": {
        "view_dashboard", "view_readings", "view_devices", "view_alarms",
        "view_audit",
        "register_device", "deactivate_device",
        "manage_trips", "create_trip", "close_trip",
        "manage_users",
        "manage_companies",   # exclusivo do superadmin
    },
    "admin": {
        "view_dashboard", "view_readings", "view_devices", "view_alarms",
        "view_audit",
        "register_device", "deactivate_device",
        "manage_trips", "create_trip", "close_trip",
        "manage_users",
    },
    "operator": {
        "view_dashboard", "view_readings", "view_devices", "view_alarms",
    },
}
