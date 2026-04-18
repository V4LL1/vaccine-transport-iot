"""
routes/auth.py — Blueprint de autenticação.

Rotas:
  GET/POST /login        — formulário de login (email + senha)
  GET/POST /setup-totp   — configuração inicial do MFA (exibe QR code)
  GET/POST /verify-totp  — verificação do código TOTP
  GET      /logout       — encerra a sessão

Fluxo de login em dois fatores:
  1. /login valida email+senha → salva pending_user_id na sessão
  2. /setup-totp (apenas primeiro acesso) → gera secret, mostra QR, confirma código
  3. /verify-totp → verifica TOTP → chama login_user() → redireciona ao dashboard
"""

import base64
import io

import bcrypt
import pyotp
import qrcode
from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from database import audit, db
from models import load_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").encode()

        conn = db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT user_id, name, email, role, password_hash, totp_secret"
            " FROM users WHERE email = %s",
            (email,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and bcrypt.checkpw(password, row["password_hash"].encode()):
            # Limpa estado de tentativas de login anteriores incompletas
            session.pop("pending_user_id",    None)
            session.pop("pending_user_email", None)
            session.pop("totp_setup_secret",  None)

            session["pending_user_id"]    = row["user_id"]
            session["pending_user_email"] = row["email"]
            audit("login_password_ok", details={"email": email}, ip=request.remote_addr)

            # Redireciona para setup na primeira vez (sem TOTP ainda)
            if not row["totp_secret"]:
                return redirect(url_for("auth.setup_totp"))
            return redirect(url_for("auth.verify_totp"))

        error = "Email ou senha incorretos."
        audit("login_failed", details={"email": email}, ip=request.remote_addr)

    return render_template("login.html", error=error)


@auth_bp.route("/setup-totp", methods=["GET", "POST"])
def setup_totp():
    if "pending_user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["pending_user_id"]
    email   = session.get("pending_user_email", "user")

    # Reutiliza o secret já gerado para não invalidar um QR code já escaneado
    if "totp_setup_secret" not in session:
        session["totp_setup_secret"] = pyotp.random_base32()

    secret = session["totp_setup_secret"]
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email, issuer_name="VaccineTransport IoT"
    )

    # Gera imagem PNG do QR code em memória e converte para base64 para o template
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    if request.method == "GET":
        return render_template("setup_totp.html", qr_b64=qr_b64, secret=secret, email=email)

    # POST: valida o primeiro código digitado pelo usuário
    code = request.form.get("code", "")
    if pyotp.TOTP(secret).verify(code, valid_window=5):
        conn = db()
        cur  = conn.cursor()
        cur.execute("UPDATE users SET totp_secret = %s WHERE user_id = %s", (secret, user_id))
        conn.commit()
        cur.close()
        conn.close()
        audit("totp_setup_ok", user_id=user_id, ip=request.remote_addr)
        session.pop("totp_setup_secret", None)
        return redirect(url_for("auth.verify_totp"))

    audit("totp_setup_failed", user_id=user_id, ip=request.remote_addr)
    return render_template("setup_totp.html",
                           qr_b64=qr_b64, secret=secret, email=email,
                           error="Código inválido. Tente novamente.")


@auth_bp.route("/verify-totp", methods=["GET", "POST"])
def verify_totp():
    if "pending_user_id" not in session:
        return redirect(url_for("auth.login"))

    error = None
    if request.method == "POST":
        code    = request.form.get("code", "")
        user_id = session["pending_user_id"]
        user    = load_user(user_id)

        if user and user.totp_secret and \
                pyotp.TOTP(user.totp_secret).verify(code, valid_window=5):
            login_user(user, remember=False)
            session.pop("pending_user_id",    None)
            session.pop("pending_user_email", None)
            audit("login_ok", user_id=user_id, ip=request.remote_addr,
                  details={"name": user.name, "role": user.role})
            return redirect(url_for("dashboard.index"))

        error = "Código TOTP inválido."
        audit("totp_failed", user_id=user_id, ip=request.remote_addr)

    return render_template("verify_totp.html", error=error)


@auth_bp.route("/logout")
@login_required
def logout():
    audit("logout", user_id=current_user.id, ip=request.remote_addr)
    logout_user()
    return redirect(url_for("auth.login"))
