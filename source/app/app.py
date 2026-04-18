import threading
import json
import logging
import os
import io
import base64
import hmac
import hashlib
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
import mysql.connector
import bcrypt
import pyotp
import qrcode
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# ======== CONFIGURAÇÕES ========
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DB = {
    "host":     os.getenv("DB_HOST", "127.0.0.1"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "vaccine_transport"),
}

MQTT_BROKER   = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT     = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CA_CERT  = os.getenv("MQTT_CA_CERT", "")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
HMAC_KEY      = os.getenv("HMAC_KEY", "v@ccine-hmac-key-2026-xK9mP7qR!")

TOPIC_READINGS  = "vaccines/readings"
TOPIC_HEARTBEAT = "vaccines/heartbeat"

# ======== RBAC — Permissões por role ========
PERMISSIONS = {
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
# ================================

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Acesso restrito. Faça login."

mqtt_status = {"connected": False, "last_message": None}


# -------------------------------------------------------
# Helpers de banco
# -------------------------------------------------------
def db():
    return mysql.connector.connect(**DB)


def audit(action, target_table=None, target_id=None, details=None, user_id=None, ip=None):
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO audit_log (user_id, action, target_table, target_id, ip_address, details)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                user_id,
                action,
                target_table,
                target_id,
                ip or (request.remote_addr if request else None),
                json.dumps(details) if details else None,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.warning(f"Audit log falhou: {e}")


def ensure_device_exists(serial_number):
    """Cria dispositivo como 'pending' na primeira vez que aparece. Retorna o device dict."""
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM devices WHERE serial_number = %s", (serial_number,))
    device = cur.fetchone()
    if not device:
        cur.execute(
            "INSERT INTO devices (serial_number, registration_status, last_seen) VALUES (%s, 'pending', NOW())",
            (serial_number,)
        )
        conn.commit()
        device_id = cur.lastrowid
        logging.info(f"MQTT: Novo dispositivo descoberto: {serial_number}")
        audit("device_discovered", target_table="devices", target_id=device_id,
              details={"serial_number": serial_number})
        cur.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
        device = cur.fetchone()
    cur.close()
    conn.close()
    return device


def update_device_last_seen(serial_number):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE devices SET last_seen = NOW() WHERE serial_number = %s",
        (serial_number,)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_active_trip_for_device(device_id):
    """Retorna viagem em andamento para o device_id (PK). None se não houver."""
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT trip_id, batch_id FROM trips WHERE device_id = %s AND end_time IS NULL LIMIT 1",
        (device_id,)
    )
    trip = cur.fetchone()
    cur.close()
    conn.close()
    return trip


# -------------------------------------------------------
# Flask-Login — User Model
# -------------------------------------------------------
class User(UserMixin):
    def __init__(self, user_id, name, email, role, totp_secret):
        self.id          = user_id
        self.name        = name
        self.email       = email
        self.role        = role
        self.totp_secret = totp_secret

    def has_permission(self, permission):
        return permission in PERMISSIONS.get(self.role, set())


