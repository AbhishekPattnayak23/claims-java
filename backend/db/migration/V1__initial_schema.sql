-- Flyway migration script for Claims Management System
-- Version: 1
-- Description: Initial database schema creation

-- User table
CREATE TABLE users (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT chk_role CHECK (role IN ('ADMIN', 'PROCESSOR', 'USER', 'AUDITOR'))
);

-- Policy table
CREATE TABLE policies (
    policy_id VARCHAR(36) PRIMARY KEY,
    policy_number VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    policy_type VARCHAR(50) NOT NULL,
    coverage_details JSONB,
    effective_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_policy_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_policy_status CHECK (status IN ('ACTIVE', 'EXPIRED', 'CANCELLED', 'PENDING'))
);

-- Provider table
CREATE TABLE providers (
    provider_id VARCHAR(36) PRIMARY KEY,
    provider_name VARCHAR(100) NOT NULL,
    npi_number VARCHAR(10) UNIQUE,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Benefits table
CREATE TABLE benefits (
    benefit_id VARCHAR(36) PRIMARY KEY,
    benefit_code VARCHAR(20) UNIQUE NOT NULL,
    benefit_name VARCHAR(100) NOT NULL,
    description TEXT,
    coverage_limit DECIMAL(15,2),
    deductible DECIMAL(15,2),
    co_pay DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ProviderPolicy join table (many-to-many)
CREATE TABLE provider_policy (
    provider_policy_id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36) NOT NULL,
    policy_id VARCHAR(36) NOT NULL,
    is_in_network BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_provider_policy_provider FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE,
    CONSTRAINT fk_provider_policy_policy FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE,
    CONSTRAINT uq_provider_policy UNIQUE (provider_id, policy_id)
);

-- Claim table
CREATE TABLE claims (
    claim_id BIGSERIAL PRIMARY KEY,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    policy_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36),
    submission_date TIMESTAMP NOT NULL,
    incident_date TIMESTAMP,
    total_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT,
    line_items JSONB,
    status VARCHAR(20) DEFAULT 'SUBMITTED',
    status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 0,
    CONSTRAINT fk_claim_policy FOREIGN KEY (policy_id) REFERENCES policies(policy_id),
    CONSTRAINT fk_claim_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_claim_provider FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    CONSTRAINT chk_claim_status CHECK (status IN ('SUBMITTED', 'PROCESSING', 'APPROVED', 'DENIED', 'PAID', 'CLOSED'))
);

-- Document table
CREATE TABLE documents (
    document_id VARCHAR(36) PRIMARY KEY,
    claim_id BIGINT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    uploaded_by VARCHAR(36),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT false,
    CONSTRAINT fk_document_claim FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    CONSTRAINT fk_document_uploader FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
);

-- AuditLog table
CREATE TABLE audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36),
    details JSONB,
    performed_by VARCHAR(36),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    CONSTRAINT fk_audit_performer FOREIGN KEY (performed_by) REFERENCES users(user_id)
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_policies_user_id ON policies(user_id);
CREATE INDEX idx_policies_policy_number ON policies(policy_number);
CREATE INDEX idx_providers_npi ON providers(npi_number);
CREATE INDEX idx_benefits_benefit_code ON benefits(benefit_code);
CREATE INDEX idx_provider_policy_provider ON provider_policy(provider_id);
CREATE INDEX idx_provider_policy_policy ON provider_policy(policy_id);
CREATE INDEX idx_claims_policy_id ON claims(policy_id);
CREATE INDEX idx_claims_user_id ON claims(user_id);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_claim_number ON claims(claim_number);
CREATE INDEX idx_documents_claim_id ON documents(claim_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_performed_at ON audit_logs(performed_at);

-- Add comments to tables
COMMENT ON TABLE users IS 'System users including administrators, claims processors, and policy holders';
COMMENT ON TABLE policies IS 'Insurance policies information';
COMMENT ON TABLE providers IS 'Healthcare providers (hospitals, doctors, clinics)';
COMMENT ON TABLE benefits IS 'Insurance benefit types and coverage details';
COMMENT ON TABLE provider_policy IS 'Join table linking providers with policies (network relationships)';
COMMENT ON TABLE claims IS 'Insurance claims submitted by users';
COMMENT ON TABLE documents IS 'Supporting documents uploaded for claims';
COMMENT ON TABLE audit_logs IS 'Audit trail for security and compliance';

-- Insert default admin user (password: admin123)
INSERT INTO users (user_id, username, email, role, is_active) 
VALUES ('admin-001', 'admin', 'admin@claims-system.com', 'ADMIN', true);

-- Insert default benefit types
INSERT INTO benefits (benefit_id, benefit_code, benefit_name, description, coverage_limit, deductible, co_pay) 
VALUES 
('benefit-001', 'MED', 'Medical Services', 'Coverage for medical services and procedures', 1000000.00, 500.00, 20.00),
('benefit-002', 'PHARM', 'Pharmacy', 'Prescription drug coverage', 20000.00, 100.00, 10.00),
('benefit-003', 'LAB', 'Laboratory', 'Lab tests and diagnostics', 5000.00, 50.00, 15.00),
('benefit-004', 'ER', 'Emergency Room', 'Emergency room visits', 2500.00, 250.00, 100.00),
('benefit-005', 'HOSP', 'Hospitalization', 'Inpatient hospital stays', 50000.00, 1000.00, 500.00);