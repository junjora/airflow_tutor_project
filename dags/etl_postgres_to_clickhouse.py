# dags/etl_postgres_to_clickhouse.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.clickhouse.operators.clickhouse import ClickHouseOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import pandas as pd
from clickhouse_driver import Client
import logging

logger = logging.getLogger(__name__)

# DAG parameters
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='etl_postgres_to_clickhouse',
    default_args=default_args,
    description='ETL pipeline from PostgreSQL to ClickHouse',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'postgresql', 'clickhouse'],
)

# Python functions for ETL logic

def extract_from_postgres(**context):
    """Extract data from PostgreSQL"""
    import psycopg2
    
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        database='source_database',
        user='postgres',
        password='postgres'
    )
    
    query = "SELECT * FROM source_table WHERE created_at > NOW() - INTERVAL '1 day'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Save to XCom for next task
    context['task_instance'].xcom_push(
        key='extracted_data',
        value=df.to_json()
    )
    
    logger.info(f"Extracted {len(df)} rows from PostgreSQL")
    return len(df)

def transform_data(**context):
    """Transform and validate data"""
    ti = context['task_instance']
    json_data = ti.xcom_pull(
        task_ids='extract_postgres',
        key='extracted_data'
    )
    
    df = pd.read_json(json_data)
    
    # Data cleaning and transformation
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.dropna(subset=['id'])  # Remove null IDs
    df['processed_at'] = datetime.now()
    
    ti.xcom_push(
        key='transformed_data',
        value=df.to_json()
    )
    
    logger.info(f"Transformed {len(df)} rows")
    return len(df)

def load_to_clickhouse(**context):
    """Load data to ClickHouse"""
    ti = context['task_instance']
    json_data = ti.xcom_pull(
        task_ids='transform_data',
        key='transformed_data'
    )
    
    df = pd.read_json(json_data)
    
    client = Client('clickhouse', port=9000)
    
    # Insert data to ClickHouse
    client.execute(
        'INSERT INTO etl_table VALUES',
        df.values.tolist()
    )
    
    logger.info(f"Loaded {len(df)} rows to ClickHouse")
    
    client.disconnect()
    return len(df)

# DAG Tasks

extract_task = PythonOperator(
    task_id='extract_postgres',
    python_callable=extract_from_postgres,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_clickhouse',
    python_callable=load_to_clickhouse,
    dag=dag,
)

# Set task dependencies
extract_task >> transform_task >> load_task
