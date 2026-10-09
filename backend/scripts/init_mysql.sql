-- =====================================================================
-- Production Automated Gold Trading System (XAUUSD)
-- MySQL 8.0+ Database Initialization & User Grants
-- =====================================================================

-- 1. Create dedicated database with UTF-8 support
CREATE DATABASE IF NOT EXISTS tradebot_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE tradebot_db;

-- 2. Create dedicated bot application user (Local & Host wildcards)
CREATE USER IF NOT EXISTS 'tradebot_user'@'localhost' IDENTIFIED BY 'StrongTradeBotPass2026!';
CREATE USER IF NOT EXISTS 'tradebot_user'@'127.0.0.1' IDENTIFIED BY 'StrongTradeBotPass2026!';
CREATE USER IF NOT EXISTS 'tradebot_user'@'%' IDENTIFIED BY 'StrongTradeBotPass2026!';

-- 3. Grant explicit DDL and DML permissions on tradebot_db
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES, LOCK TABLES 
  ON tradebot_db.* TO 'tradebot_user'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES, LOCK TABLES 
  ON tradebot_db.* TO 'tradebot_user'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES, LOCK TABLES 
  ON tradebot_db.* TO 'tradebot_user'@'%';

FLUSH PRIVILEGES;

-- =====================================================================
-- Table Structures (Ensures Tables Exist Before Seeding)
-- =====================================================================

CREATE TABLE IF NOT EXISTS trading_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_name VARCHAR(50) NOT NULL UNIQUE,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    start_time_utc TIME NOT NULL,
    end_time_utc TIME NOT NULL,
    max_allowed_spread_points DECIMAL(8, 2) NOT NULL DEFAULT 35.00,
    description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trading_sessions_name (session_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS strategy_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL UNIQUE,
    symbol VARCHAR(20) NOT NULL DEFAULT 'XAUUSD',
    timeframe VARCHAR(10) NOT NULL DEFAULT 'M15',
    is_enabled TINYINT(1) NOT NULL DEFAULT 1,
    risk_percent DECIMAL(5, 2) NOT NULL DEFAULT 1.00,
    max_positions INT NOT NULL DEFAULT 2,
    max_daily_loss_percent DECIMAL(5, 2) NOT NULL DEFAULT 3.00,
    max_spread_points DECIMAL(8, 2) NOT NULL DEFAULT 35.00,
    description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_strategy_configs_name (strategy_name),
    INDEX idx_strategy_configs_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS system_settings (
    key_name VARCHAR(100) NOT NULL PRIMARY KEY,
    config_value JSON NOT NULL,
    description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- Default Seed Data for Trading Sessions & Strategy Configurations
-- =====================================================================

-- Seed Sessions (UTC times: London 07:00-15:30, New York 13:00-21:00, Asian 00:00-08:00)
INSERT INTO trading_sessions (session_name, is_active, start_time_utc, end_time_utc, max_allowed_spread_points, description, created_at, updated_at)
VALUES 
  ('LONDON', 1, '07:00:00', '16:00:00', 30.00, 'London European Trading Session - Highest Gold Liquidity', UTC_TIMESTAMP(), UTC_TIMESTAMP()),
  ('NEW_YORK', 1, '13:00:00', '21:30:00', 35.00, 'New York US Trading Session - High Gold Volatility', UTC_TIMESTAMP(), UTC_TIMESTAMP()),
  ('ASIAN', 0, '00:00:00', '08:00:00', 45.00, 'Tokyo/Sydney Asian Session - Lower Gold Volume', UTC_TIMESTAMP(), UTC_TIMESTAMP())
ON DUPLICATE KEY UPDATE updated_at = UTC_TIMESTAMP();

-- Seed Primary Gold Strategy Configuration
INSERT INTO strategy_configs (strategy_name, symbol, timeframe, is_enabled, risk_percent, max_positions, max_daily_loss_percent, max_spread_points, description, created_at, updated_at)
VALUES 
  ('XAUUSD_M15_PULLBACK', 'XAUUSD', 'M15', 1, 1.00, 2, 3.00, 35.00, 'TradingView Pine Script Pullback strategy on 15-minute Gold chart', UTC_TIMESTAMP(), UTC_TIMESTAMP())
ON DUPLICATE KEY UPDATE updated_at = UTC_TIMESTAMP();

-- Seed Default System Dynamic Configuration
INSERT INTO system_settings (key_name, config_value, description, created_at, updated_at)
VALUES 
  ('bot_runtime_flags', JSON_OBJECT('auto_trading', true, 'max_slippage_points', 20.0, 'cooldown_after_consecutive_losses_sec', 1800), 'Core runtime overrides', UTC_TIMESTAMP(), UTC_TIMESTAMP())
ON DUPLICATE KEY UPDATE updated_at = UTC_TIMESTAMP();
