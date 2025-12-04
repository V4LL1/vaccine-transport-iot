#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  Serial.println("Testando DHT22...");
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("Falha na leitura do DHT22");
  } else {
    Serial.print("Temp: "); Serial.print(t);
    Serial.print(" °C | Umidade: "); Serial.println(h);
  }

  delay(2000);
}
