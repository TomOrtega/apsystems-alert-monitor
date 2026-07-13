-- APsystems Alert Monitor - Esquema inicial PostgreSQL

CREATE TABLE IF NOT EXISTS sistemas (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    sid VARCHAR(100) NOT NULL UNIQUE,
    ecu_list JSONB DEFAULT '[]',
    light_actual INTEGER DEFAULT NULL,
    light_anterior INTEGER DEFAULT NULL,
    capacity VARCHAR(50),
    type INTEGER DEFAULT 1,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    sid VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    severidad VARCHAR(20) NOT NULL,
    mensaje TEXT,
    light_anterior INTEGER,
    light_nuevo INTEGER,
    email_enviado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_calls (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    sid VARCHAR(100),
    endpoint VARCHAR(200) NOT NULL,
    response_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_summary (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    total_sistemas INTEGER DEFAULT 0,
    green_count INTEGER DEFAULT 0,
    yellow_count INTEGER DEFAULT 0,
    red_count INTEGER DEFAULT 0,
    grey_count INTEGER DEFAULT 0,
    unknown_count INTEGER DEFAULT 0,
    api_calls_used INTEGER DEFAULT 0,
    alertas_generadas INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, account_name)
);

-- Indices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_sistemas_light ON sistemas(light_actual);
CREATE INDEX IF NOT EXISTS idx_sistemas_account ON sistemas(account_name);
CREATE INDEX IF NOT EXISTS idx_alertas_sid ON alertas(sid);
CREATE INDEX IF NOT EXISTS idx_alertas_created ON alertas(created_at);
CREATE INDEX IF NOT EXISTS idx_alertas_account ON alertas(account_name);
CREATE INDEX IF NOT EXISTS idx_api_calls_created ON api_calls(created_at);
CREATE INDEX IF NOT EXISTS idx_api_calls_account ON api_calls(account_name);
CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_summary(date);
