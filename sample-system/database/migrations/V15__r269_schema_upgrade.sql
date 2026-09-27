-- V15: R-26.9 schema upgrade
-- Adds 12-character customer_id and mandatory currency_code
-- Dependency: requires legacy-ledger 7.0

ALTER TABLE ledger_transactions RENAME TO ledger_transactions_v14;

CREATE TABLE ledger_transactions (
    id              BIGINT PRIMARY KEY,
    customer_id     VARCHAR(12) NOT NULL,  -- upgraded from VARCHAR(10)
    currency_code   CHAR(3) NOT NULL,       -- new field: ISO 4217 currency code
    amount          DECIMAL(15,2) NOT NULL,
    posted_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    schema_version  SMALLINT DEFAULT 15
);

-- Note: V14 table preserved for rollback reference
