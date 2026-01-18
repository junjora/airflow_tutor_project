-- scripts/cassandra_init.cql

-- Создание keyspace
CREATE KEYSPACE IF NOT EXISTS etl_keyspace
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Использование keyspace
USE etl_keyspace;

-- Создание таблицы для основных данных
CREATE TABLE IF NOT EXISTS etl_table (
    id UUID PRIMARY KEY,
    name TEXT,
    email TEXT,
    amount DECIMAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    processed_at TIMESTAMP,
    source_system TEXT
) WITH CLUSTERING ORDER BY (created_at DESC);

-- Создание индекса для быстрого поиска по email
CREATE INDEX IF NOT EXISTS idx_email ON etl_table (email);

-- Создание таблицы для CSV данных
CREATE TABLE IF NOT EXISTS csv_loaded_table (
    id UUID PRIMARY KEY,
    name TEXT,
    email TEXT,
    amount DECIMAL,
    loaded_at TIMESTAMP
);

-- Создание таблицы для синхронизации
CREATE TABLE IF NOT EXISTS sync_metadata (
    sync_id UUID PRIMARY KEY,
    table_name TEXT,
    last_sync_time TIMESTAMP,
    record_count BIGINT,
    status TEXT
);
