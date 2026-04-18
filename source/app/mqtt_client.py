"""
mqtt_client.py — Subscriber MQTT que roda em thread separada.

Fluxo de uma mensagem de leitura (vaccines/readings):
  1. Verifica HMAC-SHA256 — rejeita e registra no audit_log se inválido
  2. Auto-descobre o dispositivo (cria registro 'pending' se novo)
  3. Descarta se o dispositivo não estiver ativo (aguardando registro pelo admin)
  4. Busca a viagem em andamento para o dispositivo
  5. Persiste a leitura em readings e registra no audit_log

Heartbeat (vaccines/heartbeat): apenas atualiza devices.last_seen.
"""

import hashlib
import hmac as _hmac   # alias para evitar conflito com a função audit() se houver
import json
import logging
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from config import (
    HMAC_KEY,
    MQTT_BROKER, MQTT_CA_CERT, MQTT_PASSWORD, MQTT_PORT, MQTT_USERNAME,
    TOPIC_HEARTBEAT, TOPIC_READINGS,
)
from database import (
    audit, db,
    ensure_device_exists, get_active_trip_for_device, update_device_last_seen,
)

# Estado compartilhado: mutado pelos callbacks MQTT, lido pelo endpoint /api/status
mqtt_status = {"connected": False, "last_message": None}

# Buffer circular com os últimos 200 eventos MQTT — consumido pelo tab de Debug
_log_lock      = threading.Lock()
mqtt_event_log = deque(maxlen=200)


def _log_event(level: str, msg: str, data: dict = None):
    """Append um evento ao log em memória (thread-safe).
    level: 'info' | 'warn' | 'security' | 'error'
    """
    with _log_lock:
        mqtt_event_log.appendleft({
            "ts":    datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "ts_iso": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "msg":   msg,
            "data":  data or {},
        })


# ── Callbacks paho-mqtt ────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, reason_code, properties):
    """Chamado quando o cliente se conecta (ou reconecta) ao broker."""
    if reason_code == 0:
        mqtt_status["connected"] = True
        logging.info("MQTT: Conectado ao broker.")
        client.subscribe(TOPIC_READINGS,  qos=1)
        client.subscribe(TOPIC_HEARTBEAT, qos=1)
        _log_event("info", f"Conectado ao broker {MQTT_BROKER}:{MQTT_PORT} (TLS ativo)")
    else:
        mqtt_status["connected"] = False
        logging.warning(f"MQTT: Falha na conexão (rc={reason_code})")
        _log_event("error", f"Falha na conexão ao broker (rc={reason_code})")


def on_disconnect(client, userdata, flags, reason_code, properties):
    """Chamado quando a conexão com o broker é perdida."""
    mqtt_status["connected"] = False
    logging.warning("MQTT: Desconectado do broker.")
    _log_event("warn", "Desconectado do broker — aguardando reconexão automática")


