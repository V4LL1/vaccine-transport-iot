#include <WiFi.h>

const char* ssid = "Quartos";      // Nome da rede do seu celular
const char* password = "Controle0123"; // Senha do hotspot

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Conectando ao Wi-Fi...");

  WiFi.begin(ssid, password);

  // Tentativas até conectar
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
    tentativas++;

    if (tentativas > 20) {
      Serial.println("\nFalha ao conectar! Reiniciando...");
      ESP.restart();
    }
  }

  Serial.println("\nConectado com sucesso!");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Mostrar status da conexão
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ Wi-Fi perdido! Tentando reconectar...");
    WiFi.reconnect();
  }

  delay(3000);
}
