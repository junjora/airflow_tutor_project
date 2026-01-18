# dags/etl_csv_to_clickhouse.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-engineering',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='etl_csv_to_clickhouse',
    default_args=default_args,
    description='Load CSV files to ClickHouse',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'csv', 'clickhouse'],
)

def process_csv_file(**context):
    """Process and load CSV file"""
    from clickhouse_driver import Client
    
    csv_path = '/data/input/source_data.csv'
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Data validation and cleaning
    df = df.dropna(subset=['id'])
    df['loaded_at'] = pd.Timestamp.now()
    
    # Connect to ClickHouse and insert
    client = Client('clickhouse', port=9000)
    
    client.execute(
        'INSERT INTO csv_loaded_table VALUES',
        df.values.tolist()
    )
    
    client.disconnect()
    
    logger.info(f"Successfully loaded {len(df)} rows from CSV")
    return len(df)

# Tasks

process_csv = PythonOperator(
    task_id='process_csv',
    python_callable=process_csv_file,
    dag=dag,
)

verify_load = BashOperator(
    task_id='verify_load',
    bash_command='clickhouse-client --query "SELECT COUNT(*) FROM csv_loaded_table"',
    dag=dag,
)

process_csv >> verify_load
