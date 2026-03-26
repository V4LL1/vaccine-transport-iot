#include <WiFi.h>

const char* ssid = "iPhone-Gui";
const char* password = "hash1234";

void printStatus(int status) {
  Serial.print("Status WiFi: ");
  Serial.print(status);
  Serial.print(" -> ");

  switch (status) {
    case WL_IDLE_STATUS: Serial.println("IDLE"); break;
    case WL_NO_SSID_AVAIL: Serial.println("SSID NAO ENCONTRADO"); break;
    case WL_SCAN_COMPLETED: Serial.println("SCAN COMPLETO"); break;
    case WL_CONNECTED: Serial.println("CONECTADO"); break;
    case WL_CONNECT_FAILED: Serial.println("FALHA NA CONEXAO"); break;
    case WL_CONNECTION_LOST: Serial.println("CONEXAO PERDIDA"); break;
    case WL_DISCONNECTED: Serial.println("DESCONECTADO"); break;
    default: Serial.println("DESCONHECIDO"); break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("\n=== DEBUG WIFI ESP32 ===\n");

  // Reset WiFi
  WiFi.disconnect(true);
  delay(1000);
  WiFi.mode(WIFI_STA);

  // 🔍 Scan redes
  Serial.println("Escaneando redes...");
  int n = WiFi.scanNetworks();

  if (n == 0) {
    Serial.println("Nenhuma rede encontrada");
  } else {
    Serial.println("Redes encontradas:");
    for (int i = 0; i < n; ++i) {
      Serial.print("- ");
      Serial.print(WiFi.SSID(i));
      Serial.print(" | RSSI: ");
      Serial.print(WiFi.RSSI(i));
      Serial.print(" | Seguranca: ");
      Serial.println(WiFi.encryptionType(i));
    }
  }

  Serial.println("\nTentando conectar...\n");

  // 🔌 Conexão
  WiFi.begin(ssid, password);

  int tentativas = 0;

  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    printStatus(WiFi.status());
    delay(1000);
    tentativas++;
  }

  Serial.println("\n=== RESULTADO ===");

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✅ CONECTADO COM SUCESSO!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("❌ NAO CONECTOU");
    printStatus(WiFi.status());
  }
}

void loop() {}