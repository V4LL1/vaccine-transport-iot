import threading
import json
import logging
import os
import io
import base64
from datetime import datetime, timezone

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

TOPIC_READINGS  = "vaccines/readings"
TOPIC_HEARTBEAT = "vaccines/heartbeat"
# ================================

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Acesso restrito. Faça login."

# Estado do broker
mqtt_status = {"connected": False, "last_message": None}


# -------------------------------------------------------
# Helpers de banco
# -------------------------------------------------------
def db():
    return mysql.connector.connect(**DB)


def get_batch_id_for_trip(trip_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT batch_id FROM trips WHERE trip_id = %s", (trip_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


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


def audit(action, target_table=None, target_id=None, details=None, user_id=None, ip=None):
    """Registra uma ação no audit_log."""
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
                ip or request.remote_addr if request else None,
                json.dumps(details) if details else None,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.warning(f"Audit log falhou: {e}")


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


def admin_required(f):
    """Decorator: exige role = admin."""
    from functools import wraps
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
            # Senha correta — salvar user_id na session para etapa TOTP
            session["pending_user_id"] = row["user_id"]
            session["pending_user_email"] = row["email"]
            audit("login_password_ok", details={"email": email}, ip=request.remote_addr)

            if not row["totp_secret"]:
                # Primeiro login — redirecionar para configurar TOTP
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

    if request.method == "GET":
        # Gerar novo secret e armazenar temporariamente na session
        secret = pyotp.random_base32()
        session["totp_setup_secret"] = secret
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email, issuer_name="VaccineTransport IoT"
        )
        # Gerar QR code em base64
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        return render_template("setup_totp.html", qr_b64=qr_b64, secret=secret)

    # POST — verificar código antes de salvar
    code   = request.form.get("code", "")
    secret = session.get("totp_setup_secret", "")
    if pyotp.TOTP(secret).verify(code, valid_window=1):
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
                           qr_b64=None, secret=secret,
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

        if user and user.totp_secret and pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
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
# MQTT subscriber (roda em thread separada)
# -------------------------------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        mqtt_status["connected"] = True
        logging.info("MQTT: Conectado ao broker.")
        client.subscribe(TOPIC_READINGS)
        client.subscribe(TOPIC_HEARTBEAT)
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
    except json.JSONDecodeError:
        logging.error(f"MQTT: Payload inválido em {msg.topic}")
        return

    if msg.topic == TOPIC_HEARTBEAT:
        device_id = payload.get("device_id")
        if device_id:
            update_device_last_seen(device_id)
        return

    # --- Processar leitura de sensor ---
    device_id   = payload.get("device_id")
    trip_id     = payload.get("trip_id")
    temperature = payload.get("temperature")
    humidity    = payload.get("humidity")
    latitude    = payload.get("latitude", 0.0)
    longitude   = payload.get("longitude", 0.0)

    # Normaliza timestamp; usa hora do servidor se GPS sem fix
    raw_ts = payload.get("timestamp") or ""
    if not raw_ts or raw_ts.startswith("2000-00-00") or raw_ts.startswith("2000-01-01"):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp = raw_ts.replace("T", " ").replace("Z", "").split(".")[0]

    if None in (device_id, trip_id, temperature, humidity):
        logging.warning("MQTT: Payload incompleto, ignorado.")
        return

    batch_id = get_batch_id_for_trip(trip_id)
    if not batch_id:
        logging.warning(f"MQTT: trip_id={trip_id} não encontrado no banco.")
        return

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

        update_device_last_seen(device_id)
        logging.info(f"MQTT: Leitura gravada — {temperature}°C / {humidity}% (trip {trip_id})")

        # Audit log da leitura recebida
        audit("reading_received", target_table="readings", target_id=reading_id,
              details={"device_id": device_id, "temp": temperature, "humidity": humidity})

    except Exception as e:
        logging.error(f"MQTT: Erro ao gravar leitura: {e}")


def start_mqtt_subscriber():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="flask-subscriber")
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    # TLS — ativar se CA cert estiver configurado
    ca_cert = MQTT_CA_CERT
    if ca_cert and os.path.isfile(ca_cert):
        client.tls_set(ca_certs=ca_cert)
        logging.info(f"MQTT: TLS ativado com CA={ca_cert}")
    else:
        logging.warning("MQTT: CA cert não encontrado — conectando sem TLS (modo dev)")

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever()
    except Exception as e:
        logging.error(f"MQTT: Não foi possível conectar ao broker: {e}")


# -------------------------------------------------------
# Rotas Flask — todas protegidas por @login_required
# -------------------------------------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/trips")
@login_required
def trips():
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT t.trip_id, t.start_time, t.end_time, t.origin, t.destination,
               b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp
        FROM trips t
        JOIN vaccine_batch b ON t.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
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
        SELECT device_id, serial_number, status, last_seen,
               CASE
                 WHEN last_seen IS NULL THEN 'never'
                 WHEN last_seen >= NOW() - INTERVAL 60 SECOND THEN 'online'
                 WHEN last_seen >= NOW() - INTERVAL 5 MINUTE  THEN 'recent'
                 ELSE 'offline'
               END AS connectivity
        FROM devices
        ORDER BY serial_number
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route("/api/status")
@login_required
def status():
    return jsonify({
        "broker_connected":  mqtt_status["connected"],
        "last_mqtt_message": mqtt_status["last_message"],
        "server_time":       datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/audit")
@login_required
@admin_required
def audit_log():
    """Retorna os últimos 200 registros do audit_log (somente admin)."""
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
if __name__ == "__main__":
    t = threading.Thread(target=start_mqtt_subscriber, daemon=True)
    t.start()
    app.run(debug=False, host="0.0.0.0", port=5000)
