"""
seed_demo.py — Popula o banco com dados ricos para apresentação do TCC.

Execução:
    cd source/database
    ..\..\venv\Scripts\python.exe seed_demo.py
"""

import os
import sys
import random
from datetime import datetime, timedelta

import mysql.connector

# ── Conexão ────────────────────────────────────────────────────────────────────
DB = dict(host="127.0.0.1", port=3306, user="root",
          password="VaccineSecure@2026", database="vaccine_transport")

def conn():
    return mysql.connector.connect(**DB)

# ── Geradores de dados ─────────────────────────────────────────────────────────

def gen_temps(min_t, max_t, n, violation_rate=0.06):
    """Passeio aleatório com reversão à média; ~6% de leituras fora da faixa."""
    mid = (min_t + max_t) / 2
    spread = (max_t - min_t) / 2
    cur = mid + random.uniform(-spread * 0.4, spread * 0.4)
    out = []
    for _ in range(n):
        cur += (mid - cur) * 0.12 + random.gauss(0, spread * 0.18)
        if random.random() < violation_rate:
            cur = (max_t + random.uniform(0.3, 1.8)) if random.random() < 0.5 \
                  else (min_t - random.uniform(0.3, 1.8))
        out.append(round(cur, 2))
    return out

def gen_humidity(n, cold=False):
    """Umidade: ~35% em ultracongelados, ~55% em refrigerados."""
    base = 35 if cold else 55
    return [round(max(10, min(95, random.gauss(base, 4))), 2) for _ in range(n)]

def gen_gps(lat0, lon0, lat1, lon1, n, noise=0.0015):
    """Interpolação linear com ruído Gaussiano."""
    lats, lons = [], []
    for i in range(n):
        t = i / max(n - 1, 1)
        lats.append(round(lat0 + (lat1 - lat0) * t + random.gauss(0, noise), 7))
        lons.append(round(lon0 + (lon1 - lon0) * t + random.gauss(0, noise), 7))
    return lats, lons

def readings_for_trip(trip_id, batch_id, min_t, max_t,
                      start_dt, end_dt, lat0, lon0, lat1, lon1,
                      interval_min=15):
    """Gera leituras de 15 em 15 minutos entre start_dt e end_dt."""
    cold = max_t <= 0
    rows = []
    ts = start_dt
    pts = []
    while ts <= end_dt:
        pts.append(ts)
        ts += timedelta(minutes=interval_min)
    if not pts:
        return rows
    temps = gen_temps(min_t, max_t, len(pts))
    hums  = gen_humidity(len(pts), cold=cold)
    lats, lons = gen_gps(lat0, lon0, lat1, lon1, len(pts))
    for i, ts in enumerate(pts):
        rows.append((trip_id, batch_id, ts, temps[i], hums[i], lats[i], lons[i]))
    return rows

# ── Dados de referência ────────────────────────────────────────────────────────

VACCINES = [
    # (company_id, nome, fabricante, min_temp, max_temp)
    # ── PharmaTransport (1) ──
    (1, "Comirnaty",                  "Pfizer / BioNTech",    -90.0, -60.0),
    (1, "Spikevax",                   "Moderna",              -25.0, -15.0),
    (1, "Spikevax Bivalente",         "Moderna",              -50.0, -15.0),
    (1, "Varivax",                    "MSD",                  -50.0, -15.0),
    (1, "OPV Sabin",                  "Bio-Manguinhos",       -20.0, -15.0),
    (1, "Vaxzevria",                  "AstraZeneca",            2.0,   8.0),
    (1, "Fluzone Quadrivalente",      "Sanofi Pasteur",         2.0,   8.0),
    (1, "Gardasil 9",                 "MSD",                    2.0,   8.0),
    (1, "Rotarix",                    "GSK",                    2.0,   8.0),
    (1, "Priorix (MMR)",              "GSK",                    2.0,   8.0),
    (1, "Bexsero",                    "GSK",                    2.0,   8.0),
    (1, "Prevenar 13",                "Pfizer",                 2.0,   8.0),
    (1, "Stamaril (Febre Amarela)",   "Sanofi Pasteur",         2.0,   8.0),
    # ── BioFrio (2) ──
    (2, "Humira (Adalimumabe)",       "AbbVie",                 2.0,   8.0),
    (2, "Enbrel (Etanercepte)",       "Amgen / Pfizer",         2.0,   8.0),
    (2, "Lantus SoloStar (Insulina)", "Sanofi",                 2.0,   8.0),
    (2, "Herceptin (Trastuzumabe)",   "Roche",                  2.0,   8.0),
    (2, "Remicade (Infliximabe)",     "Janssen / J&J",          2.0,   8.0),
    (2, "Neupogen (Filgrastim)",      "Amgen",                  2.0,   8.0),
    (2, "Koate (Fator VIII)",         "CSL Behring",            2.0,   8.0),
    (2, "Epogen (Epoetina alfa)",     "Amgen",                  2.0,   8.0),
    (2, "Humatrope (Somatropina)",    "Eli Lilly",              2.0,   8.0),
    (2, "Avastin (Bevacizumabe)",     "Roche",                  2.0,   8.0),
    (2, "CoronaVac",                  "Sinovac",                2.0,   8.0),
    (2, "Janssen COVID-19",           "Johnson & Johnson",      2.0,   8.0),
]

