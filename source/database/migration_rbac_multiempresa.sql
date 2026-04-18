-- =============================================================
-- MIGRAÇÃO: RBAC Multi-Empresa
-- Executar sobre o banco vaccine_transport já existente
-- =============================================================

USE vaccine_transport;
SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================
-- 1. TABELA COMPANIES
-- =============================================================
CREATE TABLE IF NOT EXISTS companies (
    company_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    cnpj        VARCHAR(18)  NULL UNIQUE,
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- 2. ATUALIZAR TABELA USERS
--    - Adicionar company_id (NULL = superadmin, sem empresa)
--    - Expandir role para incluir 'superadmin'
-- =============================================================
ALTER TABLE users
    MODIFY COLUMN role ENUM('superadmin','admin','operator') NOT NULL DEFAULT 'operator',
    ADD COLUMN company_id INT NULL AFTER role,
    ADD CONSTRAINT fk_users_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL;

-- =============================================================
-- 3. ATUALIZAR TABELA VACCINES
--    - Adicionar company_id (cada produto pertence a uma empresa)
-- =============================================================
ALTER TABLE vaccines
    ADD COLUMN company_id INT NULL AFTER vaccine_id,
    ADD CONSTRAINT fk_vaccines_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL;

-- =============================================================
-- 4. ATUALIZAR TABELA DEVICES
--    - Adicionar company_id (dispositivo é atribuído a uma empresa
--      quando o admin o registra)
-- =============================================================
ALTER TABLE devices
    ADD COLUMN company_id INT NULL AFTER device_id,
    ADD CONSTRAINT fk_devices_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL;

SET FOREIGN_KEY_CHECKS = 1;


-- =============================================================
-- 5. SEED: EMPRESA DE DEMONSTRAÇÃO
-- =============================================================
INSERT INTO companies (company_id, name, cnpj) VALUES
(1, 'PharmaTransport Logística', '12.345.678/0001-99');


-- =============================================================
-- 6. SEED: SUPERADMIN (desenvolvedor do sistema)
--    Sem company_id — acesso global a tudo
--    Senha: admin123
-- =============================================================
INSERT INTO users (name, email, password_hash, role, company_id) VALUES
('Guilherme (Dev)', 'guilherme.palmanhani@gmail.com',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36DQBuMpV9h.L7MfxlJiUAy',
 'superadmin', NULL);


-- =============================================================
-- 7. ASSOCIAR USUÁRIOS EXISTENTES À EMPRESA 1
--    admin e operators existentes pertencem à PharmaTransport
-- =============================================================
UPDATE users
SET company_id = 1
WHERE email IN (
    'admin@logistica.com',
    'maria@transporte.com',
    'joao@transporte.com',
    'ana@monitoramento.com'
);


-- =============================================================
-- 8. ASSOCIAR VACINAS EXISTENTES À EMPRESA 1
-- =============================================================
UPDATE vaccines SET company_id = 1;


-- =============================================================
-- 9. ASSOCIAR DISPOSITIVOS EXISTENTES À EMPRESA 1
-- =============================================================
UPDATE devices SET company_id = 1;


-- =============================================================
-- RESULTADO DO RELACIONAMENTO
-- =============================================================
-- companies ──< users          (um admin/operador pertence a uma empresa)
-- companies ──< vaccines       (produto pertence a uma empresa)
-- companies ──< devices        (dispositivo pertence a uma empresa)
-- vaccines  ──< vaccine_batch  (lote herda empresa pela vacina)
-- vaccine_batch ──< trips      (viagem herda empresa pelo lote)
-- trips     ──< readings       (leitura herda empresa pela viagem)
--
-- REGRAS DE ACESSO:
--   superadmin → tudo, campo empresa editável
--   admin      → apenas sua company_id, campo empresa auto-populado
--   operator   → apenas sua company_id, somente leitura
-- =============================================================
