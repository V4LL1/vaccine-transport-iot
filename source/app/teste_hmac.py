import paho.mqtt.client as mqtt
import json, ssl, time

BROKER   = "1fe6e4dc6c3b41d193f6448d1ab84a93.s1.eu.hivemq.cloud"
PORT     = 8883
USER     = "esp32-device"
PASSWORD = "Esp32Mqtt@2026"

payload = {
    "device_id":   "ATACANTE-001",
    "timestamp":   "2026-04-18T14:00:00Z",
    "temperature": 99.9,
    "humidity":    50.0,
    "latitude":    0.0,
    "longitude":   0.0,
    "satellites":  0,
    "nonce":       "aaaaaaaaaaaaaaaa",
    "signed":      '{"device_id":"ATACANTE-001","temperature":99.9}',
    "hmac":        "0000000000000000000000000000000000000000000000000000000000000000"
}

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.connect(BROKER, PORT)
client.publish("vaccines/readings", json.dumps(payload))
time.sleep(1)
client.disconnect()
print("Mensagem adulterada enviada — verifique o log do Flask.")
