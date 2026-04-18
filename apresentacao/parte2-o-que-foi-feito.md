# PARTE 2 — O QUE FOI CONSTRUÍDO

---

## 2.1 Visão Geral da Arquitetura

O sistema foi construído em duas milestones principais, com desenvolvimento incremental e testado em cada etapa antes de avançar.

**Milestone 1 (M1)** — Pipeline funcional: ESP32 → MQTT → Flask → MySQL → Dashboard. Sistema operacional sem segurança avançada, foco em validar o fluxo de dados de ponta a ponta.

**Milestone 2 (M2)** — Camada de segurança: TLS 1.2, autenticação MQTT, MFA, RBAC, HMAC, nonce, audit log. Sistema com segurança em produção.

O desenvolvimento seguiu o princípio de **security by design** — cada componente foi projetado com segurança como requisito desde o início, não como adição posterior.

---

## 2.2 Hardware — A Camada de Percepção

### O Dispositivo

O dispositivo físico é construído sobre o **ESP32 DevKit V1**, um microcontrolador da Espressif Systems com as seguintes características relevantes para este projeto:

- **Processador**: Xtensa LX6 dual-core, 240 MHz
- **Memória**: 520KB SRAM, 4MB Flash
- **Conectividade**: WiFi 802.11 b/g/n, Bluetooth 4.2
- **Criptografia**: Acelerador de hardware para AES, SHA, RSA (utilizado pelo `mbedtls`)
- **Custo**: ~R$30 no mercado brasileiro

A escolha do ESP32 sobre alternativas como Arduino Uno ou Raspberry Pi foi deliberada:
- WiFi nativo (sem shield adicional)
- Suporte a TLS via `WiFiClientSecure` e `mbedtls`
- Acelerador criptográfico em hardware (HMAC-SHA256 sem sobrecarregar a CPU)
- Sistema de arquivos SPIFFS para buffer offline
- Watchdog Timer por hardware via IDF

### Sensores Integrados

#### DHT22 — Temperatura e Umidade
- **Pino**: GPIO 4
- **Faixa de temperatura**: -40°C a +80°C (precisão ±0.5°C)
- **Faixa de umidade**: 0% a 100% (precisão ±2%)
- **Protocolo**: Single-wire (1-Wire customizado)
- **Taxa de amostragem**: 1 leitura a cada 2 segundos (mínimo do sensor)
- **Tratamento de falha**: `isnan(temp)` → valor 0.0 no payload (evita travamento)
- **Biblioteca**: `DHT sensor library` (Adafruit)

O DHT22 foi escolhido sobre o DHT11 pela precisão significativamente superior (±0.5°C vs ±2°C) — crítico para produtos com faixas estreitas como Spikevax (-25°C a -15°C, janela de apenas 10°C).

#### GPS NEO-6M — Localização
- **Interface**: UART1 (GPIO 16 RX, GPIO 17 TX)
- **Baudrate**: 9600 bps
- **Protocolo**: NMEA 0183 (sentença GPRMC, GPGGA)
- **Precisão**: ±2.5m (CEP, sem SBAS)
- **Tempo de fix frio**: ~30s em campo aberto
- **Biblioteca**: TinyGPS++ (parser eficiente em memória)

A biblioteca TinyGPS++ foi escolhida pela eficiência — processa bytes NMEA individualmente (`gps.encode(c)`) sem alocar strings grandes, adequado para a RAM limitada do ESP32.

**Validação GPS**: antes de usar as coordenadas, o firmware verifica `gps.location.isValid()`. Se o fix ainda não foi adquirido, envia `latitude: 0.0, longitude: 0.0` — o dashboard distingue esses valores de coordenadas reais.

### A Caixa 3D

A caixa do dispositivo foi modelada do zero no **OpenSCAD** — uma linguagem de programação para modelagem 3D sólida, ideal para designs paramétricos.

**Dimensões**: 170 × 90 × 80mm (externas)
**Material**: PLA (impressão FDM)
**Espessura de parede**: 2.5mm

**Características de design**:
- Abertura frontal (USB/alimentação): 27 × 18mm — cobre o conector Micro-B com margem para plugues angulados
- Abertura lateral (DHT22): 29 × 21mm — sensor voltado para o ambiente externo para leitura correta
- 3 furos de ventilação (Ø7mm): na parede oposta ao USB, para circulação de ar
- Tampa removível: encaixe por plug de 3mm de profundidade com folga de 0.15mm por lado (0.3mm total) — calibrado para impressão FDM

