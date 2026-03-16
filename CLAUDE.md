# TCC — Secure IoT System for Vaccine Transport
## Contexto do Projeto

Sistema IoT seguro para monitoramento de transporte de vacinas. TCC de Engenharia da Computação.
Arquitetura em 4 pilares: **Percepção** (ESP32 + sensores) → **Conectividade** (MQTT) → **Análise** (Flask + MySQL) → **Ação** (dashboard + alertas).

**Tech stack:** ESP32 (Arduino), Mosquitto MQTT, Python Flask, MySQL, Leaflet.js, Chart.js

---

## Arquivos Críticos

| Arquivo | Função |
|---|---|
| `source/esp32/main/main.ino` | Firmware ESP32 — sensores + MQTT |
| `source/app/app.py` | Backend Flask — API + subscriber MQTT |
| `source/app/templates/index.html` | Dashboard web |
| `source/database/db_script.sql` | Schema + dados de seed |
| `source/broker/mosquitto.conf` | Config Mosquitto (M1, sem TLS) |
| `source/broker/mosquitto-tls.conf` | Config Mosquitto TLS (criar no M2) |
| `source/app/requirements.txt` | Dependências Python |
| `PROGRESSO.md` | Log detalhado de implementação por milestone |

---

## Como subir o ambiente (após reinicialização)

```bash
# 1. MySQL (sem serviço Windows — iniciar manualmente)
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --datadir="C:/Users/guilh/mysql-data" --port=3306

# 2. Mosquitto (TLS — porta 8883)
"C:\Program Files\mosquitto\mosquitto.exe" -c source/broker/mosquitto-tls.conf

# 3. Flask
cd source/app
../../venv/Scripts/python.exe app.py
```

---

## Roadmap de Implementação

### ✅ M1 — Pipeline MQTT Funcional (concluído 2026-03-12)

- [x] **ESP32 firmware completo**
  - [x] WiFi com reconexão automática
  - [x] MQTT via PubSubClient (porta 1883)
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
  - [x] Refresh automático a cada 5s
  - [x] Badge MQTT (verde/vermelho)
  - [x] Painel de alarmes de temperatura
  - [x] Status online/offline dos dispositivos
- [x] **Banco de dados**
  - [x] Tabelas `audit_log` e `seen_nonces` criadas
  - [x] Coluna `totp_secret` em `users` (para M2)
  - [x] Hashes bcrypt reais nos dados de seed
- [x] **Infra**
  - [x] `mosquitto.conf` (porta 1883, anônimo)
  - [x] `requirements.txt` com versões fixas

---

### ✅ M2 — Camada de Segurança (concluído 2026-03-15)

- [x] **Certificados TLS (openssl)**
  - [x] Gerar CA self-signed com CA:TRUE (`certs/ca.crt` + `certs/ca.key`)
  - [x] Gerar certificado do broker assinado pela CA (`certs/broker.crt`, `certs/broker.key`)
  - [x] Script `certs/gerar_certs.sh` para reproduzir os certificados
  - [x] SAN (Subject Alt Name) com IP:10.0.0.175 e IP:127.0.0.1

- [x] **Mosquitto TLS — `source/broker/mosquitto-tls.conf`**
  - [x] Porta 8883 com `cafile`, `certfile`, `keyfile`
  - [x] `password_file` com credenciais do ESP32 e Flask (`mosquitto_passwd`)
  - [x] `acl_file` — ESP32 só publica, Flask só lê
  - [x] TLS mínimo v1.2, anônimo desativado

- [x] **ESP32 — segurança de comunicação**
  - [x] Trocar `WiFiClient` por `WiFiClientSecure`
  - [x] CA cert como string `PROGMEM` no firmware
  - [x] `wifiClientSecure.setCACert(CA_CERT)`
  - [x] Credenciais MQTT em `mqttClient.connect(id, user, pass)`
  - [x] Porta 8883
  - [x] HMAC-SHA256 do payload com `mbedtls_md_hmac`
  - [x] Nonce com `esp_random()` (8 bytes em hex)
  - [ ] Chave HMAC no NVS via `Preferences.h` (atualmente hardcoded — pendente M3)

- [x] **Flask — verificação de segurança**
  - [x] paho-mqtt com TLS (`client.tls_set(ca_certs=...)`)
  - [x] `Flask-Login` + bcrypt para autenticação
  - [x] Rota `GET/POST /login` + `GET /logout`
  - [x] TOTP com `pyotp` na rota de login (MFA via Google Authenticator)
  - [x] Decorator `@login_required` em todas as rotas
  - [x] Decorator `@admin_required` para rotas admin
  - [x] Templates `login.html`, `setup_totp.html`, `verify_totp.html`
  - [x] Audit log ativo (leituras, logins, TOTP setup, logout)
  - [x] Endpoint `/api/audit` (somente admin)
  - [x] Configuração via `.env` + `python-dotenv`
  - [ ] Verificação HMAC em `on_message` (pendente)
  - [ ] Deduplicação de nonce em `seen_nonces` (pendente)
  - [ ] Janela de timestamp anti-replay (pendente)

