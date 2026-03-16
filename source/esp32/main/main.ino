// ============================================================
// Vaccine Transport IoT — Firmware ESP32
// Milestone 2: TLS/SSL + Credenciais MQTT + HMAC + Nonce
// ============================================================

#define MQTT_MAX_PACKET_SIZE 768   // Maior por causa do HMAC

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <TinyGPS++.h>
#include "mbedtls/md.h"     // HMAC-SHA256

// ======== CONFIGURAÇÕES — ALTERE ANTES DE GRAVAR ========
const char* WIFI_SSID     = "Quartos";
const char* WIFI_PASSWORD = "Controle0123";
const char* MQTT_BROKER   = "10.0.0.175";
const int   MQTT_PORT     = 8883;            // TLS

// Credenciais MQTT (devem coincidir com mosquitto/passwd)
const char* MQTT_USER     = "esp32-device";
const char* MQTT_PASS     = "Esp32Mqtt@2026";

// Chave HMAC-SHA256 (32 bytes) — compartilhada com o servidor
// Em produção: armazenar no NVS via Preferences.h
const char* HMAC_KEY      = "v@ccine-hmac-key-2026-xK9mP7qR!";
// =========================================================

// Identificação do dispositivo/viagem
const char* DEVICE_ID   = "IOT-GPS-004";
const int   TRIP_ID     = 3;

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
MIIF6zCCA9OgAwIBAgIUeQhtIbF2/Z3rdrdlwk7KHKFmBlYwDQYJKoZIhvcNAQEL
BQAwfTELMAkGA1UEBhMCQlIxCzAJBgNVBAgMAlNQMREwDwYDVQQHDAhDYW1waW5h
czEZMBcGA1UECgwQVmFjY2luZVRyYW5zcG9ydDEVMBMGA1UECwwMSW9ULVNlY3Vy
aXR5MRwwGgYDVQQDDBNWYWNjaW5lVHJhbnNwb3J0LUNBMB4XDTI2MDMxNTE0MzA1
OFoXDTM2MDMxMjE0MzA1OFowfTELMAkGA1UEBhMCQlIxCzAJBgNVBAgMAlNQMREw
DwYDVQQHDAhDYW1waW5hczEZMBcGA1UECgwQVmFjY2luZVRyYW5zcG9ydDEVMBMG
A1UECwwMSW9ULVNlY3VyaXR5MRwwGgYDVQQDDBNWYWNjaW5lVHJhbnNwb3J0LUNB
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAniFf2lJAoGxr6ixXf/mr
dsfKyEQzgQFzQf8pl8ZS9iOQoGj+gdnjsQVDrmF5FT+r8SR/gvxULmiaA7xhpLkn
/MERy4UxSTgQGzZ4cz0qd9SWVGsmcYgzQiDP3LDxBLHAysR9XukpuNaVEmr2P5Y9
8Y9pByBMYT+zwe6tBkl4uubMFy3va2Jdy+qtCNySaKzfL9SG06n/CuFD09f6r6pv
j93fcZD2Hw2c27qnYWEbJwdf7GGOaM99RuAiE3BOW3P0b75jSoz4nRmbURNKgbOY
25BK+VLzh4REUrhKgTsDZF5YnyO70xQCg70WIkKDDxVhe97RM3o8x1KwL/xKy2rw
L+A5hl8AAOwYUblhlTo1n+2LTs6aClH/NO8tSXrCb7J+0rb+5CAoA4H8bU5MJ39m
VI4ciSwadAoEjXtyPG3Jqgwxye7QEV6XadA6LMn1FZJ5nvcqn27RM+DQlLASEK7n
r1cmNmjjAsUIE4F3yi4Qzr2WEc3eysJXIMGAqM2Z8e2PSi5RU76Ho7aP0EKtKcTq
YbD7aSbcNcrOu1qciL26FNx3Vu3PuRLkh/M0khllNvWVTS5c99oF717KAk8LTwh2
POYsL5edCdkvuxfpCRBvC3gbr8mMxeG4FSoixtTSWAsUp11lBBgvUJJNz0gvd2Jr
NlNiWna6gN1H2huOmTivObsCAwEAAaNjMGEwHQYDVR0OBBYEFJg4odf5zH4khFpb
VBq+dINaNQaDMB8GA1UdIwQYMBaAFJg4odf5zH4khFpbVBq+dINaNQaDMA8GA1Ud
EwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgGGMA0GCSqGSIb3DQEBCwUAA4ICAQAb
afdRYjC5Ew31fZXkCdPc34EYf0E352x8fieFWh2MP4NovmtOcyy7H70WaiwTXow2
BNR5UH8RZR+V/BVKf+LxZOBcF5TLyIju2GejK65+WCpraSHl2ZdScWiQvAXZf0E1
/yJpbk7gRJ82lwAwqbnNKmaC/reyK3SJfMzlKlVTT8HIrVhIDSfQWTcWN051Le5L
eZySJUTLJzJAQxa7qJSPyPXm89zG1wFU0SzQftvI7b1nD+ZX4QyNuPMW3KCWwvQE
reTMofhi/F2eg6thZdXLO2LRdTqKPPu5fAtWSZnVI7UwaT1HSrYUu/Rzof060j/5
qws64sCw9eB9l68mh4+x3Y0YN2LgCQYCv5RB3jWN7hTL8BsiiiTTiZiiiNwHnvrV
GQnCycZZIgf7z+OKvL1aDQYvJG+GoN1Fn50MjEcbY1roFSIzqAxqSLE5ilLT3ZJF
ajhle3c9+k3kt00DKU7wkau2TM/A8VLaBuwOQcDlWv6XdgvSG7gTJKjx+JemHEJZ
mSEFOnbyG5TpQue0NeFTqyETQKjgF6xffCCZemBU79FV0FmpDio5AVdVLcUYuX+r
U2nD/MqbRPCL1F3cQysAOiWQ5RLw/8ERZgd+6afpcNPh7mT6A6vkshrC5RQK5CFc
AcIP2D9H/pr6/yFjxGwAl9ig2xdAYW5IOUW3xqPYtQ==
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