O projeto passou por iteração com o estabelecimento de impressão 3D: a primeira versão tinha o lip interno de encaixe que impossibilitava o fechamento. A versão final usa encaixe direto nas paredes internas da caixa, sem saliências.

---

## 2.3 Firmware — A Lógica do Dispositivo

O firmware foi desenvolvido em **C++ com Arduino Framework** na Arduino IDE, com as seguintes bibliotecas:

| Biblioteca | Versão | Função |
|---|---|---|
| PubSubClient | 2.8 | Cliente MQTT |
| ArduinoJson | 6.x | Serialização JSON |
| DHT sensor library | 1.4.x | Leitura DHT22 |
| TinyGPS++ | 1.0.x | Parser NMEA GPS |
| WiFiClientSecure | (ESP32 built-in) | TLS sobre WiFi |
| mbedtls | (ESP32 built-in) | HMAC-SHA256 |
| SPIFFS | (ESP32 built-in) | Buffer offline |
| esp_task_wdt | (ESP32 IDF) | Watchdog timer |

### 2.3.1 Estrutura do Firmware

O firmware é organizado em módulos funcionais dentro de um único arquivo `main.ino`:

```
setup()
  ├── Serial.begin(115200)
  ├── SPIFFS.begin()              ← monta filesystem
  ├── configureWatchdog()         ← inicializa WDT 60s
  ├── WiFi.begin(SSID, PASS)
  ├── syncNTP()                   ← sincroniza relógio
  └── connectMQTT()

loop()
  ├── esp_task_wdt_reset()        ← alimenta watchdog
  ├── processGPS()                ← lê bytes UART
  ├── ensureWiFi()                ← reconecta se necessário
  ├── ensureMQTT()                ← reconecta + flushBuffer()
  ├── mqttClient.loop()           ← processa ACKs
  ├── a cada 5s: publishReading() ← ou saveToBuffer()
  └── a cada 30s: publishHeartbeat()
```

### 2.3.2 Payload JSON

Cada mensagem de leitura tem a seguinte estrutura:

```json
{
  "device_id":   "ESP32-A1B2C3D4E5F6",
  "timestamp":   "2026-03-15T18:45:30Z",
  "temperature": -20.5,
  "humidity":    65.3,
  "latitude":    -23.550520,
  "longitude":   -46.633309,
  "satellites":  12,
  "hmac":        "a3f2c1...64chars",
  "nonce":       "9f3a2b1c4d5e6f7a"
}
```

O heartbeat (a cada 30s) é mais simples:

```json
{
  "device_id": "ESP32-A1B2C3D4E5F6",
  "timestamp": "2026-03-15T18:45:30Z",
  "status":    "online"
}
```

### 2.3.3 Device ID Dinâmico

O ID do dispositivo é gerado automaticamente do endereço MAC do hardware:

```cpp
String mac = WiFi.macAddress();   // "A1:B2:C3:D4:E5:F6"
mac.replace(":", "");             // "A1B2C3D4E5F6"
DEVICE_ID_STR = "ESP32-" + mac;  // "ESP32-A1B2C3D4E5F6"
```

Isso garante unicidade por hardware, sem precisar hardcodar identificadores. Em uma frota de 100 dispositivos, cada um se auto-identifica corretamente.

### 2.3.4 Sincronização de Tempo — NTP + GPS

O timestamp preciso é fundamental para a rastreabilidade. O firmware usa uma hierarquia de fontes:

1. **GPS (prioridade máxima)**: quando a localização é válida, o GPS também fornece a hora UTC com precisão de ±1ms. Isso é importante para o mecanismo anti-replay — um timestamp muito divergente do servidor pode indicar ataque.

2. **NTP (fallback)**: se o GPS ainda não tem fix, sincroniza com `pool.ntp.org` e `time.google.com`. A sincronização é executada no boot e após cada reconexão WiFi.

3. **Timestamp vazio (último recurso)**: se ambos falharem, o campo é enviado vazio e o Flask usa `NOW()` do MySQL — mantém o dado, mas com menor precisão.

### 2.3.5 Segurança no Firmware

#### TLS com Verificação de Certificado

```cpp
WiFiClientSecure wifiClientSecure;
wifiClientSecure.setCACert(CA_CERT);  // embedded como string PROGMEM
PubSubClient mqttClient(wifiClientSecure);
mqttClient.setServer(MQTT_BROKER, 8883);
```