@login_manager.user_loader
def load_user(user_id):
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT user_id, name, email, role, totp_secret FROM users WHERE user_id = %s",
        (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return User(row["user_id"], row["name"], row["email"], row["role"], row["totp_secret"])
    return None


def require_permission(permission):
    """Decorator: exige permissão específica para a role do usuário."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Não autenticado"}), 401
            if not current_user.has_permission(permission):
                return jsonify({
                    "error": f"Acesso negado — sua conta ({current_user.role}) não tem permissão para '{permission}'"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# Mantido para compatibilidade com rotas existentes
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return jsonify({"error": "Acesso negado — requer perfil admin"}), 403
        return f(*args, **kwargs)
    return decorated


# -------------------------------------------------------
# Rotas de autenticação
# -------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").encode()

        conn = db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT user_id, name, email, role, password_hash, totp_secret FROM users WHERE email = %s",
            (email,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and bcrypt.checkpw(password, row["password_hash"].encode()):
            # Clear any leftover state from a previous incomplete login attempt
            session.pop("pending_user_id", None)
            session.pop("pending_user_email", None)
            session.pop("totp_setup_secret", None)
            session["pending_user_id"]    = row["user_id"]
            session["pending_user_email"] = row["email"]
            audit("login_password_ok", details={"email": email}, ip=request.remote_addr)

            if not row["totp_secret"]:
                return redirect(url_for("setup_totp"))
            return redirect(url_for("verify_totp"))
        else:
            error = "Email ou senha incorretos."
            audit("login_failed", details={"email": email}, ip=request.remote_addr)

    return render_template("login.html", error=error)


@app.route("/setup-totp", methods=["GET", "POST"])
def setup_totp():
    if "pending_user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["pending_user_id"]
    email   = session.get("pending_user_email", "user")

    # Reuse existing secret if already generated (avoid invalidating a scanned QR on refresh)
    if "totp_setup_secret" not in session:
        session["totp_setup_secret"] = pyotp.random_base32()

    secret = session["totp_setup_secret"]
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email, issuer_name="VaccineTransport IoT"
    )
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    if request.method == "GET":
        return render_template("setup_totp.html", qr_b64=qr_b64, secret=secret, email=email)

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
        return redirect(url_for("verify_totp"))

    audit("totp_setup_failed", user_id=user_id, ip=request.remote_addr)
    return render_template("setup_totp.html",
                           qr_b64=qr_b64, secret=secret, email=email,
                           error="Código inválido. Tente novamente.")


@app.route("/verify-totp", methods=["GET", "POST"])
def verify_totp():
    if "pending_user_id" not in session:
        return redirect(url_for("login"))

    error = None
    if request.method == "POST":
        code    = request.form.get("code", "")
        user_id = session["pending_user_id"]
        user    = load_user(user_id)

        if user and user.totp_secret and pyotp.TOTP(user.totp_secret).verify(code, valid_window=5):
            login_user(user, remember=False)
            session.pop("pending_user_id", None)
            session.pop("pending_user_email", None)
            audit("login_ok", user_id=user_id, ip=request.remote_addr,
                  details={"name": user.name, "role": user.role})
            return redirect(url_for("index"))

        error = "Código TOTP inválido."
        audit("totp_failed", user_id=user_id, ip=request.remote_addr)

    return render_template("verify_totp.html", error=error)


@app.route("/logout")
@login_required
def logout():
    audit("logout", user_id=current_user.id, ip=request.remote_addr)
    logout_user()
    return redirect(url_for("login"))


# -------------------------------------------------------
# MQTT subscriber (thread separada)
# -------------------------------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        mqtt_status["connected"] = True
        logging.info("MQTT: Conectado ao broker.")
        client.subscribe(TOPIC_READINGS,  qos=1)
        client.subscribe(TOPIC_HEARTBEAT, qos=1)
    else:
        mqtt_status["connected"] = False
        logging.warning(f"MQTT: Falha na conexão (rc={reason_code})")


def on_disconnect(client, userdata, flags, reason_code, properties):
    mqtt_status["connected"] = False
    logging.warning("MQTT: Desconectado do broker.")


def on_message(client, userdata, msg):
    mqtt_status["last_message"] = datetime.now(timezone.utc).isoformat()

    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        logging.warning(f"MQTT: Payload descartado (JSON inválido/truncado) em {msg.topic}")
        return

    device_serial = payload.get("device_id")
    if not device_serial:
        return

    # Heartbeat — não verifica HMAC (sem dados críticos)
    if msg.topic == TOPIC_HEARTBEAT:
        ensure_device_exists(device_serial)
        update_device_last_seen(device_serial)
        return

    # --- Verificação HMAC ---
    received_hmac = payload.get("hmac", "")
    signed_text   = payload.get("signed", "")
    if received_hmac and signed_text:
        # Verifica o HMAC sobre o texto exato que o ESP32 assinou
        expected_hmac = hmac.new(
            HMAC_KEY.encode(), signed_text.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(received_hmac, expected_hmac):
            logging.warning(f"MQTT: HMAC inválido de [{device_serial}] — mensagem rejeitada.")
            audit("hmac_failed", details={"device_id": device_serial})
            return
        logging.debug(f"MQTT: HMAC verificado OK [{device_serial}]")
    else:
        logging.warning(f"MQTT: Mensagem sem HMAC/signed de [{device_serial}] — aceita (modo compatibilidade).")

    # --- Leitura de sensor ---
    # 1. Auto-descobrir / buscar dispositivo
    device = ensure_device_exists(device_serial)
    update_device_last_seen(device_serial)

    # 2. Verificar se está registrado (admin atribuiu a uma viagem)
    if device.get("registration_status") != "active":
        logging.info(f"MQTT: Leitura de dispositivo pendente [{device_serial}] — aguardando registro por admin.")
        return

    # 3. Buscar viagem em andamento atribuída a este dispositivo
    active_trip = get_active_trip_for_device(device["device_id"])
    if not active_trip:
        logging.warning(f"MQTT: Dispositivo [{device_serial}] ativo mas sem viagem em andamento.")
        return

    trip_id  = active_trip["trip_id"]
    batch_id = active_trip["batch_id"]

    temperature = payload.get("temperature")
    humidity    = payload.get("humidity")
    latitude    = payload.get("latitude", 0.0)
    longitude   = payload.get("longitude", 0.0)

    if None in (temperature, humidity):
        logging.warning("MQTT: Payload sem temperatura/humidade, ignorado.")
        return

    raw_ts = payload.get("timestamp") or ""
    timestamp = None
    if raw_ts:
        normalized = raw_ts.replace("T", " ").replace("Z", "").split(".")[0]
        try:
            parsed = datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S")
            # Reject GPS default dates (no fix): month=0, day=0, or year before 2020
            if parsed.year >= 2020 and parsed.month >= 1 and parsed.day >= 1:
                timestamp = normalized
        except ValueError:
            pass
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = db()
        cur  = conn.cursor()
        cur.execute(
            """INSERT INTO readings (trip_id, batch_id, timestamp, temperature, humidity, latitude, longitude)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (trip_id, batch_id, timestamp, temperature, humidity,
             latitude if latitude else None,
             longitude if longitude else None)
        )
        reading_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()

        logging.info(f"MQTT: Leitura gravada — {temperature}°C / {humidity}% (device={device_serial}, trip={trip_id})")
        audit("reading_received", target_table="readings", target_id=reading_id,
              details={"device_id": device_serial, "temp": temperature, "humidity": humidity, "trip_id": trip_id})

    except Exception as e:
        logging.error(f"MQTT: Erro ao gravar leitura: {e}")


