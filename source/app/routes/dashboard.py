"""
routes/dashboard.py — Blueprint do dashboard e APIs de leitura.

Rotas de visualização (todos os roles com login):
  GET /                          — página principal do dashboard
  GET /trips/<id>/readings       — página de detalhes de uma viagem

APIs de dados (somente leitura, scoped por empresa):
  GET /api/trips                 — lista de viagens
  GET /api/readings/<trip_id>    — leituras de uma viagem específica
  GET /api/readings/recent       — últimas 20 leituras da empresa
  GET /api/alarms                — violações de temperatura
  GET /api/devices               — status dos dispositivos
  GET /api/alerts/poll           — alertas novos para toast (polling a cada 10s)
  GET /api/status                — estado da conexão MQTT
  GET /api/audit                 — log de auditoria (admin/superadmin)
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from config import PERMISSIONS
from database import db
from models import company_where, require_permission
from mqtt_client import mqtt_status

dashboard_bp = Blueprint("dashboard", __name__)


# ── Páginas ────────────────────────────────────────────────────────────────────

@dashboard_bp.route("/")
@login_required
def index():
    """Página principal: pré-seleciona a viagem ativa mais recente da empresa."""
    active_trip_id = None
    try:
        scope, params = company_where("v")
        conn = db()
        cur  = conn.cursor()
        cur.execute(f"""
            SELECT t.trip_id FROM trips t
            JOIN vaccine_batch b ON t.batch_id  = b.batch_id
            JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
            WHERE t.end_time IS NULL AND ({scope})
            ORDER BY t.start_time DESC LIMIT 1
        """, params)
        row = cur.fetchone()
        if row:
            active_trip_id = row[0]
        cur.close()
        conn.close()
    except Exception:
        pass

    return render_template(
        "index.html",
        user_name=current_user.name,
        user_role=current_user.role,
        user_company=current_user.company_name or "—",
        user_permissions=list(PERMISSIONS.get(current_user.role, set())),
        active_trip_id=active_trip_id,
    )


@dashboard_bp.route("/trips/<int:trip_id>/readings")
@login_required
@require_permission("view_readings")
def trip_readings_page(trip_id):
    """Página de detalhes de uma viagem: exibe todas as leituras e estatísticas."""
    conn = db()
    cur  = conn.cursor(dictionary=True)

    # Dados da viagem (cabeçalho da página)
    cur.execute("""
        SELECT t.trip_id, t.origin, t.destination, t.start_time, t.end_time,
               IF(t.end_time IS NULL, 'active', 'closed') AS status,
               d.serial_number AS device_serial, d.name AS device_name,
               b.batch_code, v.name AS vaccine_name, v.min_temp, v.max_temp
        FROM trips t
        LEFT JOIN devices d     ON t.device_id  = d.device_id
        JOIN vaccine_batch b    ON t.batch_id   = b.batch_id
        JOIN vaccines v         ON b.vaccine_id = v.vaccine_id
        WHERE t.trip_id = %s
    """, (trip_id,))
    trip = cur.fetchone()
    if not trip:
        cur.close(); conn.close()
        return "Viagem não encontrada", 404

    # Todas as leituras em ordem cronológica
    cur.execute("""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               r.latitude, r.longitude, v.min_temp, v.max_temp
        FROM readings r
        JOIN vaccine_batch b ON r.batch_id  = b.batch_id
        JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
        WHERE r.trip_id = %s
        ORDER BY r.timestamp ASC
    """, (trip_id,))
    readings_data = cur.fetchall()
    cur.close(); conn.close()

    temps = [r["temperature"] for r in readings_data if r["temperature"] is not None]
    violations = sum(
        1 for r in readings_data
        if r["temperature"] is not None
        and (r["temperature"] < trip["min_temp"] or r["temperature"] > trip["max_temp"])
    )
    stats = {
        "total":      len(readings_data),
        "violations": violations,
        "avg":        round(sum(temps) / len(temps), 2) if temps else None,
        "max":        round(max(temps), 2) if temps else None,
        "min":        round(min(temps), 2) if temps else None,
    }
    return render_template("trip_readings.html",
                           trip=trip, readings=readings_data, stats=stats,
                           user_name=current_user.name, user_role=current_user.role)


# ── APIs de dados ──────────────────────────────────────────────────────────────

@dashboard_bp.route("/api/trips")
@login_required
def trips():
    """Lista todas as viagens da empresa do usuário."""
    scope, params = company_where("v")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT t.trip_id, t.start_time, t.end_time, t.origin, t.destination,
               IF(t.end_time IS NULL, 'active', 'closed') AS status,
               b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp,
               d.serial_number AS device_serial, d.name AS device_name
        FROM trips t
        JOIN vaccine_batch b ON t.batch_id  = b.batch_id
        JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
        LEFT JOIN devices d  ON t.device_id  = d.device_id
        WHERE {scope}
        ORDER BY t.start_time DESC
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@dashboard_bp.route("/api/readings/<int:trip_id>")
@login_required
def readings(trip_id):
    """Retorna todas as leituras de uma viagem em ordem cronológica."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               r.latitude, r.longitude,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN vaccine_batch b ON r.batch_id  = b.batch_id
        JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
        WHERE r.trip_id = %s
        ORDER BY r.timestamp ASC
    """, (trip_id,))
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@dashboard_bp.route("/api/readings/recent")
@login_required
def recent_readings():
    """Retorna as 20 leituras mais recentes da empresa do usuário."""
    scope, params = company_where("v")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               r.latitude, r.longitude,
               t.trip_id, b.batch_code,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN trips t         ON r.trip_id   = t.trip_id
        JOIN vaccine_batch b ON r.batch_id  = b.batch_id
        JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
        WHERE {scope}
        ORDER BY r.timestamp DESC
        LIMIT 20
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@dashboard_bp.route("/api/alarms")
@login_required
def alarms():
    """Retorna as 50 violações de temperatura mais recentes da empresa."""
    scope, params = company_where("v")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               t.trip_id, b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN trips t         ON r.trip_id   = t.trip_id
        JOIN vaccine_batch b ON r.batch_id  = b.batch_id
        JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
        WHERE ({scope}) AND (r.temperature < v.min_temp OR r.temperature > v.max_temp)
        ORDER BY r.timestamp DESC
        LIMIT 50
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@dashboard_bp.route("/api/devices")
@login_required
def devices():
    """Retorna dispositivos da empresa com status de conectividade calculado."""
    scope, params = company_where("d")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT d.device_id, d.serial_number, d.name, d.status,
               d.registration_status, d.last_seen,
               u.name AS registered_by_name,
               d.registered_at,
               CASE
                 WHEN d.last_seen IS NULL                          THEN 'never'
                 WHEN d.last_seen >= NOW() - INTERVAL 60 SECOND   THEN 'online'
                 WHEN d.last_seen >= NOW() - INTERVAL 5 MINUTE    THEN 'recent'
                 ELSE 'offline'
               END AS connectivity,
               t.trip_id     AS active_trip_id,
               t.destination AS active_trip_dest
        FROM devices d
        LEFT JOIN users u ON d.registered_by = u.user_id
        LEFT JOIN trips t ON t.device_id = d.device_id AND t.end_time IS NULL
        WHERE {scope}
        ORDER BY d.registration_status ASC, d.serial_number
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@dashboard_bp.route("/api/alerts/poll")
@login_required
def alerts_poll():
    """Retorna alertas novos desde o timestamp 'since' (ISO 8601).

    Chamado pelo dashboard a cada ~10s para exibir toasts:
      - temp_violations: violações de temperatura (todos os roles, scoped por empresa)
      - hmac_attacks:    ataques de HMAC (somente admin e superadmin)

    Query param trip_id (opcional): filtra violações por viagem específica.
    """
    since   = request.args.get("since", "")
    trip_id = request.args.get("trip_id", type=int)

    # Fallback: últimos instantes se 'since' não foi fornecido
    if not since:
        since = (datetime.now(timezone.utc).replace(microsecond=0)
                 .strftime("%Y-%m-%d %H:%M:%S"))

    result = {"temp_violations": [], "hmac_attacks": []}

    try:
        conn = db()
        cur  = conn.cursor(dictionary=True)

        # Violações de temperatura — scoped por empresa e opcionalmente por viagem
        scope, params = company_where("v")
        trip_filter   = "AND r.trip_id = %s" if trip_id else ""
        trip_params   = [trip_id] if trip_id else []

        cur.execute(f"""
            SELECT r.reading_id, r.timestamp, r.temperature,
                   v.min_temp, v.max_temp, v.name AS vaccine_name,
                   t.trip_id
            FROM readings r
            JOIN trips t         ON r.trip_id   = t.trip_id
            JOIN vaccine_batch b ON r.batch_id  = b.batch_id
            JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
            WHERE ({scope})
              AND r.timestamp > %s
              AND (r.temperature < v.min_temp OR r.temperature > v.max_temp)
              {trip_filter}
            ORDER BY r.timestamp DESC
            LIMIT 10
        """, params + [since] + trip_params)
        result["temp_violations"] = cur.fetchall()

        # Ataques HMAC — apenas para admin e superadmin
        if current_user.role in ("admin", "superadmin"):
            cur.execute("""
                SELECT log_id, created_at, details
                FROM audit_log
                WHERE action = 'hmac_failed'
                  AND created_at > %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (since,))
            result["hmac_attacks"] = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        logging.warning(f"alerts_poll error: {e}")

    return jsonify(result)


@dashboard_bp.route("/api/status")
@login_required
def status():
    """Retorna estado da conexão MQTT e horário do servidor.

    Grace period de 90s: se uma mensagem foi recebida recentemente, considera
    o broker conectado mesmo que on_disconnect tenha disparado (janela de reconexão).
    """
    connected = mqtt_status["connected"]

    if not connected and mqtt_status["last_message"]:
        try:
            last = datetime.fromisoformat(mqtt_status["last_message"])
            if (datetime.now(timezone.utc) - last).total_seconds() < 90:
                connected = True
        except Exception:
            pass

    return jsonify({
        "broker_connected":  connected,
        "last_mqtt_message": mqtt_status["last_message"],
        "server_time":       datetime.now(timezone.utc).isoformat()
    })


@dashboard_bp.route("/api/audit")
@login_required
@require_permission("view_audit")
def audit_log():
    """Retorna as 200 entradas mais recentes do log de auditoria (admin/superadmin)."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT l.log_id, l.action, l.target_table, l.target_id,
               l.ip_address, l.details, l.created_at,
               u.name AS user_name
        FROM audit_log l
        LEFT JOIN users u ON l.user_id = u.user_id
        ORDER BY l.created_at DESC
        LIMIT 200
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)
