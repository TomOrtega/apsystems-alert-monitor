CREATE TABLE IF NOT EXISTS config (
    id SERIAL PRIMARY KEY,
    section VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    value_type VARCHAR(20) DEFAULT 'text',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(section, key)
);

INSERT INTO config (section, key, value, value_type, description) VALUES
('accounts', 'account1_name', 'Residencial', 'text', 'Nombre de la cuenta 1'),
('accounts', 'account1_app_id', '', 'text', 'App ID de la cuenta 1'),
('accounts', 'account1_app_secret', '', 'password', 'App Secret de la cuenta 1'),
('accounts', 'account1_base_url', 'https://api.apsystemsema.com:9282', 'text', 'URL base API cuenta 1'),
('accounts', 'account1_systems', '', 'text', 'SIDs separados por coma cuenta 1'),
('accounts', 'account2_name', 'Comercial', 'text', 'Nombre de la cuenta 2'),
('accounts', 'account2_app_id', '', 'text', 'App ID de la cuenta 2'),
('accounts', 'account2_app_secret', '', 'password', 'App Secret de la cuenta 2'),
('accounts', 'account2_base_url', 'https://api.apsystemsema.com:9282', 'text', 'URL base API cuenta 2'),
('accounts', 'account2_systems', '', 'text', 'SIDs separados por coma cuenta 2')
ON CONFLICT (section, key) DO NOTHING;

INSERT INTO config (section, key, value, value_type, description) VALUES
('smtp', 'enabled', 'true', 'boolean', 'Habilitar envio de emails'),
('smtp', 'host', 'smtp.office365.com', 'text', 'Servidor SMTP'),
('smtp', 'port', '587', 'integer', 'Puerto SMTP'),
('smtp', 'user', '', 'text', 'Usuario SMTP'),
('smtp', 'password', '', 'password', 'Password SMTP'),
('smtp', 'from_addr', 'Monitor Solar <alertas@tudominio.com>', 'text', 'Direccion remitente'),
('smtp', 'alert_to', '', 'text', 'Destinatario de alertas')
ON CONFLICT (section, key) DO NOTHING;

INSERT INTO config (section, key, value, value_type, description) VALUES
('telegram', 'enabled', 'false', 'boolean', 'Habilitar notificaciones Telegram'),
('telegram', 'bot_token', '', 'password', 'Token del bot de Telegram'),
('telegram', 'chat_id', '', 'text', 'Chat ID de destino')
ON CONFLICT (section, key) DO NOTHING;

INSERT INTO config (section, key, value, value_type, description) VALUES
('scheduler', 'check_interval_hours', '24', 'integer', 'Intervalo de verificacion en horas'),
('scheduler', 'alert_retention_days', '90', 'integer', 'Dias de retencion de alertas')
ON CONFLICT (section, key) DO NOTHING;

INSERT INTO config (section, key, value, value_type, description) VALUES
('general', 'log_level', 'INFO', 'text', 'Nivel de logging'),
('general', 'timezone', 'UTC', 'text', 'Zona horaria del sistema')
ON CONFLICT (section, key) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_config_section ON config(section);