def start_mqtt_subscriber():
    import time as _time

    # Client created once — reused across reconnects so paho never fights itself
    # clean_session=False: sessão persistente — HiveMQ guarda mensagens QoS 1 enquanto offline
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="flask-subscriber", clean_session=False)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    ca_cert = MQTT_CA_CERT
    # If relative path, resolve it against the directory of this script (not CWD)
    if ca_cert and not os.path.isabs(ca_cert):
        ca_cert = os.path.join(os.path.dirname(os.path.abspath(__file__)), ca_cert)
    if ca_cert and os.path.isfile(ca_cert):
        client.tls_set(ca_certs=ca_cert)
        logging.info(f"MQTT: TLS ativado com CA={ca_cert}")
    else:
        client.tls_set()  # usa CA store do sistema (HiveMQ Cloud / Let's Encrypt)
        logging.info("MQTT: TLS ativado via CA store do sistema")

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # paho will wait 5–60s between automatic reconnect attempts
    client.reconnect_delay_set(min_delay=5, max_delay=60)

    # Outer loop: only needed if connect() itself raises before loop_forever() starts
    retry_delay = 5
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()   # blocks; paho handles reconnects internally
        except Exception as e:
            logging.error(f"MQTT: Conexão falhou: {e}. Tentando em {retry_delay}s...")
        mqtt_status["connected"] = False
        _time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)


# -------------------------------------------------------
# Rotas Flask — Dashboard
# -------------------------------------------------------
@app.route("/")
@login_required
def index():
    # Busca a viagem ativa mais recente para pré-selecionar no dashboard
    active_trip_id = None
    try:
        conn = db()
        cur  = conn.cursor()
        cur.execute("SELECT trip_id FROM trips WHERE end_time IS NULL ORDER BY start_time DESC LIMIT 1")
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
        user_permissions=list(PERMISSIONS.get(current_user.role, set())),
        active_trip_id=active_trip_id,
    )


