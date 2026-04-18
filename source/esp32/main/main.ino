// ============================================================
// Vaccine Transport IoT — Firmware ESP32
// Milestone 2: TLS/SSL + Credenciais MQTT + HMAC + Nonce
// BCP: Hardware Watchdog + Buffer Offline SPIFFS
// ============================================================

#define MQTT_MAX_PACKET_SIZE 768

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <TinyGPS++.h>
#include "mbedtls/md.h"       // HMAC-SHA256
#include "esp_task_wdt.h"     // Hardware Watchdog Timer
#include <SPIFFS.h>           // Buffer offline
#include <time.h>             // NTP — clock de fallback quando GPS sem fix
#include <vector>             //   std::vector para flush do buffer

// Watchdog: reinicia o ESP32 se o loop principal travar por mais de N segundos
#define WDT_TIMEOUT_SEC 60

// Buffer offline: armazena leituras no SPIFFS quando sem conexão
#define BUFFER_FILE      "/buffer.jsonl"
#define BUFFER_TMP_FILE  "/buffer.tmp"
#define BUFFER_MAX_BYTES 102400   // 100 KB ≈ 500 leituras (~40 min a 5s)

// NTP: servidores e flag de sincronização
#define NTP_SERVER1 "pool.ntp.org"
#define NTP_SERVER2 "time.google.com"
bool ntpSynced = false;

// ======== CONFIGURAÇÕES — ALTERE ANTES DE GRAVAR ========
const char* WIFI_SSID     = "iPhone-Gui";
const char* WIFI_PASSWORD = "hash1234";
const char* MQTT_BROKER   = "1fe6e4dc6c3b41d193f6448d1ab84a93.s1.eu.hivemq.cloud";
const int   MQTT_PORT     = 8883;            // TLS

// Credenciais MQTT (devem coincidir com mosquitto/passwd)
const char* MQTT_USER     = "esp32-device";
const char* MQTT_PASS     = "Esp32Mqtt@2026";

// Chave HMAC-SHA256 (32 bytes) — compartilhada com o servidor
// Em produção: armazenar no NVS via Preferences.h
const char* HMAC_KEY      = "v@ccine-hmac-key-2026-xK9mP7qR!";
// =========================================================

// Device ID gerado automaticamente do endereço MAC (preenchido em setup())
// Formato: ESP32-AABBCCDDEEFF  — único por hardware, sem hardcoding
String DEVICE_ID_STR = "ESP32-UNKNOWN";
const char* DEVICE_ID = nullptr;  // aponta para DEVICE_ID_STR.c_str() após setup()

// Tópicos MQTT
const char* TOPIC_READINGS  = "vaccines/readings";
const char* TOPIC_HEARTBEAT = "vaccines/heartbeat";

// Intervalos
const unsigned long PUBLISH_INTERVAL    = 5000;
const unsigned long HEARTBEAT_INTERVAL  = 30000;