# Lotes: (vaccine_index_0based, batch_code, expiry, qty)
BATCHES = [
    # Comirnaty (0)
    (0,  "CMR-2026-EU001", "2026-11-30", 3200),
    (0,  "CMR-2026-US001", "2027-01-15", 2800),
    # Spikevax (1)
    (1,  "SPK-2026-BR001", "2026-12-31", 4500),
    (1,  "SPK-2027-BR001", "2027-03-20", 3800),
    # Spikevax Bivalente (2)
    (2,  "SPB-2026-BR001", "2026-10-10", 2500),
    # Varivax (3)
    (3,  "VRX-2026-US001", "2027-02-28", 1800),
    # OPV Sabin (4)
    (4,  "OPV-2026-BR001", "2026-09-15", 6000),
    (4,  "OPV-2026-AF001", "2026-08-31", 9000),
    # Vaxzevria (5)
    (5,  "AZN-2026-BR001", "2026-07-20", 5000),
    (5,  "AZN-2026-AR001", "2026-09-30", 4200),
    # Fluzone (6)
    (6,  "FLZ-2026-BR001", "2026-06-30", 7500),
    (6,  "FLZ-2026-US001", "2026-11-30", 6200),
    # Gardasil 9 (7)
    (7,  "GRD-2026-BR001", "2027-04-15", 3000),
    # Rotarix (8)
    (8,  "RTX-2026-BR001", "2026-08-10", 4800),
    # Priorix (9)
    (9,  "PRX-2026-EU001", "2026-12-20", 3500),
    # Bexsero (10)
    (10, "BXS-2026-EU001", "2027-01-31", 2200),
    # Prevenar 13 (11)
    (11, "PNV-2026-BR001", "2026-10-25", 5500),
    (11, "PNV-2027-BR001", "2027-02-28", 4800),
    # Stamaril (12)
    (12, "STM-2026-BR001", "2026-09-01", 3200),
    # Humira (13)
    (13, "HUM-2026-BR001", "2026-11-15", 1200),
    (13, "HUM-2026-EU001", "2026-12-31", 1500),
    # Enbrel (14)
    (14, "ENB-2026-BR001", "2026-10-31", 900),
    # Lantus (15)
    (15, "LNT-2026-BR001", "2027-01-20", 8000),
    (15, "LNT-2026-AR001", "2026-12-15", 6500),
    # Herceptin (16)
    (16, "HCP-2026-BR001", "2027-03-31", 600),
    # Remicade (17)
    (17, "RMC-2026-BR001", "2026-11-30", 750),
    (17, "RMC-2026-EU001", "2027-02-15", 800),
    # Neupogen (18)
    (18, "NPG-2026-BR001", "2026-09-20", 2200),
    # Koate Fator VIII (19)
    (19, "KOT-2026-BR001", "2026-08-31", 400),
    # Epogen (20)
    (20, "EPG-2026-BR001", "2027-01-10", 1800),
    # Humatrope (21)
    (21, "HMT-2026-BR001", "2026-10-30", 550),
    # Avastin (22)
    (22, "AVS-2026-BR001", "2026-12-05", 480),
    # CoronaVac (23)
    (23, "CRV-2026-BR001", "2026-07-31", 12000),
    (23, "CRV-2026-MX001", "2026-09-15", 9500),
    # Janssen (24)
    (24, "JNS-2026-BR001", "2026-08-20", 7000),
    (24, "JNS-2026-CO001", "2026-10-01", 5500),
]

