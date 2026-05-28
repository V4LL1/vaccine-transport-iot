# TCC — PharmaTrack IoT: Sistema Seguro de Monitoramento de Transporte Farmacêutico
## Contexto do Projeto

Sistema IoT seguro para monitoramento de transporte de vacinas e medicamentos. TCC de Engenharia da Computação.
Arquitetura em 4 pilares: **Percepção** (ESP32 + sensores) → **Conectividade** (MQTT) → **Análise** (Flask + MySQL) → **Ação** (dashboard + alertas).

**Nome do sistema**: PharmaTrack IoT
**Tech stack:** ESP32 (Arduino), Mosquitto MQTT / HiveMQ Cloud, Python Flask, MySQL, Leaflet.js, Chart.js

---

## Arquivos Críticos

| Arquivo | Função |
|---|---|
| `source/esp32/main/main.ino` | Firmware ESP32 — sensores + MQTT |
| `source/app/app.py` | Backend Flask — criação dos blueprints + subscriber MQTT |
| `source/app/routes/dashboard.py` | Blueprint dashboard — APIs de leitura e páginas |
| `source/app/routes/admin.py` | Blueprint admin — gestão de dispositivos, rastreamentos, usuários |
| `source/app/routes/auth.py` | Blueprint auth — login, logout, TOTP |
| `source/app/routes/debug.py` | Blueprint debug — publicação manual de payloads (dev) |
| `source/app/templates/index.html` | Dashboard web (SPA) |
| `source/app/templates/trip_readings.html` | Página de detalhes de rastreamento |
| `source/app/templates/login.html` | Tela de login |
| `source/app/templates/setup_totp.html` | Setup do MFA |
| `source/app/templates/verify_totp.html` | Verificação do código TOTP |
| `source/database/db_script.sql` | Schema completo do banco |
| `source/database/seed_demo.py` | Seed com dados ricos para demonstração |
| `source/broker/mosquitto.conf` | Config Mosquitto (M1, sem TLS, porta 1883) |
| `source/broker/mosquitto-tls.conf` | Config Mosquitto TLS (porta 8883) |
| `source/app/requirements.txt` | Dependências Python |
| `PROGRESSO.md` | Log detalhado de implementação por milestone |

---

## Como subir o ambiente (após reinicialização)

```bash
# 1. MySQL (sem serviço Windows — iniciar manualmente)
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --datadir="C:/Users/guilh/mysql-data" --port=3306

# 2. Mosquitto (TLS — porta 8883)  ← opcional, sistema usa HiveMQ Cloud em produção
"C:\Program Files\mosquitto\mosquitto.exe" -c source/broker/mosquitto-tls.conf

# 3. Flask
cd source/app
../../venv/Scripts/python.exe app.py
```

---

## Estrutura da Aplicação Flask (Blueprints)

```
app.py                        ← fábrica da aplicação, registra blueprints, inicia MQTT thread
routes/
  auth.py      (auth_bp)      ← GET/POST /login, GET /logout, GET /setup-totp, POST /verify-totp
  dashboard.py (dashboard_bp) ← GET /, GET /trips/<id>/readings, GET /api/*
  admin.py     (admin_bp)     ← POST /api/admin/* (gestão de devices, trips, users, vaccines)
  debug.py     (debug_bp)     ← GET /debug, POST /debug/publish (somente admin, dev)
models.py                     ← User (Flask-Login), require_permission(), company_where()
config.py                     ← PERMISSIONS dict por role
mqtt_client.py                ← subscriber paho-mqtt, on_message, on_connect, mqtt_status dict
database.py                   ← db() helper → mysql.connector.connect()
```

### APIs principais (dashboard_bp)

| Endpoint | Função |
|---|---|
| `GET /api/trips` | Lista rastreamentos da empresa (scoped) |
| `GET /api/readings/<trip_id>` | Leituras de um rastreamento |
| `GET /api/readings/recent` | Últimas 20 leituras da empresa |
| `GET /api/alarms` | Violações de temperatura (50 mais recentes) |
| `GET /api/devices` | Dispositivos com status de conectividade |
| `GET /api/map/all` | Todos os rastreamentos GPS amostrados (≤40 pts/trip) para mapa combinado |
| `GET /api/alerts/poll` | Alertas novos para toast (polling ~10s) |
| `GET /api/status` | Estado conexão MQTT + server_time |
| `GET /api/audit` | Log de auditoria (admin/superadmin) |

### APIs principais (admin_bp)

