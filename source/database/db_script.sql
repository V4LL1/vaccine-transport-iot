-- ===========================================
-- DATABASE FOR SECURE IoT VACCINE TRANSPORT
-- RBAC Multi-Empresa: superadmin / admin / operator
-- ===========================================

DROP DATABASE IF EXISTS vaccine_transport;
CREATE DATABASE vaccine_transport;
USE vaccine_transport;

-- ============================
-- COMPANIES TABLE
-- ============================
CREATE TABLE companies (
    company_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    cnpj        VARCHAR(18)  NULL UNIQUE,
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- USERS TABLE
-- ============================
CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('superadmin','admin','operator') NOT NULL DEFAULT 'operator',
    company_id    INT NULL,                -- NULL apenas para superadmin
    totp_secret   VARCHAR(32) NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL
);

-- ============================
-- DEVICES TABLE
-- ============================
CREATE TABLE devices (
    device_id           INT AUTO_INCREMENT PRIMARY KEY,
    company_id          INT NULL,
    serial_number       VARCHAR(100) UNIQUE NOT NULL,
    name                VARCHAR(100) NULL,
    status              ENUM('active','inactive') DEFAULT 'active',
    registration_status ENUM('pending','active','inactive') NOT NULL DEFAULT 'pending',
    registered_by       INT NULL,
    registered_at       DATETIME NULL,
    last_seen           DATETIME NULL,
    FOREIGN KEY (company_id)    REFERENCES companies(company_id) ON DELETE SET NULL,
    FOREIGN KEY (registered_by) REFERENCES users(user_id)     ON DELETE SET NULL
);

