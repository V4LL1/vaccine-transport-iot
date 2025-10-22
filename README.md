# Secure IoT System for Monitoring, Control, and Tracking of Vaccine Transport with Batch ID and Delivery Token

## Project Overview
This project presents a secure IoT system designed for monitoring, controlling, and tracking vaccine transport. The system uses ESP32 devices equipped with temperature, humidity, and GPS sensors to generate critical data, including a **unique batch identifier and delivery token**, which are transmitted securely via MQTT.  

The project integrates advanced security measures, such as TLS mutual authentication, X.509 certificates, HMAC signatures, replay attack protection, and role-based access control (RBAC) with multi-factor authentication (MFA). Continuity and resilience mechanisms, including broker failover, encrypted backups, and power redundancy, are also implemented.

---

## Objectives

### General Objective
Develop a **secure and resilient IoT system** for vaccine transport, capable of generating and transmitting sensitive data (batch ID + delivery token) via MQTT while ensuring **confidentiality, integrity, and availability**.

### Specific Objectives
- Implement secure communication between ESP32 and the server using MQTT over TLS with mutual authentication.
- Generate sensitive data (batch ID + delivery token) on the ESP32 and transmit it encrypted.
- Apply digital signatures (HMAC/SHA256) to ensure message integrity and authentication.
- Protect against replay attacks using timestamps and nonces.
- Harden the MQTT/HTTP broker by disabling unnecessary ports/protocols, enforcing strong authentication, and using access control lists (ACLs).
- Apply RBAC and MFA on the dashboard and control interfaces.
- Rotate keys and X.509 certificates periodically.
- Encrypt all sensitive data, including sensor readings, batch ID, and delivery token.
- Implement business continuity and disaster recovery strategies, including broker failover, encrypted backups, and power redundancy.
- Build a secure dashboard for real-time monitoring of metrics, location, system status, and continuity indicators.
- Test security and resilience through sniffing, MITM, DDoS, and unauthorized access attempts.
- Evaluate the impact of security measures on confidentiality, integrity, availability, and overall system reliability.

---


