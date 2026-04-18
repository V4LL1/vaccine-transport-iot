"""
models.py — Modelo de usuário (Flask-Login) e utilitários de RBAC.

Responsabilidades:
  - Classe User com propriedades de role e permissão
  - Callback user_loader registrado no LoginManager
  - company_where(): helper para isolar queries por empresa
  - Decorators require_permission() e admin_required()
"""

from functools import wraps

from flask import jsonify
from flask_login import UserMixin, current_user

from config import PERMISSIONS
from database import db
from extensions import login_manager


class User(UserMixin):
    """Representa um usuário autenticado.

    Guarda role e company_id para que qualquer parte do sistema possa
    verificar permissões e filtrar dados por empresa sem tocar o banco.
    """

    def __init__(self, user_id, name, email, role, totp_secret, company_id, company_name):
        self.id           = user_id
        self.name         = name
        self.email        = email
        self.role         = role
        self.totp_secret  = totp_secret
        self.company_id   = company_id
        self.company_name = company_name

    @property
    def is_superadmin(self):
        """True se o usuário tem acesso global (sem restrição de empresa)."""
        return self.role == "superadmin"

    def has_permission(self, permission):
        """Verifica se a role deste usuário inclui a permissão solicitada."""
        return permission in PERMISSIONS.get(self.role, set())


@login_manager.user_loader
def load_user(user_id):
    """Chamado pelo Flask-Login a cada requisição para restaurar o usuário da sessão."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT u.user_id, u.name, u.email, u.role, u.totp_secret,
                  u.company_id, c.name AS company_name
           FROM users u
           LEFT JOIN companies c ON u.company_id = c.company_id
           WHERE u.user_id = %s""",
        (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return User(row["user_id"], row["name"], row["email"], row["role"],
                    row["totp_secret"], row["company_id"], row.get("company_name"))
    return None


def company_where(alias=""):
    """Retorna (fragmento_sql, params) para restringir queries à empresa do usuário.

    superadmin enxerga tudo (retorna '1=1' sem parâmetros).
    admin e operator enxergam apenas sua própria empresa.

    Exemplo de uso:
        scope, params = company_where("v")
        cur.execute(f"SELECT ... FROM vaccines v WHERE {scope}", params)
    """
    col = f"{alias}.company_id" if alias else "company_id"
    if current_user.is_superadmin:
        return "1=1", []
    return f"{col} = %s", [current_user.company_id]


def require_permission(permission):
    """Decorator de rota: retorna 403 se a role do usuário não tem a permissão."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Não autenticado"}), 401
            if not current_user.has_permission(permission):
                return jsonify({
                    "error": (
                        f"Acesso negado — sua conta ({current_user.role})"
                        f" não tem permissão para '{permission}'"
                    )
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    """Decorator de rota: retorna 403 a menos que o usuário seja admin ou superadmin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role not in ("admin", "superadmin"):
            return jsonify({"error": "Acesso negado — requer perfil admin ou superadmin"}), 403
        return f(*args, **kwargs)
    return decorated
