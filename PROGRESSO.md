# Registro de Progresso — TCC IoT Vaccine Transport

## Como usar este arquivo
A cada sessão de trabalho, registre aqui o que foi concluído.
Isso serve como ponto de retomada entre sessões.

---

## MILESTONE 1 — Pipeline MQTT Funcional ✅ CONCLUÍDO (2026-03-12)

### O que foi implementado

#### ESP32 — `source/esp32/main/main.ino`
- [x] WiFi com reconexão automática (baseado em `hardware/test_wifi/test_wifi.ino`)
- [x] MQTT via `PubSubClient` conectado ao broker local
- [x] Payload JSON com `ArduinoJson` (`StaticJsonDocument<256>`)
- [x] Publicação de leituras a cada **5 segundos** no tópico `vaccines/readings`
- [x] Heartbeat a cada **30 segundos** no tópico `vaccines/heartbeat`
- [x] Campos `hmac` e `nonce` presentes no payload (vazios — prontos para M2)
- [x] Timestamp UTC via GPS (`gps.date` + `gps.time`)
- [x] `#define MQTT_MAX_PACKET_SIZE 512` configurado
- IP configurado: `10.0.0.175` | Device: `IOT-GPS-004` | Trip: `3`

#### Flask — `source/app/app.py`
- [x] Thread background `paho-mqtt` subscriber (API versão 2 — sem deprecation warning)
- [x] `on_message`: normaliza timestamp ISO 8601 → formato MySQL, grava em `readings`
- [x] `on_message`: atualiza `devices.last_seen` ao receber heartbeat ou leitura
- [x] Novo endpoint `GET /api/alarms` — leituras fora do range da vacina
- [x] Novo endpoint `GET /api/devices` — status online/offline por último heartbeat
- [x] Novo endpoint `GET /api/status` — estado do broker MQTT + último timestamp
- [x] Endpoint `/api/trips` atualizado com `min_temp` e `max_temp`
- [x] Endpoint `/api/readings/recent` atualizado com thresholds da vacina

#### Dashboard — `source/app/templates/index.html`
- [x] Refresh automático a cada **5 segundos**
- [x] Badge MQTT (verde = conectado / vermelho = desconectado) no header
- [x] Painel de alarmes: lista violações de temperatura com batch code e tipo
- [x] Leituras em vermelho (⚠) quando fora do range da vacina
- [x] Status dos dispositivos: cards coloridos (online/recente/offline/nunca)
- [x] Informações de threshold da viagem selecionada

#### Banco de Dados — `source/database/db_script.sql`
- [x] Tabela `audit_log` criada (log de ações do sistema — rastreabilidade)
- [x] Tabela `seen_nonces` criada (anti-replay — será usada no M2)
- [x] Coluna `totp_secret VARCHAR(32)` adicionada em `users` (para M2 — MFA)
- [x] Senhas de seed substituídas por hashes bcrypt reais

#### Broker — `source/broker/mosquitto.conf`
- [x] Configuração básica: porta 1883, acesso anônimo (desenvolvimento)
- [x] Criado em `source/broker/mosquitto.conf`

#### Dependências — `source/app/requirements.txt`
- [x] Arquivo criado com versões fixas: `flask`, `mysql-connector-python`, `paho-mqtt`
- [x] Libs de M2 listadas em comentário (bcrypt, pyotp, flask-login, cryptography)

### Como subir o ambiente (após reinicialização)

```bash
# 1. Iniciar MySQL (sem senha, datadir customizado)
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --datadir="C:/Users/guilh/mysql-data" --port=3306

# 2. Iniciar Mosquitto
"C:\Program Files\mosquitto\mosquitto.exe" -c "source/broker/mosquitto.conf"

# 3. Iniciar Flask
cd source/app
../../venv/Scripts/python.exe app.py

# Para recriar o banco do zero:
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root < source/database/db_script.sql
```

### Verificação end-to-end M1
```bash
# Publicar leitura de teste (temperatura dentro do range Spikevax: -25°C a -15°C)
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h 127.0.0.1 -p 1883 -t "vaccines/readings" \
  -m '{"device_id":"IOT-GPS-004","trip_id":3,"timestamp":"2026-03-12T18:00:00Z","temperature":-20.0,"humidity":60.0,"latitude":-23.21,"longitude":-45.88,"satellites":8,"hmac":"","nonce":""}'

# Verificar no banco
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root --batch -e "SELECT COUNT(*) FROM vaccine_transport.readings;"

# Verificar status
curl http://127.0.0.1:5000/api/status
```

---

## MILESTONE 2 — Camada de Segurança ⏳ PENDENTE

### O que precisa ser feito

#### Certificados TLS (openssl)
- [ ] Gerar CA self-signed
- [ ] Gerar certificado do broker assinado pela CA
- [ ] Criar pasta `certs/` com CA, broker.crt, broker.key

