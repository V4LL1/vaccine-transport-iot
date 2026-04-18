"""
extensions.py — Instâncias das extensões Flask.

Separar as extensões em um módulo próprio evita importações circulares:
  app.py cria o Flask app e chama login_manager.init_app(app)
  models.py decora load_user com @login_manager.user_loader
  ambos importam login_manager daqui, sem depender um do outro.
"""

from flask_login import LoginManager

# Instanciado aqui; vinculado ao app Flask em app.py via init_app()
login_manager = LoginManager()

# Nome do endpoint de login — usa notação Blueprint: "<blueprint>.<função>"
login_manager.login_view    = "auth.login"
login_manager.login_message = "Acesso restrito. Faça login."
