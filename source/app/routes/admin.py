"""
routes/admin.py — Blueprint de administração (admin + superadmin).

Rotas de dispositivos:
  GET  /api/admin/devices/pending              — dispositivos aguardando registro
  POST /api/admin/devices/<id>/register        — registra dispositivo (atribui nome + viagem)
  POST /api/admin/devices/<id>/deactivate      — desativa dispositivo

Rotas de viagens:
  GET  /api/admin/trips                        — lista viagens da empresa
  POST /api/admin/trips                        — cria nova viagem
  POST /api/admin/trips/<id>/close             — encerra viagem em andamento

Rotas de lotes e vacinas:
  GET  /api/admin/batches                      — lotes da empresa
  POST /api/admin/batches                      — cria novo lote
  GET  /api/admin/vaccines                     — catálogo global de vacinas
  POST /api/admin/vaccines                     — cadastra nova vacina

Rotas de empresas (superadmin):
  GET  /api/admin/companies                    — lista empresas
  POST /api/admin/companies                    — cria empresa

Rotas de usuários:
  GET  /api/admin/users                        — lista usuários da empresa
  POST /api/admin/users                        — cria usuário
"""

import logging

import bcrypt
import mysql.connector
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from database import audit, db
from models import company_where, require_permission

admin_bp = Blueprint("admin", __name__)


# ── Dispositivos ───────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/devices/pending")
@login_required
@require_permission("register_device")
def admin_pending_devices():
    """Lista dispositivos que enviaram dados mas ainda não foram registrados por um admin."""
    scope, params = company_where("d")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT d.device_id, d.serial_number, d.last_seen,
               CASE
                 WHEN d.last_seen >= NOW() - INTERVAL 60 SECOND THEN 'online'
                 WHEN d.last_seen >= NOW() - INTERVAL 5 MINUTE  THEN 'recent'
                 ELSE 'offline'
               END AS connectivity
        FROM devices d
        WHERE d.registration_status = 'pending' AND ({scope})
        ORDER BY d.last_seen DESC
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@admin_bp.route("/api/admin/devices/<int:device_id>/register", methods=["POST"])
@login_required
@require_permission("register_device")
def admin_register_device(device_id):
    """Registra um dispositivo pendente: atribui nome, empresa e viagem."""
    body    = request.get_json(force=True)
    name    = body.get("name", "").strip()
    trip_id = body.get("trip_id")

    if not name:
        return jsonify({"error": "Nome do dispositivo obrigatório"}), 400
    if not trip_id:
        return jsonify({"error": "Viagem obrigatória"}), 400

    conn = db()
    cur  = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
    device = cur.fetchone()
    if not device:
        cur.close(); conn.close()
        return jsonify({"error": "Dispositivo não encontrado"}), 404
    if device["registration_status"] == "active":
        cur.close(); conn.close()
        return jsonify({"error": "Dispositivo já está registrado"}), 409

    cur.execute("SELECT * FROM trips WHERE trip_id = %s AND end_time IS NULL", (trip_id,))
    trip = cur.fetchone()
    if not trip:
        cur.close(); conn.close()
        return jsonify({"error": "Viagem não encontrada ou já encerrada"}), 404

    # superadmin mantém empresa atual do dispositivo; admin atribui a própria empresa
    company_id = None if current_user.is_superadmin else current_user.company_id
    cur.execute("""
        UPDATE devices
        SET name                = %s,
            registration_status = 'active',
            status              = 'active',
            registered_by       = %s,
            registered_at       = NOW(),
            company_id          = COALESCE(company_id, %s)
        WHERE device_id = %s
    """, (name, current_user.id, company_id, device_id))

    cur.execute(
        "UPDATE trips SET device_id = %s WHERE trip_id = %s",
        (device_id, trip_id)
    )
    conn.commit()
    cur.close(); conn.close()

    audit("device_registered", target_table="devices", target_id=device_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"name": name, "trip_id": trip_id, "serial": device["serial_number"]})
    logging.info(
        f"Dispositivo {device['serial_number']} registrado como '{name}'"
        f" na viagem {trip_id} por {current_user.name}"
    )
    return jsonify({"message": f"Dispositivo '{name}' registrado com sucesso na viagem {trip_id}"}), 200


