# dags/etl_hdfs_to_databases.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='etl_hdfs_to_databases',
    default_args=default_args,
    description='Load data from HDFS to ClickHouse and Cassandra',
    schedule_interval='@weekly',
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'hdfs'],
)

def read_from_hdfs(**context):
    """Read data from HDFS"""
    import pyspark.sql as spark_sql
    
    spark = spark_sql.SparkSession.builder \
        .appName("HDFS_ETL") \
        .getOrCreate()
    
    # Read Parquet from HDFS
    df = spark.read.parquet("hdfs://namenode:9000/data/input/data.parquet")
    
    # Convert to Pandas
    pandas_df = df.toPandas()
    
    context['task_instance'].xcom_push(
        key='hdfs_data',
        value=pandas_df.to_json()
    )
    
    logger.info(f"Read {len(pandas_df)} rows from HDFS")
    return len(pandas_df)

def load_to_both_databases(**context):
    """Load data to both ClickHouse and Cassandra"""
    from plugins.clickhouse_utils import ClickHouseManager
    from plugins.cassandra_utils import CassandraManager
    import json
    
    ti = context['task_instance']
    json_data = ti.xcom_pull(
        task_ids='read_hdfs',
        key='hdfs_data'
    )
    
    df = pd.read_json(json_data)
    data = df.to_dict('records')
    
    # Load to ClickHouse
    with ClickHouseManager() as ch:
        ch.insert_data('etl_db.hdfs_loaded_table', data)
    
    # Load to Cassandra
    with CassandraManager() as cass:
        cass.insert_data('hdfs_loaded_table', data)
    
    logger.info(f"Loaded {len(data)} rows to both databases")

read_hdfs = PythonOperator(
    task_id='read_hdfs',
    python_callable=read_from_hdfs,
    dag=dag,
)

load_both = PythonOperator(
    task_id='load_both_databases',
    python_callable=load_to_both_databases,
    dag=dag,
)

read_hdfs >> load_both