// ======== CA CERTIFICATE (gerado em certs/ca.crt) ========
// Certificado da CA que assinou o broker — permite verificar TLS
static const char CA_CERT[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFBjCCAu6gAwIBAgIRAMISMktwqbSRcdxA9+KFJjwwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMjQwMzEzMDAwMDAw
WhcNMjcwMzEyMjM1OTU5WjAzMQswCQYDVQQGEwJVUzEWMBQGA1UEChMNTGV0J3Mg
RW5jcnlwdDEMMAoGA1UEAxMDUjEyMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEA2pgodK2+lP474B7i5Ut1qywSf+2nAzJ+Npfs6DGPpRONC5kuHs0BUT1M
5ShuCVUxqqUiXXL0LQfCTUA83wEjuXg39RplMjTmhnGdBO+ECFu9AhqZ66YBAJpz
kG2Pogeg0JfT2kVhgTU9FPnEwF9q3AuWGrCf4yrqvSrWmMebcas7dA8827JgvlpL
Thjp2ypzXIlhZZ7+7Tymy05v5J75AEaz/xlNKmOzjmbGGIVwx1Blbzt05UiDDwhY
XS0jnV6j/ujbAKHS9OMZTfLuevYnnuXNnC2i8n+cF63vEzc50bTILEHWhsDp7CH4
WRt/uTp8n1wBnWIEwii9Cq08yhDsGwIDAQABo4H4MIH1MA4GA1UdDwEB/wQEAwIB
hjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwEgYDVR0TAQH/BAgwBgEB
/wIBADAdBgNVHQ4EFgQUALUp8i2ObzHom0yteD763OkM0dIwHwYDVR0jBBgwFoAU
ebRZ5nu25eQBc4AIiMgaWPbpm24wMgYIKwYBBQUHAQEEJjAkMCIGCCsGAQUFBzAC
hhZodHRwOi8veDEuaS5sZW5jci5vcmcvMBMGA1UdIAQMMAowCAYGZ4EMAQIBMCcG
A1UdHwQgMB4wHKAaoBiGFmh0dHA6Ly94MS5jLmxlbmNyLm9yZy8wDQYJKoZIhvcN
AQELBQADggIBAI910AnPanZIZTKS3rVEyIV29BWEjAK/duuz8eL5boSoVpHhkkv3
4eoAeEiPdZLj5EZ7G2ArIK+gzhTlRQ1q4FKGpPPaFBSpqV/xbUb5UlAXQOnkHn3m
FVj+qYv87/WeY+Bm4sN3Ox8BhyaU7UAQ3LeZ7N1X01xxQe4wIAAE3JVLUCiHmZL+
qoCUtgYIFPgcg350QMUIWgxPXNGEncT921ne7nluI02V8pLUmClqXOsCwULw+PVO
ZCB7qOMxxMBoCUeL2Ll4oMpOSr5pJCpLN3tRA2s6P1KLs9TSrVhOk+7LX28NMUlI
usQ/nxLJID0RhAeFtPjyOCOscQBA53+NRjSCak7P4A5jX7ppmkcJECL+S0i3kXVU
y5Me5BbrU8973jZNv/ax6+ZK6TM8jWmimL6of6OrX7ZU6E2WqazzsFrLG3o2kySb
zlhSgJ81Cl4tv3SbYiYXnJExKQvzf83DYotox3f0fwv7xln1A2ZLplCb0O+l/AK0
YE0DS2FPxSAHi0iwMfW2nNHJrXcY3LLHD77gRgje4Eveubi2xxa+Nmk/hmhLdIET
iVDFanoCrMVIpQ59XWHkzdFmoHXHBV7oibVjGSO7ULSQ7MJ1Nz51phuDJSgAIU7A
0zrLnOrAj/dfrlEWRhCvAgbuwLZX1A2sjNjXoPOHbsPiy+lO1KF8/XY7
-----END CERTIFICATE-----
)EOF";
// =========================================================

// ======== CONFIG DHT22 ========
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// ======== CONFIG GPS ========
TinyGPSPlus gps;
HardwareSerial SerialGPS(1);
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
#define GPS_BAUD   9600

// ======== MQTT CLIENT (com TLS) ========
WiFiClientSecure wifiClientSecure;
PubSubClient     mqttClient(wifiClientSecure);

// Controle de tempo e estado de conexão
unsigned long lastPublish   = 0;
unsigned long lastHeartbeat = 0;
bool prevMqttOk = false;   // detecta transição desconectado → conectado


// -------------------------------------------------------
// Gera nonce de 8 bytes em hex usando esp_random()
String generateNonce() {
  char buf[17];
  uint32_t r1 = esp_random();
  uint32_t r2 = esp_random();
  snprintf(buf, sizeof(buf), "%08x%08x", r1, r2);
  return String(buf);
}


// -------------------------------------------------------
// Calcula HMAC-SHA256 de 'data' com HMAC_KEY
// Retorna string hex de 64 chars
String computeHMAC(const String& data) {
  unsigned char hmacResult[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_type_t mdType = MBEDTLS_MD_SHA256;

  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(mdType), 1);
  mbedtls_md_hmac_starts(&ctx,
    (const unsigned char*)HMAC_KEY, strlen(HMAC_KEY));
  mbedtls_md_hmac_update(&ctx,
    (const unsigned char*)data.c_str(), data.length());
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  char hexStr[65];
  for (int i = 0; i < 32; i++) {
    snprintf(hexStr + (i * 2), 3, "%02x", hmacResult[i]);
  }
  return String(hexStr);
}


