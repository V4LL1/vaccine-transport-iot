// DHT22 serial test for ESP32
#include <DHT.h>
#include <Adafruit_Sensor.h>

// ----- CONFIG -----
#define DHTPIN 23        // GPIO where DATA pin is connected
#define DHTTYPE DHT22   // DHT 22 (AM2302)

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("DHT22 test - ESP32");

  dht.begin();
}

void loop() {
  // The sensor requires ~2s between readings
  delay(2000);

  float h = dht.readHumidity();
  float t = dht.readTemperature(); // Celsius
  float f = dht.readTemperature(true); // Fahrenheit (if needed)

  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor! Check wiring.");
    continue;
  }

  // Print to serial
  Serial.print("Temperature: ");
  Serial.print(t, 2);
  Serial.print(" °C\t");

  Serial.print("Humidity: ");
  Serial.print(h, 2);
  Serial.println(" %");

  // Optionally print timestamp (ms since boot)
  Serial.print("Millis: ");
  Serial.println(millis());
}
