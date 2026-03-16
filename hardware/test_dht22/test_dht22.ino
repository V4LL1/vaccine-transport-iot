#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

int leitura = 0;
int falhas = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("=================================");
  Serial.println("INICIANDO TESTE DO SENSOR DHT22");
  Serial.println("=================================");

  Serial.print("Pino de dados: ");
  Serial.println(DHTPIN);

  Serial.print("Tipo de sensor: ");
  Serial.println("DHT22");

  Serial.println("Inicializando sensor...");
  dht.begin();

  Serial.println("Aguarde as leituras...");
  Serial.println();
}

void loop() {

  leitura++;

  Serial.println("---------------------------------");
  Serial.print("Leitura numero: ");
  Serial.println(leitura);

  Serial.println("Lendo sensor...");

  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {

    falhas++;

    Serial.println("ERRO: Falha na leitura do DHT22");
    Serial.print("Total de falhas: ");
    Serial.println(falhas);

    Serial.println();
    Serial.println("Possiveis causas:");
    Serial.println("1 - Sensor mal conectado");
    Serial.println("2 - Falta de resistor pull-up (4.7k a 10k)");
    Serial.println("3 - Pino errado configurado");
    Serial.println("4 - Sensor queimado");
    Serial.println("5 - Intervalo de leitura muito curto");

  } else {

    Serial.println("Leitura OK!");

    Serial.print("Temperatura: ");
    Serial.print(t);
    Serial.println(" C");

    Serial.print("Umidade: ");
    Serial.print(h);
    Serial.println(" %");

    Serial.print("Falhas acumuladas: ");
    Serial.println(falhas);
  }

  Serial.println("---------------------------------");
  Serial.println();

  delay(3000);  // DHT22 precisa de pelo menos 2 segundos
}