#### Mosquitto TLS — `source/broker/mosquitto-tls.conf`
- [ ] Configurar porta 8883 com TLS
- [ ] Configurar `cafile`, `certfile`, `keyfile`
- [ ] Criar `passwd` file com credenciais dos dispositivos (`mosquitto_passwd`)
- [ ] Criar `acl_file` por device_id
- [ ] Desativar porta 1883 (apenas 8883)

#### ESP32 — `source/esp32/main/main.ino`
- [ ] Trocar `WiFiClient` por `WiFiClientSecure`
- [ ] Adicionar CA cert como string PROGMEM
- [ ] `wifiClientSecure.setCACert(CA_CERT)`
- [ ] Calcular HMAC-SHA256 do payload com chave do NVS
  - Usar `mbedtls_md_hmac` (disponível no ESP32)
  - Chave armazenada via `Preferences.h` (`preferences.putBytes("hmac_key", ...)`)
- [ ] Gerar nonce com `esp_random()` (hex 8 bytes = 16 chars)
- [ ] Mudar porta para 8883
- [ ] Adicionar usuário/senha MQTT (`mqttClient.connect(id, user, pass)`)

#### Flask — `source/app/app.py`
- [ ] Verificação HMAC-SHA256 em `on_message`
- [ ] Deduplicação de nonce (INSERT em `seen_nonces`, rejeitar duplicata)
- [ ] Verificação de janela de timestamp (rejeitar msg com timestamp > 5min atrás)
- [ ] Instalar e configurar `Flask-Login`
- [ ] Rota `GET/POST /login` com verificação bcrypt
- [ ] Verificação TOTP (`pyotp.TOTP(user.totp_secret).verify(token)`)
- [ ] Decorator `@login_required` em todas as rotas
- [ ] RBAC: decorator `@admin_required` para rotas admin
- [ ] paho-mqtt com TLS (`client.tls_set(ca_certs=...)`)
- [ ] Novo template `source/app/templates/login.html`

#### Banco
- [ ] Nenhuma migration necessária (tabelas `seen_nonces` e coluna `totp_secret` já existem)

---

## MILESTONE 3 — Proteção de Dados + Continuidade ⏳ PENDENTE

- [ ] AES-256-GCM em Python antes de INSERT (colunas temp, humidity, lat, lng)
- [ ] Chave AES em `.env` (`python-dotenv`)
- [ ] Script `source/scripts/backup.sh` (mysqldump + gpg symmetric)
- [ ] Buffer SPIFFS no ESP32 (`/buffer.jsonl`) para mensagens offline
- [ ] Reconexão automática com flush do buffer (QoS 1)
- [ ] Script `source/scripts/cleanup_nonces.py` (limpeza de nonces > 10min)
- [ ] Hardware: circuito de redundância de energia (TP4056 + LiPo 18650)

---

## MILESTONE 4 — Dashboard Completo + Alertas ⏳ PENDENTE

- [ ] Server-Sent Events (SSE) em vez de polling
- [ ] Painel de alarmes com botão ACK (registra em `audit_log`)
- [ ] Alerta por email via `smtplib` (gmail app password)
- [ ] Geração de PDF de viagem (`reportlab`)
- [ ] Viewer de `audit_log` (admin only)
- [ ] Página admin com gestão de usuários e dispositivos

---

## MILESTONE 5 — Failover + Documentação Final ⏳ PENDENTE

- [ ] `docker-compose.yml` com dois Mosquitto (8883 + 8884)
- [ ] ESP32: lógica de troca para broker secundário após 3 falhas
- [ ] Flask: dois threads paho-mqtt (primary + secondary), mesmo DB
- [ ] Documento SOP: rotação de certificados (`docs/sop-cert-rotation.md`)
- [ ] Documento SOP: restauração de backup (`docs/sop-backup-restore.md`)
- [ ] README final com diagrama de arquitetura atualizado

---

## Notas Técnicas Importantes

| Assunto | Detalhe |
|---|---|
| MySQL sem senha | Inicializado com `--initialize-insecure`. Datadir: `C:/Users/guilh/mysql-data` |
| MySQL sem serviço Windows | Precisa iniciar manualmente a cada boot (ver comando acima) |
| Mosquitto path | `C:\Program Files\mosquitto\mosquitto.exe` |
| Python venv | `source/venv/Scripts/python.exe` |
| Senha admin dashboard | `admin123` (bcrypt no banco) |
| Senha operadores | `op123` (bcrypt no banco) |
| Viagem ativa (M1) | Trip ID 3 — Spikevax Moderna, device IOT-GPS-004 |
| Range temp. Spikevax | -25°C a -15°C (testar com temperatura nesse range) |
| Payload MQTT M1 | Campos `hmac` e `nonce` presentes mas vazios |
