"""
routes/debug.py — Blueprint do painel de Debug (superadmin only).

Expõe informações internas do sistema para uso em apresentações/demos,
evitando a necessidade de abrir o Serial Monitor do Arduino IDE ou o
terminal do Flask durante a defesa.

Endpoints:
  GET  /api/debug/log              — últimos 200 eventos MQTT em memória
  GET  /api/debug/system           — info de segurança e conexão
  POST /api/debug/simulate-attack  — injeta um evento de ataque HMAC (demo)
  POST /api/debug/clear-log        — limpa o buffer em memória
"""

import os
import platform
import sys
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from database import audit, db
from mqtt_client import _log_event, _log_lock, mqtt_event_log, mqtt_status
from config import HMAC_KEY, MQTT_BROKER, MQTT_CA_CERT, MQTT_PORT, MQTT_USERNAME

debug_bp = Blueprint("debug", __name__)


def _superadmin_only():
    """Retorna resposta 403 se o usuário não for superadmin, None caso contrário."""
    if not current_user.is_authenticated or not current_user.is_superadmin:
        return jsonify({"error": "Acesso restrito ao superadmin"}), 403
    return None


# ── Log em memória ─────────────────────────────────────────────────────────────

@debug_bp.route("/api/debug/log")
@login_required
def debug_log():
    """Retorna os últimos eventos MQTT do buffer em memória (mais recente primeiro)."""
    err = _superadmin_only()
    if err:
        return err
    with _log_lock:
        entries = list(mqtt_event_log)
    return jsonify(entries)


@debug_bp.route("/api/debug/clear-log", methods=["POST"])
@login_required
def debug_clear_log():
    """Limpa o buffer de log em memória."""
    err = _superadmin_only()
    if err:
        return err
    with _log_lock:
        mqtt_event_log.clear()
    _log_event("info", "Log limpo pelo superadmin")
    return jsonify({"message": "Log limpo"}), 200


# ── Informações do sistema ─────────────────────────────────────────────────────

@debug_bp.route("/api/debug/system")
@login_required
def debug_system():
    """Retorna estado de segurança e conexão do sistema para exibição na apresentação."""
    err = _superadmin_only()
    if err:
        return err

    # Verifica se DB está acessível
    db_ok = False
    try:
        conn = db()
        conn.close()
        db_ok = True
    except Exception:
        pass

    # Resolve modo TLS do MQTT
    ca_cert = MQTT_CA_CERT
    if ca_cert and not os.path.isabs(ca_cert):
        import os as _os
        ca_cert = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ca_cert)
    tls_mode = "CA cert personalizado" if (ca_cert and os.path.isfile(ca_cert)) \
               else "CA store do sistema (Let's Encrypt / HiveMQ Cloud)"

    return jsonify({
        "mqtt": {
            "broker":      MQTT_BROKER,
            "port":        MQTT_PORT,
            "tls":         True,
            "tls_mode":    tls_mode,
            "auth":        bool(MQTT_USERNAME),
            "user":        MQTT_USERNAME or "—",
            "connected":   mqtt_status["connected"],
            "last_message": mqtt_status["last_message"],
        },
        "security": {
            "hmac":            True,
            "hmac_algorithm":  "HMAC-SHA256 (mbedTLS no ESP32)",
            "hmac_key_len":    len(HMAC_KEY),
            "totp_mfa":        True,
            "totp_algorithm":  "TOTP RFC 6238 (Google Authenticator)",
            "bcrypt_rounds":   12,
            "tls_min_version": "TLS 1.2",
            "rbac":            True,
            "rbac_roles":      ["superadmin", "admin", "operator"],
            "audit_log":       True,
            "nonce_table":     True,
        },
        "database": {
            "connected": db_ok,
            "engine":    "MySQL 8.0",
        },
        "server": {
            "python":   sys.version.split(" ")[0],
            "platform": platform.system(),
            "time_utc": datetime.now(timezone.utc).isoformat(),
        },
    })


# ── Simulador de ataques ───────────────────────────────────────────────────────

@debug_bp.route("/api/debug/simulate-attack", methods=["POST"])
@login_required
def debug_simulate_attack():
    """Injeta um evento de ataque HMAC falso para demonstração ao vivo.

    Aparece no log de debug EM TEMPO REAL e dispara o toast de ataque HMAC
    no dashboard (via /api/alerts/poll) para todos os admins conectados.
    """
    err = _superadmin_only()
    if err:
        return err

    body      = request.get_json(force=True) or {}
    device_id = body.get("device_id", "DEMO-ATTACKER-001").strip() or "DEMO-ATTACKER-001"
    fake_hmac = "0000000000000000000000000000000000000000000000000000000000000000"

    # Registra no log em memória (aparece no console ao vivo)
    _log_event(
        "security",
        f"⚠ DEMO — HMAC inválido de [{device_id}] REJEITADO  (hmac={fake_hmac[:16]}…)",
        {"device": device_id, "demo": True, "received": fake_hmac[:16] + "…"}
    )

    # Registra no audit_log (dispara o toast no dashboard de todos os admins)
    audit("hmac_failed",
          details={"device_id": device_id, "demo": True},
          user_id=current_user.id,
          ip=request.remote_addr)

    return jsonify({
        "message": f"Ataque simulado de '{device_id}' registrado com sucesso.",
        "device_id": device_id,
        "result": "REJEITADO — HMAC inválido",
    }), 200