@app.route("/trips/<int:trip_id>/readings")
@login_required
@require_permission("view_readings")
def trip_readings_page(trip_id):
    conn = db()
    cur  = conn.cursor(dictionary=True)
    # Detalhes da viagem
    cur.execute("""
        SELECT t.trip_id, t.origin, t.destination, t.start_time, t.end_time,
               IF(t.end_time IS NULL, 'active', 'closed') AS status,
               d.serial_number AS device_serial, d.name AS device_name,
               b.batch_code, v.name AS vaccine_name, v.min_temp, v.max_temp
        FROM trips t
        LEFT JOIN devices d ON t.device_id = d.device_id
        JOIN vaccine_batch b ON t.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        WHERE t.trip_id = %s
    """, (trip_id,))
    trip = cur.fetchone()
    if not trip:
        cur.close(); conn.close()
        return "Viagem não encontrada", 404
    # Todas as leituras
    cur.execute("""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               r.latitude, r.longitude, v.min_temp, v.max_temp
        FROM readings r
        JOIN vaccine_batch b ON r.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
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
                           trip=trip,
                           readings=readings_data,
                           stats=stats,
                           user_name=current_user.name,
                           user_role=current_user.role)


@app.route("/api/trips")
@login_required
def trips():
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT t.trip_id, t.start_time, t.end_time, t.origin, t.destination,
               IF(t.end_time IS NULL, 'active', 'closed') AS status,
               b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp,
               d.serial_number AS device_serial, d.name AS device_name
        FROM trips t
        JOIN vaccine_batch b ON t.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        LEFT JOIN devices d ON t.device_id = d.device_id
        ORDER BY t.start_time DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/readings/<int:trip_id>")
@login_required
def readings(trip_id):
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               r.latitude, r.longitude,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN vaccine_batch b ON r.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        WHERE r.trip_id = %s
        ORDER BY r.timestamp ASC
    """, (trip_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/readings/recent")
@login_required
def recent_readings():
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               r.latitude, r.longitude,
               t.trip_id, b.batch_code,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN trips t ON r.trip_id = t.trip_id
        JOIN vaccine_batch b ON r.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        ORDER BY r.timestamp DESC
        LIMIT 20
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/alarms")
@login_required
def alarms():
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               t.trip_id, b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN trips t   ON r.trip_id  = t.trip_id
        JOIN vaccine_batch b ON r.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        WHERE r.temperature < v.min_temp OR r.temperature > v.max_temp
        ORDER BY r.timestamp DESC
        LIMIT 50
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/devices")
@login_required
def devices():
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT d.device_id, d.serial_number, d.name, d.status,
               d.registration_status, d.last_seen,
               u.name AS registered_by_name,
               d.registered_at,
               CASE
                 WHEN d.last_seen IS NULL THEN 'never'
                 WHEN d.last_seen >= NOW() - INTERVAL 60 SECOND THEN 'online'
                 WHEN d.last_seen >= NOW() - INTERVAL 5 MINUTE  THEN 'recent'
                 ELSE 'offline'
               END AS connectivity,
               t.trip_id AS active_trip_id,
               t.destination AS active_trip_dest
        FROM devices d
        LEFT JOIN users u ON d.registered_by = u.user_id
        LEFT JOIN trips t ON t.device_id = d.device_id AND t.end_time IS NULL
        ORDER BY d.registration_status ASC, d.serial_number
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/status")
@login_required
def status():
    connected = mqtt_status["connected"]

    # Grace period: if we received a message in the last 90s, treat as connected
    # even if on_disconnect fired (covers brief reconnect windows)
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


@app.route("/api/audit")
@login_required
@require_permission("view_audit")
def audit_log():
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
    cur.close()
    conn.close()
    return jsonify(data)


# -------------------------------------------------------
# Rotas Admin — Gestão de Dispositivos
# -------------------------------------------------------
@app.route("/api/admin/devices/pending")
@login_required
@require_permission("register_device")
def admin_pending_devices():
    """Lista dispositivos descobertos mas não registrados."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT device_id, serial_number, last_seen,
               CASE
                 WHEN last_seen >= NOW() - INTERVAL 60 SECOND THEN 'online'
                 WHEN last_seen >= NOW() - INTERVAL 5 MINUTE  THEN 'recent'
                 ELSE 'offline'
               END AS connectivity
        FROM devices
        WHERE registration_status = 'pending'
        ORDER BY last_seen DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/admin/devices/<int:device_id>/register", methods=["POST"])
@login_required
@require_permission("register_device")
def admin_register_device(device_id):
    """Registra um dispositivo: atribui nome e viagem."""
    body     = request.get_json(force=True)
    name     = body.get("name", "").strip()
    trip_id  = body.get("trip_id")

    if not name:
        return jsonify({"error": "Nome do dispositivo obrigatório"}), 400
    if not trip_id:
        return jsonify({"error": "Viagem obrigatória"}), 400

    conn = db()
    cur  = conn.cursor(dictionary=True)

    # Verifica se dispositivo existe e está pendente
    cur.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
    device = cur.fetchone()
    if not device:
        cur.close(); conn.close()
        return jsonify({"error": "Dispositivo não encontrado"}), 404
    if device["registration_status"] == "active":
        cur.close(); conn.close()
        return jsonify({"error": "Dispositivo já está registrado"}), 409

    # Verifica se viagem existe e está sem device atribuído
    cur.execute("SELECT * FROM trips WHERE trip_id = %s AND end_time IS NULL", (trip_id,))
    trip = cur.fetchone()
    if not trip:
        cur.close(); conn.close()
        return jsonify({"error": "Viagem não encontrada ou já encerrada"}), 404

    # Atualiza dispositivo
    cur.execute("""
        UPDATE devices
        SET name = %s,
            registration_status = 'active',
            status = 'active',
            registered_by = %s,
            registered_at = NOW()
        WHERE device_id = %s
    """, (name, current_user.id, device_id))

    # Atribui dispositivo à viagem
    cur.execute(
        "UPDATE trips SET device_id = %s WHERE trip_id = %s",
        (device_id, trip_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    audit("device_registered", target_table="devices", target_id=device_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"name": name, "trip_id": trip_id, "serial": device["serial_number"]})

    logging.info(f"Dispositivo {device['serial_number']} registrado como '{name}' na viagem {trip_id} por {current_user.name}")
    return jsonify({"message": f"Dispositivo '{name}' registrado com sucesso na viagem {trip_id}"}), 200


@app.route("/api/admin/devices/<int:device_id>/deactivate", methods=["POST"])
@login_required
@require_permission("deactivate_device")
def admin_deactivate_device(device_id):
    """Desativa um dispositivo (remove da viagem e marca como inativo)."""
    conn = db()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE devices SET status = 'inactive', registration_status = 'inactive'
        WHERE device_id = %s
    """, (device_id,))
    # Remove device da viagem ativa
    cur.execute(
        "UPDATE trips SET device_id = NULL WHERE device_id = %s AND end_time IS NULL",
        (device_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

    audit("device_deactivated", target_table="devices", target_id=device_id,
          user_id=current_user.id, ip=request.remote_addr)
    return jsonify({"message": "Dispositivo desativado"}), 200


# -------------------------------------------------------
# Rotas Admin — Gestão de Viagens
# -------------------------------------------------------
@app.route("/api/admin/trips", methods=["GET"])
@login_required
@require_permission("manage_trips")
def admin_trips():
    """Lista todas as viagens com status de atribuição."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT t.trip_id, t.start_time, t.end_time, t.origin, t.destination,
               b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp,
               d.serial_number AS device_serial,
               d.name AS device_name,
               d.registration_status
        FROM trips t
        JOIN vaccine_batch b ON t.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        LEFT JOIN devices d ON t.device_id = d.device_id
        ORDER BY t.start_time DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/admin/trips", methods=["POST"])
@login_required
@require_permission("create_trip")
def admin_create_trip():
    """Cria nova viagem (sem device — será atribuído no registro do dispositivo)."""
    body        = request.get_json(force=True)
    batch_id    = body.get("batch_id")
    origin      = body.get("origin", "").strip()
    destination = body.get("destination", "").strip()

    if not all([batch_id, origin, destination]):
        return jsonify({"error": "batch_id, origin e destination são obrigatórios"}), 400

    conn = db()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO trips (batch_id, device_id, start_time, origin, destination)
        VALUES (%s, NULL, NOW(), %s, %s)
    """, (batch_id, origin, destination))
    conn.commit()
    trip_id = cur.lastrowid
    cur.close()
    conn.close()

    audit("trip_created", target_table="trips", target_id=trip_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"batch_id": batch_id, "origin": origin, "destination": destination})
    return jsonify({"message": "Viagem criada", "trip_id": trip_id}), 201


@app.route("/api/admin/trips/<int:trip_id>/close", methods=["POST"])
@login_required
@require_permission("close_trip")
def admin_close_trip(trip_id):
    """Encerra uma viagem em andamento."""
    conn = db()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE trips SET end_time = NOW(), received_confirmation = TRUE WHERE trip_id = %s AND end_time IS NULL",
        (trip_id,)
    )
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()

    if affected == 0:
        return jsonify({"error": "Viagem não encontrada ou já encerrada"}), 404

    audit("trip_closed", target_table="trips", target_id=trip_id,
          user_id=current_user.id, ip=request.remote_addr)
    return jsonify({"message": "Viagem encerrada"}), 200


