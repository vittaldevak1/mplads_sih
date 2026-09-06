-- MPLADS Intelligence Platform - PostgreSQL Schema
-- Created: 2026-09-04

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- WORKS TABLE (Central work registry)
-- =============================================
CREATE TABLE IF NOT EXISTS works (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150) UNIQUE NOT NULL,
    work_id_raw TEXT,
    work_title VARCHAR(500),
    work_category VARCHAR(100),
    work_description TEXT,
    state VARCHAR(100),
    ida VARCHAR(300),
    constituency VARCHAR(100),
    parliament_house VARCHAR(20) NOT NULL,
    source_file VARCHAR(200),
    has_image_proof BOOLEAN DEFAULT false,
    is_sc_quota BOOLEAN DEFAULT false,
    is_st_quota BOOLEAN DEFAULT false,
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    citizen_complaint_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- WORK RECOMMENDATIONS
-- =============================================
CREATE TABLE IF NOT EXISTS work_recommendations (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150) REFERENCES works(work_id),
    mp_name VARCHAR(300),
    recommended_date DATE,
    recommended_amount NUMERIC(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- WORK SANCTIONS
-- =============================================
CREATE TABLE IF NOT EXISTS work_sanctions (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150) REFERENCES works(work_id),
    sanction_date DATE,
    sanction_amount NUMERIC(15,2),
    work_status VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- WORK COMPLETIONS
-- =============================================
CREATE TABLE IF NOT EXISTS work_completions (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150) REFERENCES works(work_id),
    completion_date DATE,
    amount_disbursed NUMERIC(15,2),
    image_status VARCHAR(50),
    elected_nominated VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- EXPENDITURES
-- =============================================
CREATE TABLE IF NOT EXISTS expenditures (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150),
    expenditure_date DATE,
    vendor_name VARCHAR(300),
    payment_status VARCHAR(100),
    fund_disbursed_amount NUMERIC(15,2),
    mp_name VARCHAR(300),
    state VARCHAR(100),
    ida VARCHAR(300),
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- VENDORS
-- =============================================
CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    vendor_name VARCHAR(300) UNIQUE NOT NULL,
    total_works INTEGER DEFAULT 0,
    total_expenditure NUMERIC(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- MP ALLOCATIONS
-- =============================================
CREATE TABLE IF NOT EXISTS mp_allocations (
    id SERIAL PRIMARY KEY,
    mp_name VARCHAR(300),
    state VARCHAR(100),
    constituency VARCHAR(100),
    parliament_house VARCHAR(20) NOT NULL,
    allocated_amount NUMERIC(15,2),
    elected_nominated VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- CALAMITY CONSENTS
-- =============================================
CREATE TABLE IF NOT EXISTS calamity_consents (
    id SERIAL PRIMARY KEY,
    calamity_type VARCHAR(100),
    calamity_name VARCHAR(300),
    mp_name VARCHAR(300),
    consent_date DATE,
    consent_amount NUMERIC(15,2),
    parliament_house VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- RISK SCORES (AI output storage)
-- =============================================
CREATE TABLE IF NOT EXISTS risk_scores (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150) REFERENCES works(work_id) UNIQUE,
    composite_risk NUMERIC(5,2),
    confidence_coverage NUMERIC(5,4),
    inspection_priority VARCHAR(20),
    recommended_action TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- RISK SIGNALS (AI output storage - 11 per work)
-- =============================================
CREATE TABLE IF NOT EXISTS risk_signals (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150) REFERENCES works(work_id),
    signal_code VARCHAR(5) NOT NULL,
    signal_name VARCHAR(100) NOT NULL,
    version VARCHAR(50),
    score NUMERIC(5,2),
    weight NUMERIC(5,2) NOT NULL,
    available BOOLEAN DEFAULT false,
    evidence JSONB,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(work_id, signal_code)
);

-- =============================================
-- ANOMALIES
-- =============================================
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),
    description TEXT,
    evidence JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- CITIZEN REPORTS
-- =============================================
CREATE TABLE IF NOT EXISTS citizen_reports (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150),
    complaint_text TEXT,
    photo_url VARCHAR(500),
    reporter_name VARCHAR(200),
    reporter_contact VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- DOCUMENTS
-- =============================================
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150),
    document_type VARCHAR(100),
    file_name VARCHAR(300),
    file_path VARCHAR(500),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- INGESTION LOGS
-- =============================================
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(200),
    dataset_type VARCHAR(100),
    parliament_house VARCHAR(20),
    rows_read INTEGER,
    rows_inserted INTEGER,
    rows_skipped INTEGER,
    errors JSONB,
    warnings JSONB,
    ingested_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- INDEXES
-- =============================================
CREATE INDEX IF NOT EXISTS idx_works_work_id ON works(work_id);
CREATE INDEX IF NOT EXISTS idx_works_state ON works(state);
CREATE INDEX IF NOT EXISTS idx_works_constituency ON works(constituency);
CREATE INDEX IF NOT EXISTS idx_works_parliament_house ON works(parliament_house);
CREATE INDEX IF NOT EXISTS idx_works_work_category ON works(work_category);
CREATE INDEX IF NOT EXISTS idx_work_recommendations_work_id ON work_recommendations(work_id);
CREATE INDEX IF NOT EXISTS idx_work_sanctions_work_id ON work_sanctions(work_id);
CREATE INDEX IF NOT EXISTS idx_work_completions_work_id ON work_completions(work_id);
CREATE INDEX IF NOT EXISTS idx_expenditures_work_id ON expenditures(work_id);
CREATE INDEX IF NOT EXISTS idx_expenditures_vendor ON expenditures(vendor_name);
CREATE INDEX IF NOT EXISTS idx_risk_scores_composite_risk ON risk_scores(composite_risk);
CREATE INDEX IF NOT EXISTS idx_risk_scores_inspection_priority ON risk_scores(inspection_priority);
CREATE INDEX IF NOT EXISTS idx_risk_signals_work_id ON risk_signals(work_id);
CREATE INDEX IF NOT EXISTS idx_risk_signals_signal_code ON risk_signals(signal_code);
CREATE INDEX IF NOT EXISTS idx_anomalies_work_id ON anomalies(work_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_anomaly_type ON anomalies(anomaly_type);

-- =============================================
-- INSPECTION TASKS (Workflow tracking)
-- =============================================
CREATE TABLE IF NOT EXISTS inspection_tasks (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150) REFERENCES works(work_id),
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(200),
    assigned_at TIMESTAMP,
    notes TEXT,
    priority_override VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- ACTIVITY LOG (Audit trail)
-- =============================================
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    work_id VARCHAR(150),
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(200),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inspection_tasks_work_id ON inspection_tasks(work_id);
CREATE INDEX IF NOT EXISTS idx_inspection_tasks_status ON inspection_tasks(status);
CREATE INDEX IF NOT EXISTS idx_activity_log_work_id ON activity_log(work_id);