// -------------------------------------------------------
// Tenta conectar ao WiFi (máx. 10s). Retorna true se conectado.
// Não bloqueia indefinidamente — o loop continua mesmo sem WiFi.
bool ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;

  Serial.printf("[WiFi] Sem conexão. Tentando %s...\n", WIFI_SSID);
  WiFi.disconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  for (int i = 0; i < 10; i++) {
    esp_task_wdt_reset();
    delay(1000);
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("[WiFi] Reconectado! IP: %s\n",
                    WiFi.localIP().toString().c_str());
      ntpSynced = false;  // força resync após reconexão
      syncNTP();
      return true;
    }
  }
  Serial.println("[WiFi] Falha. Gravando offline e tentando no proximo ciclo.");
  return false;
}


// -------------------------------------------------------
// Sincroniza clock interno via NTP (máx. 5s).
// Chamado após cada reconexão WiFi — fallback de timestamp quando GPS sem fix.
void syncNTP() {
  if (ntpSynced) return;   // já sincronizado — clock interno continua andando
  configTime(0, 0, NTP_SERVER1, NTP_SERVER2);  // UTC, sem DST
  struct tm t;
  for (int i = 0; i < 10; i++) {
    esp_task_wdt_reset();
    delay(500);
    if (getLocalTime(&t) && t.tm_year > 100) {  // ano > 2000
      ntpSynced = true;
      char buf[25];
      strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &t);
      Serial.printf("[NTP] Sincronizado: %s\n", buf);
      return;
    }
  }
  Serial.println("[NTP] Falha na sincronização. Tentando no proximo ciclo.");
}


// -------------------------------------------------------
// Tenta UMA conexão MQTT. Retorna true se conectado.
// Não bloqueia — se falhar, o loop continua e grava no buffer.
bool ensureMQTT() {
  if (mqttClient.connected()) return true;

  Serial.print("[MQTT] Tentando broker...");
  if (mqttClient.connect(DEVICE_ID, MQTT_USER, MQTT_PASS)) {
    Serial.println(" OK");
    return true;
  }
  Serial.printf(" Falha (rc=%d). Gravando offline.\n", mqttClient.state());
  return false;
}


// -------------------------------------------------------
// Salva payload JSON no buffer offline (SPIFFS)
void saveToBuffer(const char* payload) {
  if (SPIFFS.exists(BUFFER_FILE)) {
    File f = SPIFFS.open(BUFFER_FILE, "r");
    if (f && f.size() >= BUFFER_MAX_BYTES) {
      f.close();
      Serial.println("[Buffer] Cheio! Leitura descartada.");
      return;
    }
    if (f) f.close();
  }
  File f = SPIFFS.open(BUFFER_FILE, "a");
  if (!f) {
    Serial.println("[Buffer] Erro ao abrir arquivo!");
    return;
  }
  f.println(payload);
  f.close();
  Serial.println("[Buffer] Leitura salva offline.");
}


// -------------------------------------------------------
// Envia todas as leituras do buffer e remove o arquivo.
// Linhas com falha voltam ao buffer via arquivo temporário.
void flushBuffer() {
  if (!SPIFFS.exists(BUFFER_FILE)) return;

  // Aguarda conexão estabilizar antes de publicar
  delay(300);
  for (int i = 0; i < 3; i++) { mqttClient.loop(); delay(50); }

  if (!mqttClient.connected()) {
    Serial.println("[Buffer] Conexao perdeu antes do flush. Adiando.");
    return;
  }

  File src = SPIFFS.open(BUFFER_FILE, "r");
  if (!src) { Serial.println("[Buffer] Erro ao abrir buffer para leitura."); return; }

  size_t fileSize = src.size();
  Serial.printf("[Buffer] Iniciando flush — %u bytes no buffer.\n", fileSize);

  // Coleta todas as linhas em memória antes de apagar o arquivo
  std::vector<String> lines;
  while (src.available()) {
    String line = src.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) lines.push_back(line);
  }
  src.close();
  SPIFFS.remove(BUFFER_FILE);  // apaga agora — reescreve só o que falhar

  Serial.printf("[Buffer] %d leituras para enviar.\n", (int)lines.size());

  int published = 0;
  std::vector<String> failed;

  for (auto& line : lines) {
    esp_task_wdt_reset();
    mqttClient.loop();

    if (!mqttClient.connected()) {
      Serial.println("[Buffer] Conexao caiu durante flush. Salvando restantes.");
      failed.push_back(line);
      // adiciona as restantes também
      for (size_t j = &line - &lines[0] + 1; j < lines.size(); j++)
        failed.push_back(lines[j]);
      break;
    }

    bool ok = mqttClient.publish(TOPIC_READINGS, line.c_str(), true);
    Serial.printf("[Buffer] Linha %d/%d: %s\n",
                  published + (int)failed.size() + 1, (int)lines.size(),
                  ok ? "OK" : "FALHOU");
    if (ok) {
      published++;
      mqttClient.loop();
      delay(150);
    } else {
      failed.push_back(line);
    }
  }

  // Salva de volta as que falharam
  if (!failed.empty()) {
    File f = SPIFFS.open(BUFFER_FILE, "w");
    if (f) {
      for (auto& l : failed) f.println(l);
      f.close();
    }
    Serial.printf("[Buffer] Flush parcial: %d enviados, %d pendentes\n",
                  published, (int)failed.size());
  } else {
    Serial.printf("[Buffer] Flush completo: %d leituras enviadas\n", published);
  }
}


