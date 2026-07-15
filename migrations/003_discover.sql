CREATE TABLE IF NOT EXISTS sistemas_disponibles (
    id SERIAL PRIMARY KEY,
    account_index INT NOT NULL,
    sid TEXT NOT NULL,
    account_name TEXT DEFAULT '',
    ecu_list JSONB DEFAULT '[]',
    capacity FLOAT DEFAULT 0,
    system_type INT DEFAULT 1,
    timezone TEXT DEFAULT 'UTC',
    light INT DEFAULT 0,
    monitorear BOOLEAN DEFAULT false,
    discovered_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(account_index, sid)
);

CREATE INDEX IF NOT EXISTS idx_sistemas_disponibles_account ON sistemas_disponibles(account_index);
CREATE INDEX IF NOT EXISTS idx_sistemas_disponibles_monitorear ON sistemas_disponibles(monitorear);