O certificado CA está embutido no firmware como uma string `PROGMEM` (armazenada na flash, não na RAM). O `setCACert()` instrui o stack TLS a verificar o certificado do broker contra esse CA — qualquer certificado de outra CA é rejeitado, prevenindo ataques MITM.

**Atualmente, o projeto usa o HiveMQ Cloud como broker**, que usa Let's Encrypt como CA. O firmware contém o certificado intermediário R12 da Let's Encrypt embutido.

#### HMAC-SHA256

```cpp
void computeHMAC(const char* payload, char* out) {
    uint8_t result[32];
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
    mbedtls_md_hmac_starts(&ctx, (const uint8_t*)HMAC_KEY, strlen(HMAC_KEY));
    mbedtls_md_hmac_update(&ctx, (const uint8_t*)payload, strlen(payload));
    mbedtls_md_hmac_finish(&ctx, result);
    mbedtls_md_free(&ctx);
    // converte 32 bytes → 64 chars hex
    for (int i = 0; i < 32; i++) sprintf(out + i*2, "%02x", result[i]);
}
```

O HMAC-SHA256 usa a biblioteca `mbedtls` nativa do ESP32, que aproveita o acelerador criptográfico em hardware. A chave é compartilhada entre o dispositivo e o servidor. Qualquer alteração no payload — mesmo um único bit — resulta em um HMAC completamente diferente.

#### Nonce Anti-Replay

```cpp
String generateNonce() {
    uint8_t bytes[8];
    for (int i = 0; i < 4; i++) {
        uint32_t r = esp_random();  // hardware RNG do ESP32
        memcpy(bytes + i*2, &r, 2);
    }
    String nonce = "";
    for (int i = 0; i < 8; i++) {
        char hex[3];
        sprintf(hex, "%02x", bytes[i]);
        nonce += hex;
    }
    return nonce;  // 16 chars hex = 64 bits de entropia
}
```

O `esp_random()` usa o gerador de números aleatórios por hardware do ESP32, baseado em ruído térmico. A cada mensagem, um novo nonce é gerado. O servidor deve armazenar os nonces recebidos e rejeitar duplicatas — prevenindo que um atacante capture e reenvie mensagens legítimas.

### 2.3.6 Buffer Offline com SPIFFS

O **SPIFFS** (SPI Flash File System) é um sistema de arquivos leve que usa a memória flash do ESP32. O firmware usa o arquivo `/buffer.jsonl` (JSON Lines — um objeto JSON por linha).

**Fluxo de escrita**:
```cpp
void saveToBuffer(const char* payload) {
    if (!SPIFFS.exists(BUFFER_FILE)) {
        // verifica espaço disponível
    }
    File f = SPIFFS.open(BUFFER_FILE, FILE_APPEND);
    f.println(payload);
    f.close();
}
```

**Fluxo de flush (ao reconectar)**:
```cpp
void flushBuffer() {
    // 1. Carrega todas as linhas em memória
    std::vector<String> lines;
    File f = SPIFFS.open(BUFFER_FILE, FILE_READ);
    while (f.available()) lines.push_back(f.readStringUntil('\n'));
    f.close();
    
    // 2. Publica cada linha
    int failed_from = -1;
    for (int i = 0; i < lines.size(); i++) {
        bool ok = mqttClient.publish(TOPIC_READINGS, lines[i].c_str(), true);
        if (!ok) { failed_from = i; break; }
        delay(50);  // respeita limite de taxa do broker
    }
    
    // 3. Se falhou no meio: salva restantes em arquivo temporário
    if (failed_from >= 0) {
        File tmp = SPIFFS.open(BUFFER_TMP_FILE, FILE_WRITE);
        for (int i = failed_from; i < lines.size(); i++) tmp.println(lines[i]);
        tmp.close();
        SPIFFS.rename(BUFFER_TMP_FILE, BUFFER_FILE);
    } else {
        SPIFFS.remove(BUFFER_FILE);  // sucesso total — limpa
    }
}
```

**Limites**:
- Tamanho máximo: 100KB (~500 leituras ≈ 40 minutos a 5s/leitura)
- Se o arquivo excede o limite: novas leituras são descartadas (comportamento configurável)

### 2.3.7 Watchdog Timer

O Watchdog Timer (WDT) é um temporizador de hardware que reinicia o microcontrolador se o loop principal não "alimentar" o watchdog dentro do timeout. Isso protege contra travamentos causados por bugs, deadlocks ou condições inesperadas.