| Endpoint | Função |
|---|---|
| `POST /api/admin/devices/<id>/register` | Registra dispositivo pending → active |
| `POST /api/admin/devices/<id>/deactivate` | Desativa dispositivo |
| `POST /api/admin/devices/<id>/detach` | Desatrela dispositivo de rastreamento(s) |
| `POST /api/admin/trips` | Cria novo rastreamento |
| `POST /api/admin/trips/<id>/close` | Encerra rastreamento |
| `POST /api/admin/vaccines` | Cadastra novo produto farmacêutico |
| `POST /api/admin/batches` | Cadastra novo lote |
| `GET /api/admin/users` | Lista usuários da empresa |
| `POST /api/admin/users` | Cria novo usuário |

---

## Modelo de Dados

### Multi-tenancy
- Duas empresas: **PharmaTransport** (company_id=1) e **BioFrio** (company_id=2)
- Roles: `superadmin` (acesso total), `admin` (empresa), `operator` (somente leitura)
- Scoping via `company_where(alias)` em todas as queries — superadmin vê tudo

### Tabelas
```
companies ──< users
vaccines ──< vaccine_batch ──< trips ──< readings
                               trips >── devices ──< companies
audit_log, seen_nonces
```

### Ciclo de vida de dispositivos
```
pending (auto-descoberto) → active (registrado) → inactive (desativado)
                                    ↕ detach/re-register
```

---

## Dados de Demonstração (seed_demo.py)

Estado atual do banco após execução de `seed_demo.py`:

| | PharmaTransport | BioFrio | Total |
|---|---|---|---|
| Produtos | 13 | 12 | 25 |
| Lotes | ~18 | ~18 | 36 |
| Rastreamentos | ~15 | ~13 | 28 |
| Leituras | ~900 | ~740 | ~1638 |

**Dispositivo ativo**: `ESP32-B0A732D765D0` (PharmaTransport)
- Associado ao rastreamento: Guarulhos → Manaus (em andamento)

---

## Roadmap de Implementação

### ✅ M1 — Pipeline MQTT Funcional (concluído 2026-03-12)

- [x] **ESP32 firmware completo**
  - [x] WiFi com reconexão automática
  - [x] MQTT via PubSubClient (porta 1883 → migrado para 8883)
  - [x] Payload JSON com ArduinoJson (temp, humidity, GPS, timestamp UTC)
  - [x] Publicação a cada 5s + heartbeat a cada 30s
  - [x] Campos `hmac` e `nonce` presentes (vazios — prontos para M2)
- [x] **Flask backend**
  - [x] Thread subscriber paho-mqtt (API v2)
  - [x] Gravar leituras no MySQL via on_message
  - [x] Atualizar `devices.last_seen` por heartbeat
  - [x] Endpoint `/api/alarms` — violações de temperatura
  - [x] Endpoint `/api/devices` — status online/offline
  - [x] Endpoint `/api/status` — estado do broker
- [x] **Dashboard**
  - [x] Refresh automático a cada 10s
  - [x] Badge MQTT (verde/vermelho)
  - [x] Painel de alarmes de temperatura
  - [x] Status online/offline dos dispositivos
- [x] **Banco de dados**
  - [x] Tabelas `audit_log` e `seen_nonces` criadas
  - [x] Coluna `totp_secret` em `users`
  - [x] Hashes bcrypt reais nos dados de seed
- [x] **Infra**
  - [x] `mosquitto.conf` (porta 1883, anônimo)
  - [x] `requirements.txt` com versões fixas

---

### ✅ M2 — Camada de Segurança (concluído 2026-03-15)

- [x] **Certificados TLS (openssl)**
  - [x] CA self-signed (`certs/ca.crt` + `certs/ca.key`)
  - [x] Certificado do broker assinado pela CA (`certs/broker.crt`, `certs/broker.key`)
  - [x] Script `certs/gerar_certs.sh`
  - [x] SAN com IP:10.0.0.175 e IP:127.0.0.1

- [x] **Mosquitto TLS — `source/broker/mosquitto-tls.conf`**
  - [x] Porta 8883 com cafile, certfile, keyfile
  - [x] password_file com credenciais do ESP32 e Flask
  - [x] acl_file — ESP32 só publica, Flask só lê
  - [x] TLS mínimo v1.2, anônimo desativado

- [x] **ESP32 — segurança de comunicação**
  - [x] WiFiClientSecure + setCACert (CA embarcada em PROGMEM)
  - [x] Credenciais MQTT (user/pass)
  - [x] Porta 8883
  - [x] HMAC-SHA256 com mbedtls
  - [x] Nonce com esp_random() (8 bytes hex)
  - [ ] Chave HMAC no NVS via Preferences.h (hardcoded — pendente M3)