// -------------------------------------------------------
// Prioridade: GPS (mais preciso) → NTP (fallback) → vazio (Flask usa NOW())
String buildTimestamp() {
  // 1. GPS com fix válido
  if (gps.date.isValid() && gps.time.isValid() && gps.date.year() > 2000) {
    char buf[25];
    snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02dZ",
             gps.date.year(), gps.date.month(), gps.date.day(),
             gps.time.hour(), gps.time.minute(), gps.time.second());
    return String(buf);
  }
  // 2. NTP sincronizado — clock interno do ESP continua andando mesmo offline
  if (ntpSynced) {
    struct tm t;
    if (getLocalTime(&t) && t.tm_year > 100) {
      char buf[25];
      strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &t);
      return String(buf);
    }
  }
  // 3. Sem fonte de tempo — Flask normalizará para NOW()
  return "";
}


// -------------------------------------------------------
// Monta o payload JSON em buf — usado tanto para publish como para buffer
void buildPayload(float temp, float hum, char* buf, size_t bufLen) {
  StaticJsonDocument<512> doc;
  doc["device_id"]   = DEVICE_ID;
  doc["timestamp"]   = buildTimestamp();
  doc["temperature"] = isnan(temp) ? (float)0.0 : temp;
  doc["humidity"]    = isnan(hum)  ? (float)0.0 : hum;
  if (gps.location.isValid()) {
    doc["latitude"]   = gps.location.lat();
    doc["longitude"]  = gps.location.lng();
    doc["satellites"] = gps.satellites.isValid() ? (int)gps.satellites.value() : 0;
  } else {
    doc["latitude"]   = (float)0.0;
    doc["longitude"]  = (float)0.0;
    doc["satellites"] = 0;
  }
  doc["hmac"]  = "";
  doc["nonce"] = "";
  serializeJson(doc, buf, bufLen);
}


// -------------------------------------------------------
// Publica payload via MQTT — retorna true se sucesso
bool publishReading(const char* payload) {
  if (mqttClient.publish(TOPIC_READINGS, payload, true)) {
    Serial.print("[MQTT] Publicado: ");
    Serial.println(payload);
    return true;
  }
  Serial.println("[MQTT] Falha ao publicar!");
  return false;
}


// -------------------------------------------------------
void publishHeartbeat() {
  StaticJsonDocument<128> doc;
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = buildTimestamp();
  doc["status"]    = "online";

  char payload[128];
  serializeJson(doc, payload, sizeof(payload));
  mqttClient.publish(TOPIC_HEARTBEAT, payload);
  Serial.println("[MQTT] Heartbeat enviado.");
}