```cpp
const esp_task_wdt_config_t wdt_config = {
    .timeout_ms     = 60000,  // 60 segundos
    .idle_core_mask = 0,      // não monitora core idle
    .trigger_panic  = true,   // reinicia em caso de timeout
};
esp_task_wdt_init(&wdt_config);
esp_task_wdt_add(NULL);  // adiciona task atual ao WDT
```

No início de cada ciclo do `loop()`:
```cpp
esp_task_wdt_reset();  // prova de vida — reseta o timer
```

Se o loop travar por mais de 60 segundos (exemplo: loop infinito aguardando GPS, stack overflow), o ESP32 reinicia automaticamente e retoma a operação.

---

## 2.4 Conectividade — MQTT com TLS 1.2

### Por Que MQTT?

MQTT (Message Queuing Telemetry Transport) é o protocolo padrão da indústria para IoT. Foi desenvolvido pela IBM em 1999 para monitoramento de oleodutos via satélite — exatamente o cenário de conexão instável e dispositivo com recursos limitados que este projeto enfrenta.

**Comparação com HTTP/REST**:

| Aspecto | MQTT | HTTP |
|---|---|---|
| Overhead por mensagem | ~2 bytes (header) | ~hundreds of bytes |
| Modelo | Publish-Subscribe | Request-Response |
| Conexão | Persistente (keep-alive) | Nova a cada request |
| Reconexão | Automática (built-in) | Responsabilidade do cliente |
| QoS | 0, 1, 2 (garantias de entrega) | Não nativo |
| Mensagens offline | Broker retém (QoS 1+) | Não |

Para um dispositivo IoT em movimento, enviando dados a cada 5 segundos, o overhead do HTTP seria proibitivo. O MQTT mantém uma única conexão TCP persistente e envia payloads mínimos.

### Broker HiveMQ Cloud

O broker escolhido para produção é o **HiveMQ Cloud** — um serviço gerenciado de MQTT na nuvem, com plano gratuito que inclui:
- 100 conexões simultâneas
- 10 GB de dados/mês
- TLS obrigatório (porta 8883)
- Disponibilidade 99.9% (SLA)
- Certificado Let's Encrypt (CA reconhecida globalmente)
s
**Por que cloud em vez de broker local?**
O broker local (Mosquitto) era suficiente para M1, mas limitava o ESP32 à rede local do servidor. Com HiveMQ Cloud, o dispositivo pode enviar dados de qualquer rede com internet — celular, WiFi público, 4G — tornando o sistema verdadeiramente portátil.

### Configuração TLS

O TLS (Transport Layer Security) 1.2 garante:
- **Confidencialidade**: todos os dados são criptografados com AES-256
- **Autenticidade**: o broker prova sua identidade com um certificado X.509
- **Integridade**: qualquer alteração nos dados em trânsito é detectada

**No ESP32**: `WiFiClientSecure.setCACert(CA_CERT)` instrui o stack TLS a verificar o certificado do broker contra o certificado CA embutido no firmware. Conexões com certificados de CAs não reconhecidas são rejeitadas — prevenindo MITM.