@app.route("/api/admin/batches")
@login_required
@require_permission("create_trip")
def admin_batches():
    """Lista lotes disponíveis para criação de viagens."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT b.batch_id, b.batch_code, b.expiration_date, b.quantity_units,
               v.name AS vaccine_name, v.min_temp, v.max_temp
        FROM vaccine_batch b
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        ORDER BY v.name, b.batch_code
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/admin/vaccines", methods=["GET"])
@login_required
@require_permission("manage_users")
def admin_vaccines():
    """Lista todos os produtos cadastrados."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT vaccine_id, name, manufacturer, min_temp, max_temp FROM vaccines ORDER BY name")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/admin/vaccines", methods=["POST"])
@login_required
@require_permission("manage_users")
def admin_create_vaccine():
    """Cadastra um novo produto farmacêutico."""
    body         = request.get_json(force=True)
    name         = body.get("name", "").strip()
    manufacturer = body.get("manufacturer", "").strip()
    min_temp     = body.get("min_temp")
    max_temp     = body.get("max_temp")

    if not name:
        return jsonify({"error": "Nome do produto é obrigatório"}), 400
    if min_temp is None or max_temp is None:
        return jsonify({"error": "Temperaturas mínima e máxima são obrigatórias"}), 400
    try:
        min_temp = float(min_temp)
        max_temp = float(max_temp)
    except (ValueError, TypeError):
        return jsonify({"error": "Temperaturas devem ser valores numéricos"}), 400
    if min_temp >= max_temp:
        return jsonify({"error": "Temperatura mínima deve ser menor que a máxima"}), 400

    conn = db()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO vaccines (name, manufacturer, min_temp, max_temp) VALUES (%s, %s, %s, %s)",
        (name, manufacturer or None, min_temp, max_temp)
    )
    conn.commit()
    vaccine_id = cur.lastrowid
    cur.close()
    conn.close()

    audit("vaccine_created", target_table="vaccines", target_id=vaccine_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"name": name, "manufacturer": manufacturer, "min_temp": min_temp, "max_temp": max_temp})
    return jsonify({"message": "Produto cadastrado", "vaccine_id": vaccine_id}), 201


