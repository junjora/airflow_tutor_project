#!/bin/bash

# ============================================================
# Инициализация PostgreSQL
# ============================================================

echo "Инициализация PostgreSQL..."

# Создание дополнительной БД для исходных данных
PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -h localhost << EOF

-- Создание базы данных для исходных данных
CREATE DATABASE IF NOT EXISTS source_database;

-- Подключение к новой БД
\c source_database

-- Создание таблицы источника данных
CREATE TABLE IF NOT EXISTS source_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    amount NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_email ON source_table(email);
CREATE INDEX IF NOT EXISTS idx_created_at ON source_table(created_at);

-- Вставка тестовых данных
INSERT INTO source_table (name, email, amount) VALUES
    ('Alice Smith', 'alice@example.com', 1500.00),
    ('Bob Johnson', 'bob@example.com', 2500.50),
    ('Charlie Brown', 'charlie@example.com', 3000.00),
    ('Diana Prince', 'diana@example.com', 1800.25),
    ('Edward Norton', 'edward@example.com', 2200.00)
ON CONFLICT DO NOTHING;

-- Создание функции для обновления updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создание триггера
DROP TRIGGER IF EXISTS update_source_table_timestamp ON source_table;
CREATE TRIGGER update_source_table_timestamp
BEFORE UPDATE ON source_table
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

EOF

echo "✓ PostgreSQL инициализирована успешно"
