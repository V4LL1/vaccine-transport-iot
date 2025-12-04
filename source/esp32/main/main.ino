#include <DHT.h>
#include <TinyGPS++.h>

// ======== CONFIG DHT22 ========
#define DHTPIN 4        // GPIO do ESP32 conectado ao DHT
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// ======== CONFIG GPS ========
TinyGPSPlus gps;
HardwareSerial SerialGPS(1);  // Usar UART 1 do ESP32

// GPS conectado em 16 (RX) / 17 (TX)
#define GPS_RX_PIN 16  
#define GPS_TX_PIN 17  
#define GPS_BAUD 9600

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Inicializando sensores...\n");

  // DHT22
  dht.begin();

  // GPS
  SerialGPS.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  Serial.println("Sistema iniciado.\n");
}

void loop() {
  // ========================
  // LER DHT22
  // ========================
  float hum = dht.readHumidity();
  float temp = dht.readTemperature();

  if (isnan(hum) || isnan(temp)) {
    Serial.println("[DHT22] Falha na leitura!");
  } else {
    Serial.print("[DHT22] Temperatura: ");
    Serial.print(temp);
    Serial.print(" °C | Umidade: ");
    Serial.print(hum);
    Serial.println(" %");
  }

  // ========================
  // LER GPS
  // ========================
  while (SerialGPS.available() > 0) {
    gps.encode(SerialGPS.read());
  }

  if (gps.location.isValid()) {
    Serial.print("[GPS] Latitude: ");
    Serial.println(gps.location.lat(), 6);

    Serial.print("[GPS] Longitude: ");
    Serial.println(gps.location.lng(), 6);
  } else {
    Serial.println("[GPS] Localização ainda não obtida...");
  }

  if (gps.satellites.isValid()) {
    Serial.print("[GPS] Satélites: ");
    Serial.println(gps.satellites.value());
  }

  if (gps.speed.isValid()) {
    Serial.print("[GPS] Velocidade: ");
    Serial.print(gps.speed.kmph());
    Serial.println(" km/h");
  }

  if (gps.time.isValid()) {
    Serial.print("[GPS] Hora UTC: ");
    Serial.printf("%02d:%02d:%02d\n",
                  gps.time.hour(),
                  gps.time.minute(),
                  gps.time.second());
  }

  Serial.println("---------------------------------------\n");
  delay(2000);
}