# Rastreamentos:
# (batch_idx, origem, destino, start_offset_days, duration_hours,
#  lat0, lon0, lat1, lon1, gen_readings)
# start_offset_days: dias atrás a partir de hoje
# duration_hours: None = ativo (sem end_time)
NOW = datetime.utcnow()

TRIPS = [
    # ── PharmaTransport (lotes 0-18) ──────────────────────────────────────────
    # Fechados
    dict(b=0,  org="Frankfurt, Alemanha",           dst="Paris, França",
         off=30, dur=8,    lat0=50.1109, lon0=8.6821,  lat1=48.8566, lon1=2.3522),
    dict(b=1,  org="Aeroporto Guarulhos, SP",       dst="Hospital das Clínicas, SP",
         off=20, dur=6,    lat0=-23.4356,lon0=-46.4731, lat1=-23.5594,lon1=-46.6696),
    dict(b=3,  org="Miami, EUA",                    dst="New York, EUA",
         off=18, dur=24,   lat0=25.7617, lon0=-80.1918, lat1=40.7128, lon1=-74.0060),
    dict(b=5,  org="São Paulo, SP",                 dst="Buenos Aires, Argentina",
         off=15, dur=18,   lat0=-23.5505,lon0=-46.6333, lat1=-34.6037,lon1=-58.3816),
    dict(b=6,  org="Singapore",                     dst="Tokyo, Japão",
         off=12, dur=30,   lat0=1.3521,  lon0=103.8198, lat1=35.6762, lon1=139.6503),
    dict(b=7,  org="São Paulo, SP",                 dst="Lima, Peru",
         off=10, dur=14,   lat0=-23.5505,lon0=-46.6333, lat1=-12.0464,lon1=-77.0428),
    dict(b=8,  org="London, Reino Unido",            dst="Amsterdam, Holanda",
         off=8,  dur=6,    lat0=51.5074, lon0=-0.1278,  lat1=52.3676, lon1=4.9041),
    dict(b=9,  org="São Paulo, SP",                 dst="Santiago, Chile",
         off=6,  dur=12,   lat0=-23.5505,lon0=-46.6333, lat1=-33.4489,lon1=-70.6693),
    dict(b=11, org="Toronto, Canadá",               dst="Montréal, Canadá",
         off=5,  dur=8,    lat0=43.6532, lon0=-79.3832, lat1=45.5017, lon1=-73.5673),
    dict(b=12, org="Armazém Central BioFrio — SP",  dst="Armazém Central BioFrio — SP",
         off=4,  dur=72,   lat0=-23.5505,lon0=-46.6333, lat1=-23.5505,lon1=-46.6333),
    dict(b=13, org="Madrid, Espanha",               dst="Lisboa, Portugal",
         off=3,  dur=10,   lat0=40.4168, lon0=-3.7038,  lat1=38.7223, lon1=-9.1393),
    dict(b=14, org="Mumbai, Índia",                 dst="Nova Delhi, Índia",
         off=2,  dur=16,   lat0=19.0760, lon0=72.8777,  lat1=28.6139, lon1=77.2090),
    # Ativos (PharmaTransport)
    dict(b=2,  org="Aeroporto Guarulhos, SP",       dst="Manaus, AM",
         off=1,  dur=None, lat0=-23.4356,lon0=-46.4731, lat1=-3.1190, lon1=-60.0217),
    dict(b=4,  org="Câmara Fria PharmaTrack — SP",  dst="Câmara Fria PharmaTrack — SP",
         off=0,  dur=None, lat0=-23.5505,lon0=-46.6333, lat1=-23.5505,lon1=-46.6333),

    # ── BioFrio (lotes 19-35) ──────────────────────────────────────────────────
    # Fechados
    dict(b=19, org="São Paulo, SP",                 dst="Rio de Janeiro, RJ",
         off=28, dur=6,    lat0=-23.5505,lon0=-46.6333, lat1=-22.9068,lon1=-43.1729),
    dict(b=20, org="Dubai, Emirados",               dst="Riyadh, Arábia Saudita",
         off=25, dur=5,    lat0=25.2048, lon0=55.2708,  lat1=24.7136, lon1=46.6753),
    dict(b=21, org="Johannesburgo, África do Sul",  dst="Nairóbi, Quênia",
         off=22, dur=20,   lat0=-26.2041,lon0=28.0473,  lat1=-1.2921, lon1=36.8219),
    dict(b=22, org="São Paulo, SP",                 dst="Bogotá, Colômbia",
         off=19, dur=12,   lat0=-23.5505,lon0=-46.6333, lat1=4.7110,  lon1=-74.0721),
    dict(b=23, org="Sydney, Austrália",             dst="Melbourne, Austrália",
         off=16, dur=8,    lat0=-33.8688,lon0=151.2093, lat1=-37.8136,lon1=144.9631),
    dict(b=24, org="Chicago, EUA",                  dst="Los Angeles, EUA",
         off=14, dur=20,   lat0=41.8781, lon0=-87.6298, lat1=34.0522, lon1=-118.2437),
    dict(b=25, org="Recife, PE",                    dst="Fortaleza, CE",
         off=11, dur=10,   lat0=-8.0476, lon0=-34.8770, lat1=-3.7172, lon1=-38.5434),
    dict(b=26, org="Warsaw, Polônia",               dst="Vienna, Áustria",
         off=9,  dur=12,   lat0=52.2297, lon0=21.0122,  lat1=48.2082, lon1=16.3738),
    dict(b=27, org="Hong Kong",                     dst="Xangai, China",
         off=7,  dur=10,   lat0=22.3193, lon0=114.1694, lat1=31.2304, lon1=121.4737),
    dict(b=28, org="Porto Alegre, RS",              dst="Florianópolis, SC",
         off=4,  dur=4,    lat0=-30.0277,lon0=-51.2287, lat1=-27.5954,lon1=-48.5480),
    dict(b=29, org="Armazém BioFrio — RJ",          dst="Armazém BioFrio — RJ",
         off=2,  dur=96,   lat0=-22.9068,lon0=-43.1729, lat1=-22.9068,lon1=-43.1729),
    dict(b=30, org="Manaus, AM",                    dst="Belém, PA",
         off=1,  dur=24,   lat0=-3.1190, lon0=-60.0217, lat1=-1.4558, lon1=-48.5044),
    # Ativos (BioFrio)
    dict(b=31, org="Rio de Janeiro, RJ",            dst="Salvador, BA",
         off=0,  dur=None, lat0=-22.9068,lon0=-43.1729, lat1=-12.9714,lon1=-38.5014),
    dict(b=32, org="Câmara Fria BioFrio — MG",      dst="Câmara Fria BioFrio — MG",
         off=0,  dur=None, lat0=-19.9167,lon0=-43.9345, lat1=-19.9167,lon1=-43.9345),
]

