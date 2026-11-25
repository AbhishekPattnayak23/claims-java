-- Flyway migration script V1__initial_schema.sql
-- Created for ClaimsMicroservice database schema
-- PostgreSQL compatible

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for idempotent migration)
DROP TABLE IF EXISTS claims CASCADE;
DROP TABLE IF EXISTS benefits CASCADE;
DROP TABLE IF EXISTS provider_policy CASCADE;
DROP TABLE IF EXISTS policies CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
    user_id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT chk_role CHECK (role IN ('CLAIMS_PROCESSOR', 'ADMIN', 'USER'))
);

-- Create policies table
CREATE TABLE policies (
    policy_id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_number VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    policy_type VARCHAR(50) NOT NULL,
    coverage_details JSONB,
    effective_date DATE NOT NULL,
    expiration_date DATE,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_policy_status CHECK (status IN ('ACTIVE', 'INACTIVE', 'EXPIRED', 'PENDING', 'CANCELLED'))
);

-- Create benefits table
CREATE TABLE benefits (
    benefit_id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    benefit_code VARCHAR(50) UNIQUE NOT NULL,
    benefit_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    coverage_limit NUMERIC(15, 2),
    deductible NUMERIC(15, 2),
    co_payment_percentage DECIMAL(5, 2),
    co_payment_amount NUMERIC(15, 2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create provider_policy table
CREATE TABLE provider_policy (
    provider_id VARCHAR(36) NOT NULL,
    policy_id VARCHAR(36) NOT NULL,
    relationship_type VARCHAR(50),
    is_preferred BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (provider_id, policy_id),
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE
);

-- Create claims table
CREATE TABLE claims (
    claim_id BIGSERIAL PRIMARY KEY,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    policy_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36),
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    incident_date TIMESTAMP NOT NULL,
    total_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT,
    line_items JSONB,
    status VARCHAR(50) NOT NULL,
    status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 0,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_claim_status CHECK (status IN ('SUBMITTED', 'PROCESSING', 'APPROVED', 'REJECTED', 'PAID', 'PENDING_REVIEW', 'REQUIRES_INFO')),
    CONSTRAINT chk_total_amount CHECK (total_amount >= 0)
);

-- Create indexes for better query performance
CREATE INDEX idx_claims_user_id ON claims(user_id);
CREATE INDEX idx_claims_policy_id ON claims(policy_id);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_submission_date ON claims(submission_date);
CREATE INDEX idx_policies_user_id ON policies(user_id);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_provider_policy_policy_id ON provider_policy(policy_id);

-- Create audit_trail table for security and compliance
CREATE TABLE audit_trail (
    audit_id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    performed_by VARCHAR(36),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (performed_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Create trigger for update timestamps on policies
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_policies_updated_at
    BEFORE UPDATE ON policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for update timestamps on claims
CREATE TRIGGER update_claims_updated_at
    BEFORE UPDATE ON claims
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for update timestamps on benefits
CREATE TRIGGER update_benefits_updated_at
    BEFORE UPDATE ON benefits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default benefits data
INSERT INTO benefits (benefit_id, benefit_code, benefit_name, description, category, coverage_limit, deductible, co_payment_percentage, co_payment_amount) VALUES
    (uuid_generate_v4(), 'MED_SURG', 'Medical/Surgical', 'Covers medical and surgical procedures', 'MEDICAL', 500000.00, 1000.00, 20.00, NULL),
    (uuid_generate_v4(), 'RX', 'Prescription Drugs', 'Covers prescription medications', 'PHARMACY', 10000.00, 100.00, 10.00, 15.00),
    (uuid_generate_v4(), 'HOSPITAL', 'Hospital Stay', 'Covers inpatient hospital services', 'HOSPITAL', 250000.00, 500.00, 15.00, NULL),
    (uuid_generate_v4(), 'EMERGENCY', 'Emergency Services', 'Covers emergency room visits', 'EMERGENCY', 50000.00, 250.00, 10.00, 100.00),
    (uuid_generate_v4(), 'MENTAL_HEALTH', 'Mental Health', 'Covers mental health services', 'BEHAVIORAL', 50000.00, 500.00, 20.00, NULL);

-- Create audit trail trigger function
CREATE OR REPLACE FUNCTION audit_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_trail (action, entity_type, entity_id, old_values, new_values)
        VALUES (
            'UPDATE',
            TG_TABLE_NAME,
            COALESCE(NEW.claim_id::text, NEW.policy_id, NEW.user_id, NEW.benefit_id),
            row_to_json(OLD)::jsonb,
            row_to_json(NEW)::jsonb
        );
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_trail (action, entity_type, entity_id, old_values)
        VALUES (
            'DELETE',
            TG_TABLE_NAME,
            OLD.claim_id::text,
            row_to_json(OLD)::jsonb
        );
        RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_trail (action, entity_type, entity_id, new_values)
        VALUES (
            'INSERT',
            TG_TABLE_NAME,
            NEW.claim_id::text,
            row_to_json(NEW)::jsonb
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Add audit triggers for claims table
CREATE TRIGGER audit_claims_changes
    AFTER INSERT OR UPDATE OR DELETE ON claims
    FOR EACH ROW
    EXECUTE FUNCTION audit_change();

-- Add audit triggers for policies table
CREATE TRIGGER audit_policies_changes
    AFTER INSERT OR UPDATE OR DELETE ON policies
    FOR EACH ROW
    EXECUTE FUNCTION audit_change();

-- Add audit triggers for users table
CREATE TRIGGER audit_users_changes
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW
    EXECUTE FUNCTION audit_change();

-- Add comments for documentation
COMMENT ON TABLE users IS 'System users including claims processors, administrators, and policyholders';
COMMENT ON TABLE policies IS 'Insurance policies purchased by users';
COMMENT ON TABLE claims IS 'Claims submitted against insurance policies';
COMMENT ON TABLE benefits IS 'Available insurance benefits and coverage details';
COMMENT ON TABLE provider_policy IS 'Relationship between healthcare providers and policies';
COMMENT ON TABLE audit_trail IS 'Audit trail for compliance and security tracking';

-- Create validation functions
CREATE OR REPLACE FUNCTION validate_claim_dates()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.incident_date > CURRENT_DATE THEN
        RAISE EXCEPTION 'Incident date cannot be in the future';
    END IF;
    IF NEW.submission_date < NEW.incident_date THEN
        RAISE EXCEPTION 'Submission date must be after incident date';
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER validate_claim_dates_trigger
    BEFORE INSERT OR UPDATE ON claims
    FOR EACH ROW
    EXECUTE FUNCTION validate_claim_dates();

-- Create function to update status_updated_at when status changes
CREATE OR REPLACE FUNCTION update_status_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        NEW.status_updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_claim_status_timestamp
    BEFORE UPDATE ON claims
    FOR EACH ROW
    EXECUTE FUNCTION update_status_timestamp();