@admin_bp.route("/api/admin/devices/<int:device_id>/deactivate", methods=["POST"])
@login_required
@require_permission("deactivate_device")
def admin_deactivate_device(device_id):
    """Marca o dispositivo como inativo e remove-o da viagem em andamento."""
    conn = db()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE devices SET status = 'inactive', registration_status = 'inactive'
        WHERE device_id = %s
    """, (device_id,))
    cur.execute(
        "UPDATE trips SET device_id = NULL WHERE device_id = %s AND end_time IS NULL",
        (device_id,)
    )
    conn.commit()
    cur.close(); conn.close()

    audit("device_deactivated", target_table="devices", target_id=device_id,
          user_id=current_user.id, ip=request.remote_addr)
    return jsonify({"message": "Dispositivo desativado"}), 200


# ── Viagens ────────────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/trips", methods=["GET"])
@login_required
@require_permission("manage_trips")
def admin_trips():
    """Lista todas as viagens da empresa com detalhes de lote, vacina e dispositivo."""
    scope, params = company_where("v")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT t.trip_id, t.start_time, t.end_time, t.origin, t.destination,
               b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp,
               d.serial_number AS device_serial,
               d.name          AS device_name,
               d.registration_status
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


@admin_bp.route("/api/admin/trips", methods=["POST"])
@login_required
@require_permission("create_trip")
def admin_create_trip():
    """Cria nova viagem sem dispositivo (o dispositivo é atribuído no registro)."""
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
    cur.close(); conn.close()

    audit("trip_created", target_table="trips", target_id=trip_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"batch_id": batch_id, "origin": origin, "destination": destination})
    return jsonify({"message": "Viagem criada", "trip_id": trip_id}), 201


@admin_bp.route("/api/admin/trips/<int:trip_id>/close", methods=["POST"])
@login_required
@require_permission("close_trip")
def admin_close_trip(trip_id):
    """Encerra uma viagem em andamento e marca como confirmada."""
    conn = db()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE trips SET end_time = NOW(), received_confirmation = TRUE"
        " WHERE trip_id = %s AND end_time IS NULL",
        (trip_id,)
    )
    conn.commit()
    affected = cur.rowcount
    cur.close(); conn.close()

    if affected == 0:
        return jsonify({"error": "Viagem não encontrada ou já encerrada"}), 404

    audit("trip_closed", target_table="trips", target_id=trip_id,
          user_id=current_user.id, ip=request.remote_addr)
    return jsonify({"message": "Viagem encerrada"}), 200


# ── Lotes e Vacinas ────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/batches", methods=["GET"])
@login_required
@require_permission("create_trip")
def admin_batches():
    """Lista lotes da empresa (usados na criação de viagens)."""
    scope, params = company_where("v")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT b.batch_id, b.batch_code, b.expiration_date, b.quantity_units,
               v.name AS vaccine_name, v.min_temp, v.max_temp
        FROM vaccine_batch b
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        WHERE {scope}
        ORDER BY v.name, b.batch_code
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@admin_bp.route("/api/admin/batches", methods=["POST"])
@login_required
@require_permission("create_trip")
def admin_create_batch():
    """Cria um novo lote para uma vacina existente."""
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

    # Garante que a vacina pertence à empresa do usuário (superadmin ignora essa regra)
    if not current_user.is_superadmin:
        conn = db()
        cur  = conn.cursor()
        cur.execute("SELECT company_id FROM vaccines WHERE vaccine_id = %s", (vaccine_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row or row[0] != current_user.company_id:
            return jsonify({"error": "Produto não pertence à sua empresa"}), 403

    conn = db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO vaccine_batch"
            " (vaccine_id, batch_code, expiration_date, quantity_units)"
            " VALUES (%s, %s, %s, %s)",
            (vaccine_id, batch_code, expiration_date, quantity_units)
        )
        conn.commit()
        batch_id = cur.lastrowid
    except mysql.connector.IntegrityError:
        cur.close(); conn.close()
        return jsonify({"error": f"Código de lote '{batch_code}' já existe"}), 409
    cur.close(); conn.close()

    audit("batch_created", target_table="vaccine_batch", target_id=batch_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"vaccine_id": vaccine_id, "batch_code": batch_code})
    return jsonify({"message": "Lote cadastrado", "batch_id": batch_id}), 201


@admin_bp.route("/api/admin/vaccines", methods=["GET"])
@login_required
@require_permission("manage_users")
def admin_vaccines():
    """Retorna o catálogo global de vacinas (sem filtro de empresa — visível a todos)."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT v.vaccine_id, v.name, v.manufacturer, v.min_temp, v.max_temp,
               c.name AS company_name
        FROM vaccines v
        JOIN companies c ON v.company_id = c.company_id
        ORDER BY v.name
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@admin_bp.route("/api/admin/vaccines", methods=["POST"])
@login_required
@require_permission("manage_users")
def admin_create_vaccine():
    """Cadastra nova vacina. superadmin pode escolher a empresa; admin usa a própria."""
    body         = request.get_json(force=True)
    name         = body.get("name", "").strip()
    manufacturer = body.get("manufacturer", "").strip()
    min_temp     = body.get("min_temp")
    max_temp     = body.get("max_temp")
    company_id   = body.get("company_id") if current_user.is_superadmin else current_user.company_id

    if not name:
        return jsonify({"error": "Nome do produto é obrigatório"}), 400
    if not company_id:
        return jsonify({"error": "Empresa é obrigatória"}), 400
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
        "INSERT INTO vaccines (company_id, name, manufacturer, min_temp, max_temp)"
        " VALUES (%s, %s, %s, %s, %s)",
        (company_id, name, manufacturer or None, min_temp, max_temp)
    )
    conn.commit()
    vaccine_id = cur.lastrowid
    cur.close(); conn.close()

    audit("vaccine_created", target_table="vaccines", target_id=vaccine_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"name": name, "company_id": company_id})
    return jsonify({"message": "Produto cadastrado", "vaccine_id": vaccine_id}), 201


