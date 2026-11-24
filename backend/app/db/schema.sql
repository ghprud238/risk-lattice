-- ContagionGraph DuckDB Schema Definition
-- PRD Section 5.1

CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id VARCHAR PRIMARY KEY,
    node_type VARCHAR NOT NULL, -- 'ASSET', 'SUPPLIER', 'MACRO'
    name VARCHAR NOT NULL,
    sector VARCHAR NOT NULL,
    net_debt_ebitda DOUBLE DEFAULT 1.0,
    int_coverage DOUBLE DEFAULT 4.0,
    substitutability DOUBLE DEFAULT 0.3,
    CHECK (substitutability >= 0.0 AND substitutability <= 0.8)
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type);

CREATE TABLE IF NOT EXISTS graph_edges (
    source_id VARCHAR NOT NULL,
    target_id VARCHAR NOT NULL,
    relation_type VARCHAR NOT NULL,
    base_weight DOUBLE NOT NULL,
    lag_days INTEGER DEFAULT 0,
    evidence_quote TEXT,
    is_llm_extracted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (source_id, target_id, relation_type),
    CHECK (ABS(base_weight) <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_src ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_tgt ON graph_edges(target_id);

CREATE TABLE IF NOT EXISTS macro_returns (
    trade_date DATE NOT NULL,
    node_id VARCHAR NOT NULL,
    daily_return DOUBLE NOT NULL,
    regime_tag VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_macro_returns_node_date ON macro_returns(node_id, trade_date);

CREATE TABLE IF NOT EXISTS stress_runs (
    run_id VARCHAR PRIMARY KEY,
    scenario_name VARCHAR NOT NULL,
    hop1_pnl DOUBLE NOT NULL,
    hop2_pnl DOUBLE NOT NULL,
    hop3_4_pnl DOUBLE NOT NULL,
    total_pnl DOUBLE NOT NULL,
    cvar_99 DOUBLE NOT NULL,
    critical_path_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authentication & Authorization Tables
-- Supports Proprietary Username/Password + Google Workspace SSO
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR, -- Salted bcrypt / PBKDF2 hash, NULL for OAuth-only users
    name VARCHAR NOT NULL,
    picture TEXT,
    role VARCHAR NOT NULL DEFAULT 'ANALYST', -- 'CHIEF_RISK_OFFICER', 'PORTFOLIO_MANAGER', 'ANALYST', 'AUDITOR'
    organization VARCHAR NOT NULL DEFAULT 'Institutional Client',
    auth_provider VARCHAR NOT NULL DEFAULT 'proprietary', -- 'proprietary', 'google'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_token VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    expires_at BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);

CREATE TABLE IF NOT EXISTS user_audit_logs (
    log_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    action VARCHAR NOT NULL, -- 'REGISTER', 'LOGIN', 'LOGOUT', 'PASSWORD_RESET', 'SIGN_OFF', 'SIMULATE'
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON user_audit_logs(user_id);