@app.route("/api/admin/batches", methods=["POST"])
@login_required
@require_permission("create_trip")
def admin_create_batch():
    """Cadastra um novo lote de produto."""
    body            = request.get_json(force=True)
    vaccine_id      = body.get("vaccine_id")
    batch_code      = body.get("batch_code", "").strip()
    expiration_date = body.get("expiration_date", "").strip()
    quantity_units  = body.get("quantity_units")

    if not all([vaccine_id, batch_code, expiration_date, quantity_units]):
        return jsonify({"error": "Todos os campos são obrigatórios"}), 400
    try:
        quantity_units = int(quantity_units)
    except (ValueError, TypeError):
        return jsonify({"error": "Quantidade deve ser um número inteiro"}), 400

    conn = db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO vaccine_batch (vaccine_id, batch_code, expiration_date, quantity_units) VALUES (%s, %s, %s, %s)",
            (vaccine_id, batch_code, expiration_date, quantity_units)
        )
        conn.commit()
        batch_id = cur.lastrowid
    except mysql.connector.IntegrityError:
        cur.close(); conn.close()
        return jsonify({"error": f"Código de lote '{batch_code}' já existe"}), 409
    cur.close()
    conn.close()

    audit("batch_created", target_table="vaccine_batch", target_id=batch_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"vaccine_id": vaccine_id, "batch_code": batch_code, "quantity_units": quantity_units})
    return jsonify({"message": "Lote cadastrado", "batch_id": batch_id}), 201


# -------------------------------------------------------
if __name__ == "__main__":
    t = threading.Thread(target=start_mqtt_subscriber, daemon=True)
    t.start()
    ssl_cert = os.path.join(os.path.dirname(__file__), "../../certs/flask.crt")
    ssl_key  = os.path.join(os.path.dirname(__file__), "../../certs/flask.key")
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        app.run(debug=False, host="0.0.0.0", port=5000,
                ssl_context=(ssl_cert, ssl_key))
    else:
        app.run(debug=False, host="0.0.0.0", port=5000)
