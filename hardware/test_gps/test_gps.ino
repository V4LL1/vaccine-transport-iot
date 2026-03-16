#include <TinyGPS++.h>
#include <HardwareSerial.h>

TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

unsigned long lastDebug = 0;
unsigned long bytesRecebidos = 0;

void setup() {

  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("=================================");
  Serial.println("TESTE GPS NEO-6M + ESP32");
  Serial.println("=================================");

  Serial.println("Inicializando UART2...");
  Serial.println("RX -> GPIO16");
  Serial.println("TX -> GPIO17");
  Serial.println("Baudrate -> 9600");
  Serial.println();

  gpsSerial.begin(9600, SERIAL_8N1, 16, 17);

  Serial.println("Aguardando dados do GPS...");
  Serial.println();
}

void loop() {

  while (gpsSerial.available()) {

    char c = gpsSerial.read();
    bytesRecebidos++;

    Serial.write(c);   // mostra dados NMEA crus
    gps.encode(c);
  }

  if (gps.location.isUpdated()) {

    Serial.println();
    Serial.println("------ GPS FIX ------");

    Serial.print("Latitude: ");
    Serial.println(gps.location.lat(), 6);

    Serial.print("Longitude: ");
    Serial.println(gps.location.lng(), 6);

    Serial.print("Satélites: ");
    Serial.println(gps.satellites.value());

    Serial.print("Altitude: ");
    Serial.println(gps.altitude.meters());

    Serial.println("---------------------");
    Serial.println();
  }

  if (millis() - lastDebug > 5000) {

    Serial.println();
    Serial.println("----- DEBUG STATUS -----");

    Serial.print("Bytes recebidos: ");
    Serial.println(bytesRecebidos);

    if (bytesRecebidos == 0) {
      Serial.println("ERRO: Nenhum dado chegou do GPS");
      Serial.println("Verifique TX/RX");
    }

    Serial.println("------------------------");
    Serial.println();

    lastDebug = millis();
  }
}
