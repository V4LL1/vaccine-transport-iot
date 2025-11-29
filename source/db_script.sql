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
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','operator') DEFAULT 'operator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- DEVICES TABLE
-- ============================
CREATE TABLE devices (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    status ENUM('active','inactive') DEFAULT 'active',
    last_seen DATETIME NULL
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
    device_id INT NOT NULL,
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







USE vaccine_transport;

-- ==========================================================
-- 0. LIMPEZA (Opcional: remove dados antigos se existirem)
-- ==========================================================
SET FOREIGN_KEY_CHECKS = 0;
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
INSERT INTO users (name, email, password_hash, role) VALUES
('Carlos Silva', 'admin@logistica.com', 'hash_segura_123', 'admin'),
('Maria Oliveira', 'maria@transporte.com', 'hash_operador_456', 'operator'),
('João Santos', 'joao@transporte.com', 'hash_operador_789', 'operator'),
('Ana Costa', 'ana@monitoramento.com', 'hash_operador_000', 'operator');

-- ============================
-- 2. POPULAR DISPOSITIVOS
-- ============================
INSERT INTO devices (serial_number, status) VALUES
('IOT-GPS-001', 'active'),
('IOT-GPS-002', 'active'),
('IOT-GPS-003', 'inactive'), -- Um dispositivo em manutenção
('IOT-GPS-004', 'active'),
('IOT-TEMP-X99', 'active');

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



