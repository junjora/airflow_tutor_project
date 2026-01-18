# config/airflow_config.py

import os
from datetime import timedelta

# Генеральные настройки
AIRFLOW_HOME = os.getenv('AIRFLOW_HOME', '/opt/airflow')
AIRFLOW_UID = os.getenv('AIRFLOW_UID', '50000')

# Database connections
POSTGRES_CONN = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'source_database'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
}

CLICKHOUSE_CONN = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 9000)),
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'default'),
}

CASSANDRA_CONN = {
    'host': os.getenv('CASSANDRA_HOST', 'localhost'),
    'port': int(os.getenv('CASSANDRA_PORT', 9042)),
    'keyspace': os.getenv('CASSANDRA_KEYSPACE', 'etl_keyspace'),
    'user': os.getenv('CASSANDRA_USER', 'cassandra'),
    'password': os.getenv('CASSANDRA_PASSWORD', 'cassandra'),
}

# ETL параметры
ETL_BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', 10000))
ETL_RETRY_ATTEMPTS = int(os.getenv('ETL_RETRY_ATTEMPTS', 3))
ETL_RETRY_DELAY = int(os.getenv('ETL_RETRY_DELAY', 300))

# Default DAG parameters
DEFAULT_DAG_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# Schedule intervals
SCHEDULE_INTERVALS = {
    'daily': '@daily',
    'hourly': '@hourly',
    'every_5_min': '*/5 * * * *',
}
