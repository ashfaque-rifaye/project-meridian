-- Ledger DB Migration History
-- Flyway-style migrations for ledger-db

-- V14: Original schema (pre R-26.9)
-- customer_id VARCHAR(10) — supports up to 10 characters
CREATE TABLE ledger_transactions_v14 (
    id              BIGINT PRIMARY KEY,
    customer_id     VARCHAR(10) NOT NULL,
    amount          DECIMAL(15,2) NOT NULL,
    posted_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- V15: R-26.9 schema upgrade
-- customer_id VARCHAR(12) — supports up to 12 characters (R-26.9)
-- currency_code CHAR(3) — new mandatory field (R-26.9)
CREATE TABLE ledger_transactions (
    id              BIGINT PRIMARY KEY,
    customer_id     VARCHAR(12) NOT NULL,
    currency_code   CHAR(3) NOT NULL,
    amount          DECIMAL(15,2) NOT NULL,
    posted_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