def on_message(client, userdata, msg):
    """Processa cada mensagem recebida: valida HMAC e persiste a leitura."""
    mqtt_status["last_message"] = datetime.now(timezone.utc).isoformat()

    # Deserializa o payload JSON
    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        logging.warning(f"MQTT: Payload descartado (JSON inválido/truncado) em {msg.topic}")
        return

    device_serial = payload.get("device_id")
    if not device_serial:
        return

    # ── Heartbeat: sem dados críticos, apenas atualiza presença ──────────────
    if msg.topic == TOPIC_HEARTBEAT:
        ensure_device_exists(device_serial)
        update_device_last_seen(device_serial)
        _log_event("info", f"Heartbeat — {device_serial}", {"device": device_serial})
        return

    # ── Verificação HMAC-SHA256 ──────────────────────────────────────────────
    # O ESP32 serializa o payload sem o campo 'hmac' no campo 'signed',
    # calcula HMAC-SHA256 sobre essa string e anexa ambos ao JSON final.
    received_hmac = payload.get("hmac", "")
    signed_text   = payload.get("signed", "")

    if received_hmac and signed_text:
        expected_hmac = _hmac.new(
            HMAC_KEY.encode(), signed_text.encode(), hashlib.sha256
        ).hexdigest()

        if not _hmac.compare_digest(received_hmac, expected_hmac):
            logging.warning(f"MQTT: HMAC inválido de [{device_serial}] — mensagem rejeitada.")
            audit("hmac_failed", details={"device_id": device_serial})
            _log_event("security",
                       f"⚠ HMAC inválido — mensagem de [{device_serial}] REJEITADA",
                       {"device": device_serial, "received": received_hmac[:16] + "…"})
            return

        logging.debug(f"MQTT: HMAC verificado OK [{device_serial}]")
        _log_event("info", f"HMAC verificado ✓ — {device_serial}", {"device": device_serial})
    else:
        # Modo de compatibilidade: aceita mensagens sem HMAC (ex.: desenvolvimento)
        logging.warning(
            f"MQTT: Mensagem sem HMAC/signed de [{device_serial}] — aceita (modo compatibilidade)."
        )
        _log_event("warn", f"Sem HMAC — {device_serial} (modo compatibilidade)", {"device": device_serial})

    # ── Persistência da leitura ──────────────────────────────────────────────

    # 1. Garante que o dispositivo existe no banco (cria 'pending' se novo)
    device = ensure_device_exists(device_serial)
    update_device_last_seen(device_serial)

    # 2. Apenas dispositivos ativos (registrados por um admin) geram leituras
    if device.get("registration_status") != "active":
        logging.info(f"MQTT: Leitura de dispositivo pendente [{device_serial}] — aguardando registro.")
        _log_event("warn", f"Dispositivo pendente — {device_serial} aguarda registro pelo admin",
                   {"device": device_serial})
        return

    # 3. Leituras só são gravadas se houver uma viagem em andamento
    active_trip = get_active_trip_for_device(device["device_id"])
    if not active_trip:
        logging.warning(f"MQTT: Dispositivo [{device_serial}] ativo mas sem viagem em andamento.")
        _log_event("warn", f"Sem viagem ativa — {device_serial} ignorado", {"device": device_serial})
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

    # Normaliza o timestamp GPS; usa relógio do servidor se o GPS não tem fix
    # (GPS sem fix costuma enviar ano < 2020 ou campos zerados)
    raw_ts    = payload.get("timestamp") or ""
    timestamp = None
    if raw_ts:
        normalized = raw_ts.replace("T", " ").replace("Z", "").split(".")[0]
        try:
            parsed = datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S")
            if parsed.year >= 2020 and parsed.month >= 1 and parsed.day >= 1:
                timestamp = normalized
        except ValueError:
            pass
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # 4. Grava a leitura no banco
    try:
        conn = db()
        cur  = conn.cursor()
        cur.execute(
            """INSERT INTO readings
                   (trip_id, batch_id, timestamp, temperature, humidity, latitude, longitude)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (trip_id, batch_id, timestamp, temperature, humidity,
             latitude  if latitude  else None,
             longitude if longitude else None)
        )
        reading_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()

        logging.info(
            f"MQTT: Leitura gravada — {temperature}°C / {humidity}%"
            f" (device={device_serial}, trip={trip_id})"
        )
        _log_event("info",
                   f"Leitura gravada — {temperature}°C / {humidity}%  [{device_serial}]",
                   {"device": device_serial, "temp": temperature,
                    "humidity": humidity, "trip_id": trip_id, "lat": latitude, "lng": longitude})
        audit("reading_received", target_table="readings", target_id=reading_id,
              details={"device_id": device_serial, "temp": temperature,
                       "humidity": humidity, "trip_id": trip_id})

    except Exception as e:
        logging.error(f"MQTT: Erro ao gravar leitura: {e}")


# ── Thread de conexão ao broker ────────────────────────────────────────────────

def start_mqtt_subscriber():
    """Conecta ao broker e bloqueia em loop_forever(). Executado em daemon thread.

    clean_session=False: sessão persistente — o broker enfileira mensagens
    QoS 1 enquanto o cliente estiver offline e as entrega ao reconectar.
    paho gerencia reconexões automaticamente via reconnect_delay_set().
    """
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="flask-subscriber",
        clean_session=False,
    )
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    # Resolve o caminho do CA cert relativo ao diretório deste arquivo
    ca_cert = MQTT_CA_CERT
    if ca_cert and not os.path.isabs(ca_cert):
        ca_cert = os.path.join(os.path.dirname(os.path.abspath(__file__)), ca_cert)

    if ca_cert and os.path.isfile(ca_cert):
        client.tls_set(ca_certs=ca_cert)
        logging.info(f"MQTT: TLS ativado com CA={ca_cert}")
    else:
        # Usa o CA store do sistema (funciona com HiveMQ Cloud / Let's Encrypt)
        client.tls_set()
        logging.info("MQTT: TLS ativado via CA store do sistema")

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # paho aguarda entre 5s e 60s entre tentativas automáticas de reconexão
    client.reconnect_delay_set(min_delay=5, max_delay=60)

    # Loop externo: cobre o caso em que connect() em si lança exceção
    # antes de loop_forever() assumir o controle
    retry_delay = 5
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()   # bloqueia; paho cuida das reconexões
        except Exception as e:
            logging.error(f"MQTT: Conexão falhou: {e}. Tentando em {retry_delay}s...")
        mqtt_status["connected"] = False
        time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)
