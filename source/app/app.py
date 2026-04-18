"""
app.py — Ponto de entrada da aplicação Flask.

Responsabilidades deste arquivo:
  - Criar a instância Flask e configurar a secret key
  - Vincular as extensões (Flask-Login) ao app
  - Registrar os Blueprints de rotas
  - Iniciar o subscriber MQTT em thread daemon
  - Subir o servidor (com TLS se os certificados existirem)

Toda a lógica de negócio está nos módulos especializados:
  config.py        — variáveis de ambiente e constantes
  extensions.py    — instâncias de extensões Flask (LoginManager)
  database.py      — conexão MySQL e funções auxiliares
  models.py        — User model, RBAC decorators, company_where()
  mqtt_client.py   — subscriber MQTT e callbacks paho
  routes/auth.py   — login, logout, setup/verify TOTP
  routes/dashboard.py — dashboard e APIs de leitura
  routes/admin.py  — gestão de dispositivos, viagens, usuários, empresas
"""

import logging
import os
import threading

from flask import Flask

import config   # noqa: F401 — side-effect: dispara load_dotenv() antes de tudo
from extensions import login_manager
import models   # noqa: F401 — side-effect: registra @login_manager.user_loader

from routes.auth      import auth_bp
from routes.dashboard import dashboard_bp
from routes.admin     import admin_bp
from routes.debug     import debug_bp

from mqtt_client import start_mqtt_subscriber

# Configura o logging global (nível INFO, formato simples)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ── Criação do app Flask ───────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

# Vincula o LoginManager a esta instância do app
login_manager.init_app(app)

# ── Registro dos Blueprints ────────────────────────────────────────────────────
app.register_blueprint(auth_bp)       # /login, /logout, /setup-totp, /verify-totp
app.register_blueprint(dashboard_bp)  # /, /api/trips, /api/readings, /api/status …
app.register_blueprint(admin_bp)      # /api/admin/*
app.register_blueprint(debug_bp)      # /api/debug/* (superadmin only)


# ── Inicialização ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Subscriber MQTT em thread daemon — encerra automaticamente com o processo principal
    threading.Thread(target=start_mqtt_subscriber, daemon=True).start()

    ssl_cert = os.path.join(os.path.dirname(__file__), "../../certs/flask.crt")
    ssl_key  = os.path.join(os.path.dirname(__file__), "../../certs/flask.key")

    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        app.run(debug=False, host="0.0.0.0", port=5000,
                ssl_context=(ssl_cert, ssl_key))
    else:
        app.run(debug=False, host="0.0.0.0", port=5000)
