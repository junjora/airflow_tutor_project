-- scripts/clickhouse_init.sql

-- Создание базы данных
CREATE DATABASE IF NOT EXISTS etl_db;

-- Создание основной таблицы для хранения данных
CREATE TABLE IF NOT EXISTS etl_db.etl_table
(
    id UUID,
    name String,
    email String,
    amount Decimal128(2),
    created_at DateTime,
    updated_at DateTime,
    processed_at DateTime,
    source_system String
)
ENGINE = MergeTree()
ORDER BY (created_at, id)
PRIMARY KEY (created_at, id)
PARTITION BY toYYYYMM(created_at);

-- Создание таблицы для загруженных CSV
CREATE TABLE IF NOT EXISTS etl_db.csv_loaded_table
(
    id UUID,
    name String,
    email String,
    amount Decimal128(2),
    loaded_at DateTime
)
ENGINE = MergeTree()
ORDER BY (loaded_at, id)
PARTITION BY toYYYYMM(loaded_at);

-- Создание реплицированной таблицы для Cassandra
CREATE TABLE IF NOT EXISTS etl_db.cassandra_replica
(
    id UUID,
    name String,
    email String,
    amount Decimal128(2),
    synced_at DateTime
)
ENGINE = MergeTree()
ORDER BY (synced_at, id)
PARTITION BY toYYYYMM(synced_at);