# ── Script principal ────────────────────────────────────────────────────────────

def main():
    c = conn()
    cur = c.cursor()

    print("Conectado ao MySQL. Iniciando seed de demonstração...")

    # Desliga foreign key checks temporariamente
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")

    # 1. Limpar dados (ordem: readings → trips → batches → vaccines → devices)
    print("  Limpando dados antigos...")
    cur.execute("DELETE FROM readings")
    cur.execute("DELETE FROM trips")
    cur.execute("DELETE FROM vaccine_batch")
    cur.execute("DELETE FROM vaccines")
    cur.execute("DELETE FROM seen_nonces")
    # Devices: apaga todos exceto ESP32-B0A732D765D0
    cur.execute("DELETE FROM devices WHERE serial_number != 'ESP32-B0A732D765D0'")
    # Garante que o ESP32 está ativo e pendente (sem viagem ativa)
    cur.execute("""
        UPDATE devices
        SET registration_status = 'pending', status = 'active', company_id = 1
        WHERE serial_number = 'ESP32-B0A732D765D0'
    """)

    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    c.commit()

    # 2. Inserir vacinas/produtos
    print("  Inserindo produtos farmacêuticos...")
    vaccine_ids = []
    for v in VACCINES:
        cur.execute(
            "INSERT INTO vaccines (company_id, name, manufacturer, min_temp, max_temp)"
            " VALUES (%s, %s, %s, %s, %s)",
            v
        )
        vaccine_ids.append(cur.lastrowid)
    c.commit()
    print(f"    {len(vaccine_ids)} produtos inseridos.")

    # 3. Inserir lotes
    print("  Inserindo lotes...")
    batch_ids = []
    for b in BATCHES:
        vid = vaccine_ids[b[0]]
        cur.execute(
            "INSERT INTO vaccine_batch (vaccine_id, batch_code, expiration_date, quantity_units)"
            " VALUES (%s, %s, %s, %s)",
            (vid, b[1], b[2], b[3])
        )
        batch_ids.append(cur.lastrowid)
    c.commit()
    print(f"    {len(batch_ids)} lotes inseridos.")

    # Descobre device_id do ESP32 que ficou
    cur.execute("SELECT device_id FROM devices WHERE serial_number = 'ESP32-B0A732D765D0'")
    row = cur.fetchone()
    esp32_id = row[0] if row else None
    print(f"  ESP32-B0A732D765D0 -> device_id={esp32_id}")

    # 4. Inserir rastreamentos
    print("  Inserindo rastreamentos...")
    trip_ids = []
    for t in TRIPS:
        bidx = t["b"]
        if bidx >= len(batch_ids):
            print(f"    AVISO: batch_idx {bidx} fora do range — pulando.")
            trip_ids.append(None)
            continue

        start_dt = NOW - timedelta(days=t["off"], hours=random.randint(0, 3))
        end_dt   = None
        if t["dur"] is not None:
            end_dt = start_dt + timedelta(hours=t["dur"])
            # Não deixa end_time no futuro
            if end_dt > NOW:
                end_dt = NOW - timedelta(minutes=30)

        cur.execute(
            "INSERT INTO trips (batch_id, device_id, start_time, end_time,"
            " origin, destination, received_confirmation) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (batch_ids[bidx], None, start_dt, end_dt, t["org"], t["dst"],
             True if end_dt else False)
        )
        trip_ids.append(cur.lastrowid)

    c.commit()
    print(f"    {sum(1 for x in trip_ids if x)} rastreamentos inseridos.")

    # Vincula o ESP32 ao primeiro rastreamento ativo da PharmaTransport
    # (índice 12 na lista TRIPS — "Aeroporto Guarulhos → Manaus")
    esp32_trip_idx = 12
    if esp32_id and trip_ids[esp32_trip_idx]:
        cur.execute(
            "UPDATE trips SET device_id = %s WHERE trip_id = %s",
            (esp32_id, trip_ids[esp32_trip_idx])
        )
        cur.execute(
            "UPDATE devices SET registration_status='active', status='active'"
            " WHERE device_id = %s", (esp32_id,)
        )
        c.commit()
        print(f"  ESP32 vinculado ao rastreamento #{trip_ids[esp32_trip_idx]}"
              f" ({TRIPS[esp32_trip_idx]['org']} -> {TRIPS[esp32_trip_idx]['dst']})")

    # 5. Gerar leituras para rastreamentos fechados
    print("  Gerando leituras para rastreamentos históricos...")
    total_readings = 0
    for i, t in enumerate(TRIPS):
        tid = trip_ids[i]
        if tid is None or t["dur"] is None:
            continue  # Pula ativos e inválidos

        bidx = t["b"]
        if bidx >= len(batch_ids):
            continue

        # Descobre min/max_temp do produto via lote
        vac_idx = BATCHES[bidx][0]
        min_t, max_t = VACCINES[vac_idx][3], VACCINES[vac_idx][4]

        start_dt = NOW - timedelta(days=t["off"], hours=1)
        end_dt   = start_dt + timedelta(hours=t["dur"])
        if end_dt > NOW:
            end_dt = NOW - timedelta(minutes=30)

        rows = readings_for_trip(
            tid, batch_ids[bidx], min_t, max_t,
            start_dt, end_dt,
            t["lat0"], t["lon0"], t["lat1"], t["lon1"],
            interval_min=15
        )

        if rows:
            cur.executemany(
                "INSERT INTO readings (trip_id, batch_id, timestamp, temperature,"
                " humidity, latitude, longitude) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                rows
            )
            total_readings += len(rows)

    c.commit()
    cur.close()
    c.close()

    print(f"  {total_readings} leituras geradas.")
    print()
    print("=" * 55)
    print("  SEED CONCLUÍDO COM SUCESSO!")
    print(f"  Produtos:       {len(vaccine_ids)}")
    print(f"  Lotes:          {len(batch_ids)}")
    print(f"  Rastreamentos:  {sum(1 for x in trip_ids if x)}")
    print(f"  Leituras:       {total_readings}")
    print("=" * 55)

if __name__ == "__main__":
    main()