// -------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Vaccine Transport IoT M2 — Iniciando ===");

  // Inicializa hardware watchdog — reinicia o ESP32 se o loop travar
  // API IDF 5.x: recebe esp_task_wdt_config_t em vez de (timeout, panic)
  esp_task_wdt_deinit();  // garante estado limpo antes de configurar
  const esp_task_wdt_config_t wdt_config = {
    .timeout_ms     = WDT_TIMEOUT_SEC * 1000,
    .idle_core_mask = 0,      // não monitora idle tasks
    .trigger_panic  = true,   // reinicia o ESP32 ao disparar
  };
  esp_task_wdt_init(&wdt_config);
  esp_task_wdt_add(NULL);     // monitora a task atual (loop)
  Serial.printf("[WDT] Watchdog ativo — timeout: %ds\n", WDT_TIMEOUT_SEC);

  // Inicializa SPIFFS para buffer offline
  if (!SPIFFS.begin(true)) {
    Serial.println("[SPIFFS] Falha ao montar! Buffer offline indisponivel.");
  } else {
    size_t used  = SPIFFS.usedBytes();
    size_t total = SPIFFS.totalBytes();
    Serial.printf("[SPIFFS] Montado — %u KB usados / %u KB totais\n",
                  used / 1024, total / 1024);
    if (SPIFFS.exists(BUFFER_FILE)) {
      File f = SPIFFS.open(BUFFER_FILE, "r");
      Serial.printf("[SPIFFS] Buffer offline encontrado (%u bytes) — sera enviado ao conectar\n",
                    f ? (unsigned)f.size() : 0);
      if (f) f.close();
    }
  }

  dht.begin();
  SerialGPS.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  // Conecta WiFi no boot — tenta até 10s; se falhar, o loop tratará
  ensureWiFi();
  syncNTP();  // sincroniza clock logo no boot

  // Gerar device ID único a partir do MAC address
  // Formato: ESP32-AABBCCDDEEFF — sem hardcoding, único por hardware
  String mac = WiFi.macAddress();   // "AA:BB:CC:DD:EE:FF"
  mac.replace(":", "");             // "AABBCCDDEEFF"
  DEVICE_ID_STR = "ESP32-" + mac;
  DEVICE_ID = DEVICE_ID_STR.c_str();
  Serial.print("[Device] ID: ");
  Serial.println(DEVICE_ID);

  // TLS ativo — skip validação de certificado (HiveMQ rotaciona certs Let's Encrypt)
  wifiClientSecure.setInsecure();

  mqttClient.setBufferSize(768);
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  Serial.println("=== Sistema pronto (TLS ativo) ===\n");
}


// -------------------------------------------------------
void loop() {
  esp_task_wdt_reset();   // alimenta o watchdog — prova que o loop está vivo

  while (SerialGPS.available() > 0) {
    gps.encode(SerialGPS.read());
  }

  // Verifica conectividade — não bloqueante; falha → grava no buffer
  bool wifiOk = ensureWiFi();
  bool mqttOk = wifiOk && ensureMQTT();

  if (mqttOk) {
    mqttClient.loop();
    // Flush só quando acaba de reconectar (transição false → true)
    if (!prevMqttOk) {
      Serial.println("[MQTT] Reconectado! Aguardando subscribers reconectarem (5s)...");
      // QoS 0: broker não guarda mensagens. Aguardamos o Flask resubscrever
      // antes de publicar o buffer, senão as mensagens são perdidas.
      for (int i = 0; i < 50; i++) {
        esp_task_wdt_reset();
        mqttClient.loop();
        delay(100);
      }
      Serial.println("[MQTT] Verificando buffer offline...");
      flushBuffer();
    }
  }
  prevMqttOk = mqttOk;

  unsigned long now = millis();

  if (now - lastPublish >= PUBLISH_INTERVAL) {
    lastPublish = now;

    float hum  = dht.readHumidity();
    float temp = dht.readTemperature();

    if (isnan(hum) || isnan(temp)) {
      Serial.println("[DHT22] Falha na leitura!");
    } else {
      Serial.printf("[DHT22] Temp: %.1f°C | Umidade: %.1f%%\n", temp, hum);
    }

    if (gps.location.isValid()) {
      Serial.printf("[GPS] Lat: %.6f | Lng: %.6f | Sats: %d\n",
                    gps.location.lat(), gps.location.lng(),
                    gps.satellites.isValid() ? (int)gps.satellites.value() : 0);
    } else {
      Serial.println("[GPS] Aguardando fix...");
    }

    // Monta payload uma única vez — usado tanto para publish como para buffer
    char payload[512];
    buildPayload(temp, hum, payload, sizeof(payload));

    if (mqttOk) {
      if (!publishReading(payload)) {
        saveToBuffer(payload);  // publish falhou → guarda localmente
      }
    } else {
      saveToBuffer(payload);    // sem conexão → guarda localmente
      Serial.println("[Modo offline] Leitura armazenada no SPIFFS.");
    }
  }

  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = now;
    if (mqttOk) publishHeartbeat();
  }
}
