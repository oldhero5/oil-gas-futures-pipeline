"""DuckDB table schemas for futures and options data."""

import duckdb


def create_all_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all database tables."""
    create_commodities_table(conn)
    create_futures_contracts_table(conn)
    create_futures_prices_table(conn)
    create_options_contracts_table(conn)
    create_options_prices_table(conn)
    create_implied_volatility_table(conn)
    create_greeks_table(conn)
    create_market_data_log_table(conn)
    # User management tables
    create_users_table(conn)
    create_user_sessions_table(conn)
    create_user_audit_log_table(conn)


def create_commodities_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create commodities reference table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS commodities (
            commodity_id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            symbol VARCHAR NOT NULL,
            exchange VARCHAR NOT NULL,
            tick_size DECIMAL(10, 6),
            contract_size DECIMAL(10, 2),
            units VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert WTI Crude and Natural Gas
    conn.execute("""
        INSERT INTO commodities VALUES
        ('WTI', 'West Texas Intermediate Crude Oil', 'CL', 'NYMEX', 0.01, 1000, 'barrels', CURRENT_TIMESTAMP),
        ('NG', 'Natural Gas', 'NG', 'NYMEX', 0.001, 10000, 'mmBtu', CURRENT_TIMESTAMP)
        ON CONFLICT (commodity_id) DO NOTHING
    """)


def create_futures_contracts_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create futures contracts table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS futures_contracts (
            contract_id VARCHAR PRIMARY KEY,
            commodity_id VARCHAR NOT NULL,
            symbol VARCHAR NOT NULL,
            expiration_date DATE NOT NULL,
            first_trade_date DATE,
            last_trade_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (commodity_id) REFERENCES commodities(commodity_id)
        )
    """)

    # Create index on expiration date
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_futures_expiration
        ON futures_contracts(expiration_date)
    """)


def create_futures_prices_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create futures prices table."""
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_futures_prices_id START 1;
        CREATE TABLE IF NOT EXISTS futures_prices (
            price_id INTEGER PRIMARY KEY DEFAULT nextval('seq_futures_prices_id'),
            contract_id VARCHAR NOT NULL,
            price_date DATE NOT NULL,
            price_time TIMESTAMP,
            open_price DECIMAL(10, 4),
            high_price DECIMAL(10, 4),
            low_price DECIMAL(10, 4),
            close_price DECIMAL(10, 4) NOT NULL,
            settlement_price DECIMAL(10, 4),
            volume BIGINT,
            open_interest BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES futures_contracts(contract_id),
            UNIQUE(contract_id, price_date)
        )
    """)

    # Create indexes for efficient querying
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_futures_prices_date
        ON futures_prices(price_date)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_futures_prices_contract
        ON futures_prices(contract_id, price_date)
    """)


def create_options_contracts_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create options contracts table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS options_contracts (
            option_id VARCHAR PRIMARY KEY,
            underlying_contract_id VARCHAR NOT NULL,
            option_type VARCHAR CHECK (option_type IN ('CALL', 'PUT')),
            strike_price DECIMAL(10, 4) NOT NULL,
            expiration_date DATE NOT NULL,
            exercise_style VARCHAR DEFAULT 'AMERICAN',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (underlying_contract_id) REFERENCES futures_contracts(contract_id)
        )
    """)


def create_options_prices_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create options prices table."""
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_options_prices_id START 1;
        CREATE TABLE IF NOT EXISTS options_prices (
            price_id INTEGER PRIMARY KEY DEFAULT nextval('seq_options_prices_id'),
            option_id VARCHAR NOT NULL,
            price_date DATE NOT NULL,
            price_time TIMESTAMP,
            bid_price DECIMAL(10, 4),
            ask_price DECIMAL(10, 4),
            last_price DECIMAL(10, 4),
            settlement_price DECIMAL(10, 4),
            volume BIGINT,
            open_interest BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (option_id) REFERENCES options_contracts(option_id),
            UNIQUE(option_id, price_date)
        )
    """)


def create_implied_volatility_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create implied volatility table."""
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_implied_volatility_id START 1;
        CREATE TABLE IF NOT EXISTS implied_volatility (
            iv_id INTEGER PRIMARY KEY DEFAULT nextval('seq_implied_volatility_id'),
            option_id VARCHAR NOT NULL,
            price_date DATE NOT NULL,
            implied_vol DECIMAL(10, 6) NOT NULL,
            underlying_price DECIMAL(10, 4) NOT NULL,
            risk_free_rate DECIMAL(10, 6),
            calculation_method VARCHAR DEFAULT 'BLACK_SCHOLES',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (option_id) REFERENCES options_contracts(option_id),
            UNIQUE(option_id, price_date)
        )
    """)

    # Create index for volatility surface queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_iv_date
        ON implied_volatility(price_date)
    """)


def create_greeks_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create Greeks calculations table."""
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_greeks_id START 1;
        CREATE TABLE IF NOT EXISTS greeks (
            greek_id INTEGER PRIMARY KEY DEFAULT nextval('seq_greeks_id'),
            option_id VARCHAR NOT NULL,
            price_date DATE NOT NULL,
            delta DECIMAL(10, 6),
            gamma DECIMAL(10, 6),
            theta DECIMAL(10, 6),
            vega DECIMAL(10, 6),
            rho DECIMAL(10, 6),
            underlying_price DECIMAL(10, 4) NOT NULL,
            implied_vol DECIMAL(10, 6) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (option_id) REFERENCES options_contracts(option_id),
            UNIQUE(option_id, price_date)
        )
    """)


def create_market_data_log_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create market data ingestion log table."""
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_market_data_log_id START 1;
        CREATE TABLE IF NOT EXISTS market_data_log (
            log_id INTEGER PRIMARY KEY DEFAULT nextval('seq_market_data_log_id'),
            data_source VARCHAR NOT NULL,
            commodity_id VARCHAR,
            start_date DATE,
            end_date DATE,
            records_processed INTEGER,
            status VARCHAR,
            error_message VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def create_users_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create users table for authentication."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            role VARCHAR(50) NOT NULL DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Create indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users(email)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_role
        ON users(role)
    """)


def create_user_sessions_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create user sessions table for JWT token management."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Create indexes for performance
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id
        ON user_sessions(user_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_expires
        ON user_sessions(expires_at)
    """)


def create_user_audit_log_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create audit log table for user actions."""
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_user_audit_log_id START 1;
        CREATE TABLE IF NOT EXISTS user_audit_log (
            log_id INTEGER PRIMARY KEY DEFAULT nextval('seq_user_audit_log_id'),
            user_id UUID,
            action VARCHAR(100) NOT NULL,
            resource VARCHAR(255),
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Create index for querying user actions
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_user_id
        ON user_audit_log(user_id, created_at)
    """)