// Controle de tempo
unsigned long lastPublish   = 0;
unsigned long lastHeartbeat = 0;


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
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("[WiFi] Conectando a ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
    tentativas++;
    if (tentativas > 20) {
      Serial.println("\n[WiFi] Falha! Reiniciando...");
      ESP.restart();
    }
  }
  Serial.println();
  Serial.print("[WiFi] Conectado! IP: ");
  Serial.println(WiFi.localIP());
}


// -------------------------------------------------------
void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Conectando ao broker (TLS)...");

    // Conecta com credenciais
    if (mqttClient.connect(DEVICE_ID, MQTT_USER, MQTT_PASS)) {
      Serial.println(" OK");
    } else {
      Serial.print(" Falha (rc=");
      Serial.print(mqttClient.state());
      Serial.println("). Tentando em 3s...");
      delay(3000);
    }
  }
}


// -------------------------------------------------------
String buildTimestamp() {
  if (gps.date.isValid() && gps.time.isValid()) {
    char buf[25];
    snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02dZ",
             gps.date.year(), gps.date.month(), gps.date.day(),
             gps.time.hour(), gps.time.minute(), gps.time.second());
    return String(buf);
  }
  return "";
}


// -------------------------------------------------------
void publishReading(float temp, float hum) {
  String nonce = generateNonce();
  String ts    = buildTimestamp();

  // Monta payload parcial para calcular HMAC
  // Formato: device_id|trip_id|timestamp|temperature|humidity|nonce
  String hmacData = String(DEVICE_ID) + "|" +
                    String(TRIP_ID) + "|" +
                    ts + "|" +
                    String(temp, 2) + "|" +
                    String(hum, 2) + "|" +
                    nonce;
  String hmac = computeHMAC(hmacData);

  StaticJsonDocument<512> doc;
  doc["device_id"]   = DEVICE_ID;
  doc["trip_id"]     = TRIP_ID;
  doc["timestamp"]   = ts;
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

  doc["hmac"]  = hmac;
  doc["nonce"] = nonce;

  char payload[512];
  serializeJson(doc, payload, sizeof(payload));

  if (mqttClient.publish(TOPIC_READINGS, payload)) {
    Serial.print("[MQTT] Publicado: ");
    Serial.println(payload);
  } else {
    Serial.println("[MQTT] Falha ao publicar!");
  }
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

  dht.begin();
  SerialGPS.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  connectWiFi();

  // Configurar TLS com o certificado da CA
  wifiClientSecure.setCACert(CA_CERT);

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  Serial.println("=== Sistema pronto (TLS ativo) ===\n");
}


// -------------------------------------------------------
void loop() {
  while (SerialGPS.available() > 0) {
    gps.encode(SerialGPS.read());
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Conexão perdida. Reconectando...");
    connectWiFi();
  }
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

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

    publishReading(temp, hum);
  }

  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = now;
    publishHeartbeat();
  }
}