-- ============================
-- VACCINES TABLE
-- ============================
CREATE TABLE vaccines (
    vaccine_id  INT AUTO_INCREMENT PRIMARY KEY,
    company_id  INT NOT NULL,
    name        VARCHAR(150) NOT NULL,
    manufacturer VARCHAR(150),
    min_temp    DECIMAL(5,2) NOT NULL,
    max_temp    DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- ============================
-- VACCINE BATCH TABLE
-- ============================
CREATE TABLE vaccine_batch (
    batch_id        INT AUTO_INCREMENT PRIMARY KEY,
    vaccine_id      INT NOT NULL,
    batch_code      VARCHAR(150) UNIQUE NOT NULL,
    expiration_date DATE NOT NULL,
    quantity_units  INT NOT NULL,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(vaccine_id)
);

-- ============================
-- TRIPS TABLE
-- ============================
CREATE TABLE trips (
    trip_id               INT AUTO_INCREMENT PRIMARY KEY,
    batch_id              INT NOT NULL,
    device_id             INT NULL,
    start_time            DATETIME NOT NULL,
    end_time              DATETIME NULL,
    origin                VARCHAR(200) NOT NULL,
    destination           VARCHAR(200) NOT NULL,
    received_confirmation BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (batch_id)  REFERENCES vaccine_batch(batch_id),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- ============================
-- READINGS TABLE
-- ============================
CREATE TABLE readings (
    reading_id  INT AUTO_INCREMENT PRIMARY KEY,
    trip_id     INT NOT NULL,
    batch_id    INT NOT NULL,
    timestamp   DATETIME NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    humidity    DECIMAL(5,2) NOT NULL,
    latitude    DECIMAL(10,7) NULL,
    longitude   DECIMAL(10,7) NULL,
    FOREIGN KEY (trip_id)  REFERENCES trips(trip_id),
    FOREIGN KEY (batch_id) REFERENCES vaccine_batch(batch_id)
);

-- ============================
-- AUDIT LOG TABLE
-- ============================
CREATE TABLE audit_log (
    log_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NULL,
    action       VARCHAR(100) NOT NULL,
    target_table VARCHAR(50)  NULL,
    target_id    INT          NULL,
    ip_address   VARCHAR(45)  NULL,
    details      TEXT         NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ============================
-- SEEN NONCES TABLE
-- ============================
CREATE TABLE seen_nonces (
    nonce       VARCHAR(64) NOT NULL PRIMARY KEY,
    device_id   VARCHAR(100) NOT NULL,
    received_at DATETIME NOT NULL,
    INDEX idx_received_at (received_at)
);


-- ==========================================================
-- SEED DATA
-- ==========================================================

-- ============================
-- 1. EMPRESAS
-- ============================
INSERT INTO companies (company_id, name, cnpj) VALUES
(1, 'PharmaTransport Logística', '12.345.678/0001-99'),
(2, 'BioFrio Distribuidora',     '98.765.432/0001-11');

-- ============================
-- 2. USUÁRIOS
-- Senhas:
--   admin123 → $2b$12$DYkfTREXJTBJHd3g57UG4OcKnsYehLUT7vVY60Wh4UeGNYJ5yJTpC
--   op123    → $2b$12$MpGgyanpzh8ltYYJncGR2OlHgcznn62D7mVcY08uV4auSXNVb2BZu
-- ============================

-- Superadmin — sem empresa (acesso global)
INSERT INTO users (name, email, password_hash, role, company_id) VALUES
('Guilherme (Dev)', 'guilherme.palmanhani@gmail.com',
 '$2b$12$DYkfTREXJTBJHd3g57UG4OcKnsYehLUT7vVY60Wh4UeGNYJ5yJTpC',
 'superadmin', NULL);

-- Admin da PharmaTransport
INSERT INTO users (name, email, password_hash, role, company_id) VALUES
('Carlos Silva', 'admin@pharmatransport.com',
 '$2b$12$DYkfTREXJTBJHd3g57UG4OcKnsYehLUT7vVY60Wh4UeGNYJ5yJTpC',
 'admin', 1);

-- Operadores da PharmaTransport
INSERT INTO users (name, email, password_hash, role, company_id) VALUES
('Maria Oliveira', 'op1@pharmatransport.com',
 '$2b$12$MpGgyanpzh8ltYYJncGR2OlHgcznn62D7mVcY08uV4auSXNVb2BZu',
 'operator', 1),
('João Santos', 'op2@pharmatransport.com',
 '$2b$12$MpGgyanpzh8ltYYJncGR2OlHgcznn62D7mVcY08uV4auSXNVb2BZu',
 'operator', 1);

-- Admin da BioFrio
INSERT INTO users (name, email, password_hash, role, company_id) VALUES
('Ana Costa', 'admin@biofrio.com',
 '$2b$12$DYkfTREXJTBJHd3g57UG4OcKnsYehLUT7vVY60Wh4UeGNYJ5yJTpC',
 'admin', 2);

-- Operador da BioFrio
INSERT INTO users (name, email, password_hash, role, company_id) VALUES
('Pedro Lima', 'op1@biofrio.com',
 '$2b$12$MpGgyanpzh8ltYYJncGR2OlHgcznn62D7mVcY08uV4auSXNVb2BZu',
 'operator', 2);

-- ============================
-- 3. DISPOSITIVOS
-- ============================
INSERT INTO devices (company_id, serial_number, name, status, registration_status) VALUES
(1, 'IOT-GPS-001', 'Caminhão Refrigerado #1', 'active',   'active'),
(1, 'IOT-GPS-004', 'Carga Moderna SP',        'active',   'active'),
(2, 'IOT-GPS-002', 'Sensor BioFrio #1',       'active',   'active');

-- ============================
-- 4. VACINAS (por empresa)
-- ============================
-- PharmaTransport (company_id=1)
INSERT INTO vaccines (company_id, name, manufacturer, min_temp, max_temp) VALUES
(1, 'Spikevax',           'Moderna',          -25.00, -15.00),
(1, 'Comirnaty (COVID-19)','Pfizer/BioNTech', -80.00, -60.00),
(1, 'Vaxzevria',          'AstraZeneca',        2.00,   8.00);

-- BioFrio (company_id=2)
INSERT INTO vaccines (company_id, name, manufacturer, min_temp, max_temp) VALUES
(2, 'CoronaVac', 'Sinovac',              2.00, 8.00),
(2, 'Janssen',   'Johnson & Johnson',    2.00, 8.00);

-- ============================
-- 5. LOTES
-- ============================
INSERT INTO vaccine_batch (vaccine_id, batch_code, expiration_date, quantity_units) VALUES
(1, 'MOD-2026-X01', '2026-12-31', 4500),  -- Spikevax
(2, 'PFZ-2026-A01', '2026-10-15', 5000),  -- Comirnaty
(3, 'AZ-2026-B01',  '2026-08-20', 3000),  -- Vaxzevria
(4, 'SIN-2026-C01', '2026-07-30', 8000),  -- CoronaVac
(5, 'JNJ-2026-D01', '2026-09-10', 6000);  -- Janssen

-- ============================
-- 6. VIAGENS
-- ============================
-- Viagem PharmaTransport — Spikevax em andamento (device IOT-GPS-004)
INSERT INTO trips (batch_id, device_id, start_time, end_time, origin, destination, received_confirmation) VALUES
(1, 2, NOW() - INTERVAL 4 HOUR, NULL, 'Aeroporto Guarulhos', 'Interior SP - Campinas', FALSE);

-- Viagem PharmaTransport — Comirnaty encerrada
INSERT INTO trips (batch_id, device_id, start_time, end_time, origin, destination, received_confirmation) VALUES
(2, 1, '2026-04-10 08:00:00', '2026-04-10 14:00:00', 'CD São Paulo', 'Hospital das Clínicas', TRUE);

-- Viagem BioFrio — CoronaVac em andamento (device IOT-GPS-002)
INSERT INTO trips (batch_id, device_id, start_time, end_time, origin, destination, received_confirmation) VALUES
(4, 3, NOW() - INTERVAL 2 HOUR, NULL, 'Rio de Janeiro', 'Niterói', FALSE);