- [x] **Flask — verificação de segurança**
  - [x] paho-mqtt com TLS
  - [x] Flask-Login + bcrypt
  - [x] TOTP com pyotp (MFA via Google Authenticator)
  - [x] @login_required em todas as rotas
  - [x] @require_permission RBAC
  - [x] Audit log completo
  - [x] Configuração via .env + python-dotenv
  - [ ] Verificação HMAC em on_message (pendente)
  - [ ] Deduplicação de nonce em seen_nonces (pendente)
  - [ ] Janela de timestamp anti-replay (pendente)

- [x] **MySQL seguro**
  - [x] Credenciais em .env (fora do código)
  - [x] .gitignore protegendo .env e chaves privadas

---

### ✅ M3 (parcial) — Dashboard Completo + Gestão (concluído 2026-04)

- [x] **Sistema multi-tenant**
  - [x] Tabela `companies`, campo `company_id` em vaccines/devices/users
  - [x] `company_where()` — scoping automático por empresa em todas as queries
  - [x] Role `superadmin` com acesso cross-company
  - [x] Role `admin` com acesso à própria empresa
  - [x] Role `operator` com acesso somente-leitura

- [x] **Dashboard completo (index.html)**
  - [x] Gráfico de temperatura com Chart.js — linha do tempo, limites coloridos, pontos de violação em vermelho
  - [x] Mapa GPS interativo Leaflet.js — rota, início (verde), posição atual (laranja)
  - [x] Checkbox "Todos os Rastreamentos" — mapa combinado com 15 cores distintas por rastreamento
  - [x] Toasts de alertas polling a cada 10s (violações + ataques HMAC para admins)
  - [x] Tab Debug — publicação manual de payloads MQTT (somente admin)
  - [x] Auto-refresh parcial (status, devices, chart/map)

- [x] **Página de rastreamento (`trip_readings.html`)**
  - [x] Tabela completa de leituras com filtro por período
  - [x] Stats: total, violações, média, min, max
  - [x] Linhas de violação destacadas em vermelho

- [x] **Gestão de dispositivos (admin_bp)**
  - [x] Auto-discovery de novos dispositivos (pending)
  - [x] Registro com nome e associação a rastreamento
  - [x] Desativação
  - [x] Desatrelamento (funciona para rastreamentos ativos e encerrados)

- [x] **Gestão de rastreamentos**
  - [x] Criar rastreamento (origem, destino, lote, dispositivo)
  - [x] Encerrar rastreamento com confirmação
  - [x] Listagem com status ativo/encerrado

- [x] **Gestão de usuários (admin)**
  - [x] Criar usuário com role e empresa
  - [x] Listagem de usuários da empresa

- [x] **Dados de demonstração**
  - [x] `seed_demo.py` — 25 produtos, 36 lotes, 28 rastreamentos globais, ~1638 leituras
  - [x] Duas empresas com dados independentes

---

### ⏳ Pendente

- [ ] Verificação HMAC em on_message + deduplicação de nonce
- [ ] Criptografia em repouso (AES-256-GCM nos campos de leitura)
- [ ] Buffer offline no ESP32 (SPIFFS — firmware atualizado)
- [ ] Relatório PDF por rastreamento (reportlab)
- [ ] Alertas por email (smtplib)
- [ ] Broker failover (docker-compose com dois Mosquitto)
- [ ] Testes de segurança documentados (Wireshark, replay, MITM)

---

## Notas Técnicas

| Item | Valor |
|---|---|
| IP do servidor | `10.0.0.175` |
| Porta MQTT (dev) | `1883` (Mosquitto local, desativada em prod) |
| Porta MQTT (prod) | `8883` (TLS — HiveMQ Cloud ou Mosquitto TLS) |
| MQTT user ESP32 | `esp32-device` / `Esp32Mqtt@2026` |
| MQTT user Flask | `flask-subscriber` / `FlaskMqtt@2026` |
| MySQL senha | `VaccineSecure@2026` |
| Flask secret key | em `.env` |
| Dispositivo ativo | `ESP32-B0A732D765D0` |
| Rastreamento ativo | Guarulhos → Manaus (empresa PharmaTransport) |
| Senha admin (PharmaTransport) | `admin123` / email: `admin@pharmatransport.com` |
| Senha admin (BioFrio) | `admin123` / email: `admin@biofrio.com` |
| Senha operadores | `op123` |
| MySQL datadir | `C:/Users/guilh/mysql-data` (sem serviço Windows) |
| Mosquitto path | `C:\Program Files\mosquitto\` |
| Python venv | `source/venv/Scripts/python.exe` |