**No Flask**: `client.tls_set()` usa o CA store do sistema operacional (que inclui Let's Encrypt), sem necessidade de certificado manual.

### Tópicos e ACL

```
vaccines/readings    ← leituras de sensores (ESP32 publica)
vaccines/heartbeat   ← sinal de vida (ESP32 publica)
```

O controle de acesso (ACL — Access Control List) garante o princípio do mínimo privilégio:

```
user esp32-device
topic write vaccines/readings    ← só pode publicar
topic write vaccines/heartbeat   ← só pode publicar

user flask-subscriber
topic read vaccines/#            ← só pode ler
```

O ESP32 **fisicamente não consegue** se inscrever nos tópicos e ler dados de outros dispositivos. O Flask **fisicamente não consegue** publicar dados forjados no lugar de um dispositivo.

### QoS 1 — Garantia de Entrega

O sistema usa **QoS 1 (at least once)**:
- O publicador envia a mensagem
- O broker confirma com PUBACK
- Se não receber PUBACK, o publicador reenvia

**No Flask subscriber** (`clean_session=False`): a sessão é persistente no broker. Se o Flask desconectar temporariamente, o HiveMQ armazena as mensagens QoS 1 e as entrega ao reconectar.

---

## 2.5 Backend Flask — A Camada de Análise

### Arquitetura da Aplicação

O backend é uma aplicação **Flask** (Python) com duas responsabilidades principais executando em threads separadas:

```
Thread Principal (Flask)          Thread Secundária (MQTT)
─────────────────────────         ──────────────────────────
HTTP API (porta 5000)             Subscriber paho-mqtt
Autenticação / Sessões            on_connect → subscribe
RBAC / Decorators                 on_message → INSERT MySQL
Renderização Templates            on_disconnect → flag
```

A separação em threads é necessária porque o `loop_forever()` do paho-mqtt é bloqueante — ele precisa de sua própria thread para processar mensagens MQTT sem bloquear as requisições HTTP.

### 2.5.1 Autenticação — Flask-Login + bcrypt

O sistema implementa autenticação em três camadas progressivas:

#### Camada 1 — Email e Senha

```python
password_hash = user["password_hash"].encode("utf-8")
if not bcrypt.checkpw(password.encode("utf-8"), password_hash):
    audit("login_failed", ...)
    return render_template("login.html", error="Credenciais inválidas")
```

O bcrypt é um algoritmo de hash projetado especificamente para senhas. Ao contrário de MD5 ou SHA256 (que são rápidos), o bcrypt é intencionalmente lento — cada verificação leva ~100ms, tornando ataques de força bruta impraticáveis. O fator de custo usado é 12 (2^12 = 4096 iterações de hash).

#### Camada 2 — TOTP (Time-based One-Time Password)

Implementado com a biblioteca **pyotp**, compatível com Google Authenticator, Authy e Microsoft Authenticator.

**Na primeira vez** (setup):
```python
secret = pyotp.random_base32()  # 160 bits de entropia
uri = pyotp.totp.TOTP(secret).provisioning_uri(
    name=user["email"],
    issuer_name="PharmaTransport IoT"
)
# Gera QR code PNG → Base64 → exibe no template
img = qrcode.make(uri)
buffer = io.BytesIO()
img.save(buffer, format="PNG")
qr_b64 = base64.b64encode(buffer.getvalue()).decode()
```

**Na verificação**:
```python
totp = pyotp.TOTP(user["totp_secret"])
if not totp.verify(code, valid_window=1):  # ±30s tolerância
    audit("totp_failed", ...)
    return render_template("verify_totp.html", error="Código inválido")
```

O TOTP funciona assim: o secret é compartilhado entre o servidor e o aplicativo no celular. A cada 30 segundos, ambos calculam `HMAC-SHA1(secret, floor(unix_time / 30))` e exibem os últimos 6 dígitos. Como usam o mesmo secret e o mesmo timestamp, o código é idêntico — sem nenhuma comunicação entre eles.

#### Camada 3 — Session Cookie (Flask-Login)

Após passar pelas duas camadas, `login_user(user)` cria uma sessão segura com cookie HTTP-only, assinado com a `FLASK_SECRET_KEY`. Isso mantém o usuário logado entre requisições.

### 2.5.2 RBAC — Controle de Acesso por Perfil

O sistema define dois perfis com permissões distintas:

```python
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
```

O controle é implementado via decorator:

```python
def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.has_permission(permission):
                return jsonify({"error": "Acesso negado"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route("/api/audit")
@login_required
@require_permission("view_audit")
def audit_log():
    ...
```

Operadores veem o dashboard mas não podem gerenciar dispositivos, criar viagens ou ver o audit log.

### 2.5.3 MQTT Subscriber — Processamento de Mensagens

O subscriber MQTT processa dois tipos de mensagem:

#### Heartbeat (vaccines/heartbeat)

```python
def handle_heartbeat(payload):
    device_id = payload["device_id"]
    ensure_device_exists(device_id)  # auto-discovery
    db.execute(
        "UPDATE devices SET last_seen = NOW() WHERE serial_number = %s",
        (device_id,)
    )
```

O **auto-discovery** é um mecanismo que registra automaticamente dispositivos desconhecidos como `pending`. Quando um ESP32 novo envia seu primeiro heartbeat, o sistema cria sua entrada no banco com `registration_status = 'pending'` — o administrador visualiza no dashboard e pode registrá-lo formalmente.

#### Leitura (vaccines/readings)

```python
def handle_reading(payload):
    device_id = payload["device_id"]
    
    # 1. Verifica se dispositivo está registrado
    device = get_device(device_id)
    if not device or device["registration_status"] != "active":
        return  # descarta leituras de dispositivos não registrados
    
    # 2. Busca viagem ativa para o dispositivo
    trip = get_active_trip_for_device(device["device_id"])
    if not trip:
        return  # sem viagem ativa, descarta
    
    # 3. Normaliza timestamp
    ts = payload.get("timestamp", "")
    timestamp = normalize_timestamp(ts) or datetime.now()
    
    # 4. Insere leitura no banco
    db.execute("""
        INSERT INTO readings (trip_id, batch_id, timestamp, temperature, humidity, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (trip["trip_id"], trip["batch_id"], timestamp,
          payload["temperature"], payload["humidity"],
          payload.get("latitude"), payload.get("longitude")))
    
    # 5. Audit
    audit("reading_received", "readings", reading_id, 
          details={"device_id": device_id, "temperature": payload["temperature"]})
```

### 2.5.4 API REST — Endpoints Principais

A API segue REST e retorna JSON. Todos os endpoints exigem autenticação.

**GET /api/status**
```json
{
  "broker_connected": true,
  "last_mqtt_message": "2026-03-15T18:45:30.123456Z",
  "server_time": "2026-03-15T18:46:00.654321Z"
}
```
Grace period de 90 segundos: se a última mensagem chegou há menos de 90s, o broker é considerado conectado mesmo que o flag interno seja false.

**GET /api/devices**
```json
[{
  "device_id": 4,
  "serial_number": "IOT-GPS-004",
  "name": "Carga Moderna SP",
  "status": "active",
  "last_seen": "2026-03-15T18:45:30",
  "connectivity": "online",
  "active_trip_id": 3,
  "active_trip_dest": "Interior SP - Campinas"
}]
```
Lógica de conectividade:
- `online`: visto há menos de 60 segundos
- `recent`: visto há menos de 5 minutos
- `offline`: visto há mais de 5 minutos
- `never`: nunca visto (só heartbeats, sem leituras)

**GET /api/alarms**
Retorna leituras onde `temperature < min_temp OR temperature > max_temp`, cruzando com os limites do produto associado ao lote da viagem.

**GET /api/audit** (admin only)
Retorna os últimos N registros do audit_log com nome do usuário, IP, ação e detalhes em JSON.

### 2.5.5 Audit Log

O audit log é implementado como uma função helper chamada em todo ponto de interesse:

```python
def audit(action, target_table=None, target_id=None, details=None, user_id=None, ip=None):
    effective_user_id = user_id or (current_user.id if current_user.is_authenticated else None)
    effective_ip = ip or request.remote_addr if request else None
    db.execute("""
        INSERT INTO audit_log (user_id, action, target_table, target_id, ip_address, details, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, (effective_user_id, action, target_table, target_id,
          effective_ip, json.dumps(details) if details else None))
```

**Eventos auditados**:

| Evento | Quando |
|---|---|
| `login_failed` | Credenciais incorretas |
| `login_password_ok` | Senha correta, aguardando TOTP |
| `totp_failed` | Código TOTP incorreto |
| `totp_setup_ok` | MFA configurado com sucesso |
| `login_ok` | Login completo bem-sucedido |
| `logout` | Usuário encerrou sessão |
| `reading_received` | Leitura MQTT inserida no banco |
| `device_discovered` | Novo ESP32 visto pela primeira vez |
| `device_registered` | Admin registrou um dispositivo |
| `device_deactivated` | Admin desativou um dispositivo |
| `trip_created` | Nova viagem criada |
| `trip_closed` | Viagem encerrada com confirmação |

---

## 2.6 Banco de Dados MySQL 8.0

### 2.6.1 Modelo Relacional

O schema tem 8 tabelas organizadas em três domínios:

**Domínio de Produtos**:
```
vaccines ──< vaccine_batch
(vacina)     (lote específico com código e validade)
```

**Domínio de Operação**:
```
devices ──────────────────────────> trips
(ESP32 registrado)                  (viagem = batch + device + rota)
                                         │
                                         └──< readings
                                              (leituras de sensores)
```

**Domínio de Segurança**:
```
users ──< audit_log
          seen_nonces
```

### 2.6.2 Tabelas Principais

**`devices`** — Gerencia o ciclo de vida dos dispositivos:
```sql
registration_status ENUM('pending','active','inactive')
```
- `pending`: auto-descoberto, aguarda aprovação do admin
- `active`: registrado e operacional
- `inactive`: desativado (histórico preservado)

**`trips`** — Cada viagem é imutável:
- `start_time` preenchida na criação
- `end_time = NULL` enquanto ativa
- `end_time` preenchida ao encerrar (com `received_confirmation = TRUE`)
- Leituras vinculadas a `trip_id` nunca são deletadas

**`seen_nonces`** — Anti-replay:
```sql
CREATE TABLE seen_nonces (
    nonce       VARCHAR(64) NOT NULL PRIMARY KEY,
    device_id   VARCHAR(100) NOT NULL,
    received_at DATETIME NOT NULL,
    INDEX idx_received_at (received_at)
);
```
A chave primária no `nonce` garante unicidade em O(log n). O índice em `received_at` permite limpeza eficiente de nonces antigos.

**`audit_log`** — Imutável por design:
- Não há endpoint de DELETE ou UPDATE no audit log
- O campo `details` armazena JSON livre para contexto adicional
- `user_id = NULL` para ações de sistema (leituras MQTT)

### 2.6.3 Integridade e Segurança do Banco

- **Foreign Keys** com `ON DELETE SET NULL` onde apropriado (um usuário deletado não quebra o histórico de dispositivos)
- **bcrypt** para todas as senhas de usuário — nunca texto plano
- **Credenciais em `.env`** — nunca no código-fonte
- **`.gitignore`** protege: `.env`, `certs/*.key`, `*.pem`

---

## 2.7 Dashboard — A Camada de Ação

### Tecnologias

O dashboard foi desenvolvido em **HTML5 + CSS3 + JavaScript puro** (sem React, Angular ou Vue) por uma decisão deliberada: minimizar dependências e manter o código compreensível para uma pessoa com acesso ao repositório.

**Bibliotecas externas** (CDN, sem instalação):
- **Leaflet.js**: mapas interativos com OpenStreetMap
- **Chart.js**: gráficos de linha de temperatura
- **Google Fonts** (Inter): tipografia

### Componentes Principais

#### Status dos Dispositivos
Cards com indicador de conectividade calculado em tempo real:
- 🟢 **Online** (< 60s desde último heartbeat)
- 🟡 **Recente** (< 5 minutos)
- ⚫ **Offline** (> 5 minutos)
- ⬜ **Pendente** (auto-descoberto, não registrado)

#### Gráfico de Temperatura (Chart.js)
Linha do tempo completa da viagem selecionada. Otimização de performance: `pointRadius = 0` para viagens com mais de 100 leituras (evita renderizar centenas de círculos individuais).

#### Mapa GPS (Leaflet.js)
- Rota completa como polyline (linha contínua)
- Marcador de início (🟢) e posição atual (🟠)
- Popup no hover com temperatura e umidade no ponto
- Tiles: CARTO Dark (mapa escuro, compatível com o tema do dashboard)
- Auto-fit: `map.fitBounds(bounds)` centraliza na rota

#### Seletor de Lote
O usuário seleciona o lote transportado; o sistema exibe automaticamente a viagem associada e carrega os dados. Isso inverte a UX de "selecionar viagem" para "selecionar o produto que você quer rastrear" — mais natural para o operador.

#### Auto-refresh
```javascript
setInterval(() => {
    refreshStatus();
    refreshDevices();
    if (currentTripId) refreshChartAndMap(currentTripId);
    if (isAdmin) refreshAdminPending();
}, 10000);
```
Sem recarregar a página. Sem WebSocket. A cada 10 segundos, requisições fetch independentes atualizam cada seção.

---

## 2.8 Segurança — Visão Consolidada

A segurança foi implementada em **defesa em profundidade** — múltiplas camadas independentes, onde a falha de uma não compromete as demais.

| Camada | Ameaça Mitigada | Mecanismo |
|---|---|---|
| **Transporte** | Interceptação (sniffing) | TLS 1.2, AES-256 |
| **Autenticidade do broker** | Man-in-the-Middle | Verificação de certificado X.509 |
| **Payload** | Adulteração de dados | HMAC-SHA256 |
| **Replay Attack** | Reenvio de mensagens antigas | Nonce único por mensagem |
| **Timestamp** | Replay com timestamp falso | Janela de 5 minutos (M3) |
| **Acesso ao sistema** | Acesso não autorizado | Login + bcrypt |
| **Acesso ao sistema** | Senha comprometida | TOTP MFA |
| **Autorização** | Escalada de privilégio | RBAC por perfil |
| **MQTT** | Publicação forjada | ACL (write-only para ESP32) |
| **Credenciais** | Exposição no código | .env + .gitignore |
| **Rastreabilidade** | Ações sem responsável | Audit log completo |

### Decisões de Segurança Relevantes

**Por que TOTP em vez de SMS?**
- SMS depende de operadora — pode falhar, ser interceptado (SS7 attack) ou ter custo por mensagem
- TOTP funciona offline (calcula localmente no celular)
- Padrão RFC 6238, suportado por todos os autenticadores principais
- Sem custo adicional

**Por que bcrypt e não SHA256?**
- SHA256 processa bilhões de hashes por segundo em GPU moderna
- bcrypt é projetado para ser lento (configura-se o fator de custo)
- Com fator 12, uma GPU de alta performance leva ~100 anos para quebrar um hash bcrypt por força bruta

**Por que credenciais separadas no MQTT?**
- Se o firmware do ESP32 for extraído (attack físico), o atacante obtém apenas as credenciais de `esp32-device` — que só pode publicar
- As credenciais do `flask-subscriber` (que lê todos os dados) ficam no servidor, protegidas

**Por que ACL no broker?**
- Impede que um ESP32 comprometido se inscreva em `vaccines/#` e leia dados de outros dispositivos
- Impede que o Flask publique dados forjados nos tópicos de dispositivos
- Princípio do mínimo privilégio aplicado ao nível de protocolo

---

## 2.9 Infraestrutura e Deploy

### Como o Sistema Sobe

O ambiente de produção usa três processos independentes:

```bash
# 1. MySQL (sem serviço Windows — controle manual)
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" \
  --datadir="C:/Users/guilh/mysql-data" --port=3306

# 2. Flask (inclui o subscriber MQTT em thread separada)
cd source/app
../../venv/Scripts/python.exe app.py
# Porta 5000 — http://127.0.0.1:5000
```

O broker MQTT é o HiveMQ Cloud — gerenciado externamente, sempre disponível.

### Configuração por Variáveis de Ambiente

Todo valor sensível ou específico do ambiente está em `.env`:

```
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=VaccineSecure@2026
DB_NAME=vaccine_transport

FLASK_SECRET_KEY=v@ccine-iot-tcc-secret-2026-xK9mPqR7

MQTT_BROKER=1fe6e4dc6c3b41d193f6448d1ab84a93.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=flask-subscriber
MQTT_PASSWORD=FlaskMqtt@2026
```

O `.env` está no `.gitignore` — nunca sobe para o repositório.

### Dependências Python

```
flask==3.0.3
mysql-connector-python==8.4.0
paho-mqtt==2.1.0
flask-login==0.6.3
bcrypt==4.1.3
pyotp==2.9.0
qrcode[pil]==7.4.2
cryptography==42.0.8
python-dotenv==1.0.1
pillow==10.3.0
```

Versões fixadas para garantir reprodutibilidade — `pip install -r requirements.txt` instala exatamente o que foi testado.

---

## 2.10 Conformidade Regulatória

### RDC nº 430/2020 — Anvisa

A Resolução da Diretoria Colegiada nº 430/2020 estabelece as Boas Práticas de Distribuição, Armazenagem e Transporte de Medicamentos. O PharmaTransport IoT implementa seus requisitos principais:

| Requisito RDC 430 | Implementação |
|---|---|
| Monitoramento contínuo de temperatura | Leituras a cada 5s, armazenadas com timestamp |
| Registro das condições de transporte | Tabela `readings` com temperatura, umidade, GPS |
| Rastreabilidade por lote | `batch_id` em cada leitura, vinculado a `vaccine_batch` |
| Identificação dos responsáveis | `audit_log` com user_id, IP, ação e timestamp |
| Detecção de desvios | API `/api/alarms` detecta violações automaticamente |
| Confirmação de recebimento | Campo `received_confirmation` na tabela `trips` |

### ISO/IEC 27001

| Controle | Implementação |
|---|---|
| Controle de acesso (A.9) | RBAC + autenticação multifator |
| Criptografia (A.10) | TLS 1.2 + bcrypt + HMAC-SHA256 |
| Segurança física (A.11) | Caixa 3D com componentes protegidos |
| Operações de segurança (A.12) | Audit log, monitoramento de conectividade |
| Gestão de incidentes (A.16) | Alarmes automáticos de violação de temperatura |