- [x] **MySQL seguro**
  - [x] Senha root definida (`VaccineSecure@2026`)
  - [x] Credenciais em `.env` (fora do código-fonte)
  - [x] `.gitignore` protegendo `.env` e chaves privadas

---

### ⏳ M3 — Proteção de Dados + Continuidade (pendente)

- [ ] **Criptografia em repouso**
  - [ ] AES-256-GCM em Python antes de INSERT (colunas: temp, humidity, lat, lng)
  - [ ] Chave AES em variável de ambiente (`.env` + `python-dotenv`)
  - [ ] Decrypt em SELECT (transparente para o dashboard)

- [ ] **Backup criptografado**
  - [ ] Script `source/scripts/backup.sh` (`mysqldump | gpg --symmetric`)
  - [ ] Documentar agendamento via Task Scheduler Windows

- [ ] **Buffer offline no ESP32**
  - [ ] SPIFFS ativado (`#include <SPIFFS.h>`)
  - [ ] Append de leituras em `/buffer.jsonl` durante desconexão
  - [ ] Flush do buffer ao reconectar (QoS 1 com ACK antes de deletar)

- [ ] **Limpeza de nonces**
  - [ ] Script `source/scripts/cleanup_nonces.py` (DELETE WHERE `received_at` < NOW() - 10min)
  - [ ] Agendar via Task Scheduler ou thread periódica no Flask

- [ ] **Redundância de energia (hardware)**
  - [ ] Circuito TP4056 + LiPo 18650 + diodo
  - [ ] Monitorar tensão da bateria via ADC (pino ESP32)
  - [ ] Incluir `battery_voltage` no payload
  - [ ] Documentar com foto e esquema elétrico

---

### ⏳ M4 — Dashboard Completo + Alertas (pendente)

- [ ] **Real-time via SSE**
  - [ ] Endpoint Flask `GET /api/stream` (Server-Sent Events)
  - [ ] Substituir `setInterval` por `EventSource` no frontend

- [ ] **Painel de alarmes interativo**
  - [ ] Botão ACK por alarme (registra em `audit_log`)
  - [ ] Filtro por viagem/dispositivo/período

- [ ] **Alertas por email**
  - [ ] `smtplib` + Gmail App Password
  - [ ] Enviar quando leitura viola threshold da vacina
  - [ ] Configuração em variável de ambiente

- [ ] **Relatório PDF por viagem**
  - [ ] `reportlab` — gráfico de temperatura + resumo + violações
  - [ ] Endpoint `GET /api/trips/<id>/report`

- [ ] **Viewer de audit log**
  - [ ] Endpoint `GET /api/audit` (admin only)
  - [ ] Tabela paginada no dashboard (admin)

- [ ] **Página admin**
  - [ ] Gestão de usuários (criar, editar role, resetar TOTP)
  - [ ] Gestão de dispositivos (status, last_seen)

---

### ⏳ M5 — Failover + Documentação Final (pendente)

- [ ] **Broker failover**
  - [ ] `docker-compose.yml` com dois Mosquitto (8883 primary + 8884 secondary)
  - [ ] Ambos com TLS e mesmas credenciais
  - [ ] ESP32: tentar broker secundário após 3 falhas consecutivas
  - [ ] Flask: dois threads paho-mqtt (primary + secondary), mesmo DB

- [ ] **Documentação SOP**
  - [ ] `docs/sop-cert-rotation.md` — procedimento de rotação de certificados
  - [ ] `docs/sop-backup-restore.md` — restauração de backup
  - [ ] `docs/sop-incident-response.md` — checklist de resposta a incidentes

- [ ] **Testes de segurança (para o TCC)**
  - [ ] Captura Wireshark mostrando tráfego cifrado (porta 8883)
  - [ ] Tentativa de replay attack rejeitada (nonce duplicado)
  - [ ] Tentativa de MITM sem CA correta rejeitada
  - [ ] Login com TOTP correto e incorreto demonstrado

- [ ] **Finalização**
  - [ ] README.md atualizado com diagrama de arquitetura final
  - [ ] Fotos do hardware montado
  - [ ] Vídeo de demonstração do sistema completo

---

## Notas Técnicas

| Item | Valor |
|---|---|
| IP do servidor | `10.0.0.175` |
| Porta MQTT (M1) | `1883` (desativada — era dev) |
| Porta MQTT (M2+) | `8883` (TLS ativo) |
| MQTT user ESP32 | `esp32-device` / `Esp32Mqtt@2026` |
| MQTT user Flask | `flask-subscriber` / `FlaskMqtt@2026` |
| MySQL senha | `VaccineSecure@2026` |
| Flask secret key | em `.env` |
| Device ID ativo | `IOT-GPS-004` |
| Trip ID ativo | `3` (Spikevax Moderna, em andamento) |
| Range temp. Spikevax | `-25°C a -15°C` |
| Senha admin | `admin123` |
| Senha operadores | `op123` |
| MySQL datadir | `C:/Users/guilh/mysql-data` (sem serviço) |
| Mosquitto path | `C:\Program Files\mosquitto\` |
| Python venv | `source/venv/Scripts/python.exe` |
