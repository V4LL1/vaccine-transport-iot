"""
database.py — Conexão MySQL e funções auxiliares de banco de dados.

Centraliza toda a lógica de acesso ao banco para que as rotas e o
subscriber MQTT não precisem repetir código de conexão/cursor.
"""

import json
import logging

import mysql.connector

from config import DB


def db():
    """Abre e retorna uma nova conexão MySQL. O chamador é responsável por fechar."""
    return mysql.connector.connect(**DB)


def audit(action, target_table=None, target_id=None, details=None, user_id=None, ip=None):
    """Registra uma linha na tabela audit_log.

    Pode ser chamada tanto dentro de uma requisição HTTP (request context)
    quanto da thread MQTT (sem request context). Quando chamada sem ip
    explícito fora de uma requisição, o IP fica NULL sem erro.
    """
    try:
        # Tenta obter o IP da requisição atual; cai para None fora do contexto Flask
        if ip is None:
            try:
                from flask import request as _req
                ip = _req.remote_addr
            except RuntimeError:
                ip = None  # chamada fora de contexto HTTP (ex: thread MQTT)

        conn = db()
        cur  = conn.cursor()
        cur.execute(
            """INSERT INTO audit_log
                   (user_id, action, target_table, target_id, ip_address, details)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                user_id,
                action,
                target_table,
                target_id,
                ip,
                json.dumps(details) if details else None,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.warning(f"Audit log falhou: {e}")


def ensure_device_exists(serial_number):
    """Garante que o dispositivo existe no banco.

    Na primeira mensagem de um serial desconhecido, cria o registro
    com registration_status='pending' para que um admin possa ativá-lo.
    Retorna o dict do dispositivo (novo ou existente).
    """
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM devices WHERE serial_number = %s", (serial_number,))
    device = cur.fetchone()

    if not device:
        cur.execute(
            "INSERT INTO devices (serial_number, registration_status, last_seen)"
            " VALUES (%s, 'pending', NOW())",
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
    """Atualiza devices.last_seen para NOW() pelo serial_number."""
    conn = db()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE devices SET last_seen = NOW() WHERE serial_number = %s",
        (serial_number,)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_active_trip_for_device(device_id):
    """Retorna a viagem em andamento (end_time IS NULL) para o device_id (PK).
    Retorna None se não houver viagem ativa."""
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT trip_id, batch_id FROM trips"
        " WHERE device_id = %s AND end_time IS NULL LIMIT 1",
        (device_id,)
    )
    trip = cur.fetchone()
    cur.close()
    conn.close()
    return trip