# ── Empresas (superadmin) ──────────────────────────────────────────────────────

@admin_bp.route("/api/admin/companies", methods=["GET"])
@login_required
@require_permission("manage_companies")
def admin_companies():
    """Lista todas as empresas cadastradas (somente superadmin)."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT company_id, name, cnpj, active, created_at FROM companies ORDER BY name")
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@admin_bp.route("/api/admin/companies", methods=["POST"])
@login_required
@require_permission("manage_companies")
def admin_create_company():
    """Cria nova empresa (somente superadmin)."""
    body = request.get_json(force=True)
    name = body.get("name", "").strip()
    cnpj = body.get("cnpj", "").strip() or None

    if not name:
        return jsonify({"error": "Nome da empresa é obrigatório"}), 400

    conn = db()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO companies (name, cnpj) VALUES (%s, %s)", (name, cnpj))
        conn.commit()
        company_id = cur.lastrowid
    except mysql.connector.IntegrityError:
        cur.close(); conn.close()
        return jsonify({"error": "CNPJ já cadastrado"}), 409
    cur.close(); conn.close()

    audit("company_created", target_table="companies", target_id=company_id,
          user_id=current_user.id, ip=request.remote_addr, details={"name": name})
    return jsonify({"message": "Empresa criada", "company_id": company_id}), 201


# ── Usuários ───────────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/users", methods=["GET"])
@login_required
@require_permission("manage_users")
def admin_users():
    """Lista usuários da empresa (admin vê apenas a própria; superadmin vê todos)."""
    scope, params = company_where("u")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT u.user_id, u.name, u.email, u.role, u.created_at,
               c.name AS company_name
        FROM users u
        LEFT JOIN companies c ON u.company_id = c.company_id
        WHERE {scope}
        ORDER BY u.role, u.name
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


@admin_bp.route("/api/admin/users", methods=["POST"])
@login_required
@require_permission("manage_users")
def admin_create_user():
    """Cria novo usuário. superadmin pode escolher empresa e criar admins."""
    body       = request.get_json(force=True)
    name       = body.get("name", "").strip()
    email      = body.get("email", "").strip().lower()
    password   = body.get("password", "").strip()
    role       = body.get("role", "operator")
    company_id = body.get("company_id") if current_user.is_superadmin else current_user.company_id

    if not all([name, email, password]):
        return jsonify({"error": "Nome, email e senha são obrigatórios"}), 400
    if role not in ("admin", "operator"):
        return jsonify({"error": "Role deve ser 'admin' ou 'operator'"}), 400
    if not company_id:
        return jsonify({"error": "Empresa é obrigatória"}), 400

    # Hash bcrypt com fator de custo 12 (seguro contra força bruta)
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

    conn = db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email, password_hash, role, company_id)"
            " VALUES (%s, %s, %s, %s, %s)",
            (name, email, pw_hash, role, company_id)
        )
        conn.commit()
        user_id = cur.lastrowid
    except mysql.connector.IntegrityError:
        cur.close(); conn.close()
        return jsonify({"error": "Email já cadastrado"}), 409
    cur.close(); conn.close()

    audit("user_created", target_table="users", target_id=user_id,
          user_id=current_user.id, ip=request.remote_addr,
          details={"email": email, "role": role, "company_id": company_id})
    return jsonify({"message": "Usuário criado", "user_id": user_id}), 201
