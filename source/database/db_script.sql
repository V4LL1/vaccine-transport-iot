-- ===========================================
-- DATABASE FOR SECURE IoT VACCINE TRANSPORT
-- ===========================================

DROP DATABASE IF EXISTS vaccine_transport;
CREATE DATABASE vaccine_transport;
USE vaccine_transport;

-- ============================
-- USERS TABLE
-- ============================
CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin','operator') DEFAULT 'operator',
    totp_secret   VARCHAR(32) NULL,          -- Chave TOTP (M2 — MFA)
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- DEVICES TABLE
-- ============================
CREATE TABLE devices (
    device_id           INT AUTO_INCREMENT PRIMARY KEY,
    serial_number       VARCHAR(100) UNIQUE NOT NULL,
    name                VARCHAR(100) NULL,              -- Nome amigável (definido pelo admin no registro)
    status              ENUM('active','inactive') DEFAULT 'active',
    registration_status ENUM('pending','active','inactive') NOT NULL DEFAULT 'pending',
    registered_by       INT NULL,                       -- FK para users (quem registrou)
    registered_at       DATETIME NULL,
    last_seen           DATETIME NULL,
    FOREIGN KEY (registered_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ============================
-- VACCINES TABLE
-- ============================
CREATE TABLE vaccines (
    vaccine_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    manufacturer VARCHAR(150),
    min_temp DECIMAL(5,2) NOT NULL,
    max_temp DECIMAL(5,2) NOT NULL
);

-- ============================
-- VACCINE BATCH TABLE
-- ============================
CREATE TABLE vaccine_batch (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    vaccine_id INT NOT NULL,
    batch_code VARCHAR(150) UNIQUE NOT NULL,
    expiration_date DATE NOT NULL,
    quantity_units INT NOT NULL,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(vaccine_id)
);

-- ============================
-- TRIPS TABLE
-- ============================
CREATE TABLE trips (
    trip_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    device_id INT NULL,   -- NULL até admin registrar o ESP32 na viagem
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    origin VARCHAR(200) NOT NULL,
    destination VARCHAR(200) NOT NULL,
    received_confirmation BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (batch_id) REFERENCES vaccine_batch(batch_id),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- ============================
-- READINGS TABLE
-- ============================
CREATE TABLE readings (
    reading_id INT AUTO_INCREMENT PRIMARY KEY,
    trip_id INT NOT NULL,
    batch_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    humidity DECIMAL(5,2) NOT NULL,
    latitude DECIMAL(10,7) NULL,
    longitude DECIMAL(10,7) NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    FOREIGN KEY (batch_id) REFERENCES vaccine_batch(batch_id)
);

-- ============================
-- AUDIT LOG TABLE (M1+)
-- Registra ações relevantes do sistema para rastreabilidade
-- ============================
CREATE TABLE audit_log (
    log_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NULL,                        -- NULL = ação do sistema/IoT
    action       VARCHAR(100) NOT NULL,           -- Ex: 'login', 'trip_start', 'alarm_ack'
    target_table VARCHAR(50)  NULL,               -- Tabela afetada
    target_id    INT          NULL,               -- ID do registro afetado
    ip_address   VARCHAR(45)  NULL,
    details      TEXT         NULL,               -- JSON com detalhes adicionais
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ============================
-- SEEN NONCES TABLE (M2)
-- Usada para mitigação de replay attacks
-- Populada no Milestone 2 com validação HMAC
-- ============================
CREATE TABLE seen_nonces (
    nonce       VARCHAR(64) NOT NULL PRIMARY KEY,
    device_id   VARCHAR(100) NOT NULL,
    received_at DATETIME NOT NULL,
    INDEX idx_received_at (received_at)   -- Para limpeza periódica eficiente
);







USE vaccine_transport;

-- ==========================================================
-- 0. LIMPEZA (Opcional: remove dados antigos se existirem)
-- ==========================================================
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE seen_nonces;
TRUNCATE TABLE audit_log;
TRUNCATE TABLE readings;
TRUNCATE TABLE trips;
TRUNCATE TABLE vaccine_batch;
TRUNCATE TABLE vaccines;
TRUNCATE TABLE devices;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================
-- 1. POPULAR USUÁRIOS
-- ============================
-- Senhas bcrypt geradas com: python -c "import bcrypt; print(bcrypt.hashpw(b'senha', bcrypt.gensalt()).decode())"
-- admin123  → hash abaixo
-- op123     → hash abaixo
INSERT INTO users (name, email, password_hash, role) VALUES
('Carlos Silva',  'admin@logistica.com',    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36DQBuMpV9h.L7MfxlJiUAy', 'admin'),
('Maria Oliveira','maria@transporte.com',   '$2b$12$I5vqwLXClQELkxIGGEQUOuqUMt4TKdR9W.8jGaqyK9TKNiJHPWIJa', 'operator'),
('João Santos',   'joao@transporte.com',    '$2b$12$I5vqwLXClQELkxIGGEQUOuqUMt4TKdR9W.8jGaqyK9TKNiJHPWIJa', 'operator'),
('Ana Costa',     'ana@monitoramento.com',  '$2b$12$I5vqwLXClQELkxIGGEQUOuqUMt4TKdR9W.8jGaqyK9TKNiJHPWIJa', 'operator');

-- ============================
-- 2. POPULAR DISPOSITIVOS (seed — pré-registrados)
-- Dispositivos reais são descobertos automaticamente via MQTT
-- e registrados pelo admin pelo dashboard
-- ============================
INSERT INTO devices (serial_number, name, status, registration_status) VALUES
('IOT-GPS-001',  'Caminhão Refrigerado #1', 'active',   'active'),
('IOT-GPS-002',  'Caminhão Refrigerado #2', 'active',   'active'),
('IOT-GPS-003',  'Sensor Ultracongelado',   'inactive', 'inactive'),
('IOT-GPS-004',  'Carga Moderna SP',        'active',   'active'),
('IOT-TEMP-X99', 'Sensor Externo Teste',    'active',   'active');

-- ============================
-- 3. POPULAR VACINAS (Tipos Reais)
-- ============================
INSERT INTO vaccines (name, manufacturer, min_temp, max_temp) VALUES
('Comirnaty (COVID-19)', 'Pfizer/BioNTech', -80.00, -60.00), -- Ultra-frio
('Vaxzevria', 'AstraZeneca', 2.00, 8.00),                 -- Geladeira comum
('CoronaVac', 'Sinovac', 2.00, 8.00),                     -- Geladeira comum
('Janssen', 'Johnson & Johnson', 2.00, 8.00),
('Spikevax', 'Moderna', -25.00, -15.00);                  -- Congelado

-- ============================
-- 4. POPULAR LOTES
-- ============================
INSERT INTO vaccine_batch (vaccine_id, batch_code, expiration_date, quantity_units) VALUES
(1, 'PFZ-2025-A01', '2025-12-31', 5000), -- Pfizer
(2, 'AZ-2024-B99', '2024-10-20', 10000), -- AstraZeneca
(1, 'PFZ-2025-C03', '2025-11-15', 3000), -- Pfizer
(5, 'MOD-2025-X12', '2025-06-30', 4500); -- Moderna

-- ============================
-- 5. POPULAR VIAGENS (TRIPS)
-- ============================
-- Viagem 1: Pfizer (Ultra-frio) - Concluída
INSERT INTO trips (batch_id, device_id, start_time, end_time, origin, destination, received_confirmation) VALUES
(1, 1, '2023-10-01 08:00:00', '2023-10-01 14:00:00', 'CD São Paulo', 'Hospital das Clínicas', TRUE);

-- Viagem 2: AstraZeneca (Refrigerado) - Concluída
INSERT INTO trips (batch_id, device_id, start_time, end_time, origin, destination, received_confirmation) VALUES
(2, 2, '2023-10-02 06:00:00', '2023-10-02 18:00:00', 'Fabrica Fiocruz', 'CD Rio de Janeiro', TRUE);

-- Viagem 3: Moderna (Congelado) - EM ANDAMENTO (end_time NULL)
INSERT INTO trips (batch_id, device_id, start_time, end_time, origin, destination, received_confirmation) VALUES
(4, 4, NOW() - INTERVAL 4 HOUR, NULL, 'Aeroporto Guarulhos', 'Interior SP - Campinas', FALSE);



