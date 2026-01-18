"""
ETL DAG: PostgreSQL to ClickHouse and Cassandra
Этот DAG извлекает данные из PostgreSQL и загружает их в ClickHouse и Cassandra
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import json

logger = logging.getLogger(__name__)

# ============================================================
# DEFAULT ARGUMENTS
# ============================================================

default_args = {
    'owner': 'grjm',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
    'start_date': days_ago(1),
}

# ============================================================
# DAG DEFINITION
# ============================================================

dag = DAG(
    dag_id='etl_postgres_to_multi_db',
    default_args=default_args,
    description='ETL: Extract from PostgreSQL, Load to ClickHouse and Cassandra',
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'postgresql', 'clickhouse', 'cassandra'],
    doc_md="""
    # ETL Pipeline: PostgreSQL → ClickHouse & Cassandra
    
    ## Описание
    Этот DAG выполняет следующие операции:
    1. Извлечение данных из PostgreSQL
    2. Трансформация и валидация данных
    3. Загрузка в ClickHouse
    4. Загрузка в Cassandra
    5. Проверка целостности данных
    
    ## График выполнения
    - Ежедневно в полночь (UTC)
    
    ## Контакты
    - Team: Data Engineering
    - Slack: #data-engineering
    """,
)

# ============================================================
# PYTHON FUNCTIONS
# ============================================================

def extract_from_postgres(**context):
    """
    Извлечение данных из PostgreSQL
    """
    try:
        # Подключение к PostgreSQL
        conn = psycopg2.connect(
            host='postgres',
            port=5432,
            database='source_database',
            user='postgres',
            password='postgres'
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # SQL запрос для извлечения данных за последний день
        query = """
            SELECT 
                id,
                name,
                email,
                amount,
                created_at,
                updated_at
            FROM source_table
            WHERE created_at > NOW() - INTERVAL '1 day'
            ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Преобразование в DataFrame
        df = pd.DataFrame(rows)
        
        # Сохранение в XCom для передачи следующей задаче
        json_data = df.to_json(orient='records', date_format='iso')
        context['task_instance'].xcom_push(
            key='extracted_data',
            value=json_data
        )
        
        cursor.close()
        conn.close()
        
        logger.info(f"✓ Успешно извлечено {len(df)} строк из PostgreSQL")
        return {
            'status': 'success',
            'rows_extracted': len(df),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"✗ Ошибка при извлечении данных: {str(e)}")
        raise


def transform_data(**context):
    """
    Трансформация и валидация данных
    """
    try:
        ti = context['task_instance']
        
        # Получение данных из XCom
        json_data = ti.xcom_pull(
            task_ids='extract_postgres',
            key='extracted_data'
        )
        
        if not json_data:
            logger.warning("Нет данных для трансформации")
            return {'status': 'no_data', 'rows_transformed': 0}
        
        # Преобразование JSON в DataFrame
        df = pd.read_json(json_data)
        
        # Данные трансформации
        # 1. Удаление строк с пустыми ID
        initial_count = len(df)
        df = df.dropna(subset=['id'])
        null_removed = initial_count - len(df)
        
        # 2. Преобразование типов данных
        df['id'] = df['id'].astype('int64')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        df['updated_at'] = pd.to_datetime(df['updated_at'], utc=True)
        
        # 3. Добавление новых колонок
        df['processed_at'] = datetime.utcnow()
        df['source_system'] = 'postgresql'
        df['etl_version'] = '1.0'
        
        # 4. Нормализация текстовых полей
        df['name'] = df['name'].str.strip().str.title()
        df['email'] = df['email'].str.strip().str.lower()
        
        # 5. Удаление дубликатов
        duplicates = len(df) - len(df.drop_duplicates(subset=['id']))
        df = df.drop_duplicates(subset=['id'], keep='last')
        
        # Сохранение трансформированных данных
        json_data_transformed = df.to_json(orient='records', date_format='iso')
        ti.xcom_push(
            key='transformed_data',
            value=json_data_transformed
        )
        
        logger.info(f"✓ Трансформация завершена:")
        logger.info(f"  - Удалено {null_removed} строк с пустыми ID")
        logger.info(f"  - Удалено {duplicates} дубликатов")
        logger.info(f"  - Итоговое количество строк: {len(df)}")
        
        return {
            'status': 'success',
            'rows_before': initial_count,
            'rows_after': len(df),
            'null_removed': null_removed,
            'duplicates_removed': duplicates
        }
        
    except Exception as e:
        logger.error(f"✗ Ошибка при трансформации: {str(e)}")
        raise


def load_to_clickhouse(**context):
    """
    Загрузка данных в ClickHouse
    """
    try:
        from clickhouse_driver import Client
        
        ti = context['task_instance']
        
        # Получение трансформированных данных
        json_data = ti.xcom_pull(
            task_ids='transform_data',
            key='transformed_data'
        )
        
        if not json_data:
            logger.warning("Нет данных для загрузки в ClickHouse")
            return {'status': 'no_data', 'rows_loaded': 0}
        
        df = pd.read_json(json_data)
        
        # Подключение к ClickHouse
        client = Client('clickhouse', port=9000)
        
        try:
            # Создание таблицы если ее нет
            create_table_query = """
            CREATE TABLE IF NOT EXISTS etl_db.etl_table
            (
                id Int64,
                name String,
                email String,
                amount Decimal128(2),
                created_at DateTime,
                updated_at DateTime,
                processed_at DateTime,
                source_system String,
                etl_version String
            )
            ENGINE = MergeTree()
            ORDER BY (created_at, id)
            PRIMARY KEY (created_at, id)
            PARTITION BY toYYYYMM(created_at)
            """
            
            client.execute(create_table_query)
            
            # Подготовка данных для вставки
            data_for_insert = []
            for _, row in df.iterrows():
                data_for_insert.append((
                    int(row['id']),
                    str(row['name']),
                    str(row['email']),
                    float(row['amount']) if pd.notna(row['amount']) else 0.0,
                    row['created_at'],
                    row['updated_at'],
                    row['processed_at'],
                    str(row['source_system']),
                    str(row['etl_version'])
                ))
            
            # Вставка данных
            if data_for_insert:
                client.execute(
                    'INSERT INTO etl_db.etl_table VALUES',
                    data_for_insert,
                    types_check=True
                )
            
            logger.info(f"✓ Успешно загружено {len(data_for_insert)} строк в ClickHouse")
            
            return {
                'status': 'success',
                'rows_loaded': len(data_for_insert),
                'table': 'etl_db.etl_table'
            }
            
        finally:
            client.disconnect()
            
    except Exception as e:
        logger.error(f"✗ Ошибка при загрузке в ClickHouse: {str(e)}")
        raise


def load_to_cassandra(**context):
    """
    Загрузка данных в Cassandra
    """
    try:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
        
        ti = context['task_instance']
        
        # Получение трансформированных данных
        json_data = ti.xcom_pull(
            task_ids='transform_data',
            key='transformed_data'
        )
        
        if not json_data:
            logger.warning("Нет данных для загрузки в Cassandra")
            return {'status': 'no_data', 'rows_loaded': 0}
        
        df = pd.read_json(json_data)
        
        # Подключение к Cassandra
        cluster = Cluster(['cassandra'], port=9042)
        session = cluster.connect()
        
        try:
            # Создание keyspace если его нет
            session.execute("""
                CREATE KEYSPACE IF NOT EXISTS etl_keyspace
                WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1}
            """)
            
            session.set_keyspace('etl_keyspace')
            
            # Создание таблицы если ее нет
            session.execute("""
                CREATE TABLE IF NOT EXISTS etl_table (
                    id UUID PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    amount DECIMAL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    processed_at TIMESTAMP,
                    source_system TEXT,
                    etl_version TEXT
                )
            """)
            
            # Подготовка и вставка данных
            insert_query = session.prepare("""
                INSERT INTO etl_table 
                (id, name, email, amount, created_at, updated_at, processed_at, source_system, etl_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            
            inserted_count = 0
            for _, row in df.iterrows():
                try:
                    session.execute(insert_query, (
                        str(row['id']),  # UUID
                        str(row['name']),
                        str(row['email']),
                        float(row['amount']) if pd.notna(row['amount']) else 0.0,
                        row['created_at'],
                        row['updated_at'],
                        row['processed_at'],
                        str(row['source_system']),
                        str(row['etl_version'])
                    ))
                    inserted_count += 1
                except Exception as row_error:
                    logger.error(f"Ошибка при вставке строки: {str(row_error)}")
                    continue
            
            logger.info(f"✓ Успешно загружено {inserted_count} строк в Cassandra")
            
            return {
                'status': 'success',
                'rows_loaded': inserted_count,
                'keyspace': 'etl_keyspace',
                'table': 'etl_table'
            }
            
        finally:
            session.shutdown()
            cluster.shutdown()
            
    except Exception as e:
        logger.error(f"✗ Ошибка при загрузке в Cassandra: {str(e)}")
        raise


def verify_data_integrity(**context):
    """
    Проверка целостности данных
    """
    try:
        from clickhouse_driver import Client as ClickHouseClient
        from cassandra.cluster import Cluster
        
        ch_client = ClickHouseClient('clickhouse', port=9000)
        cass_cluster = Cluster(['cassandra'], port=9042)
        cass_session = cass_cluster.connect('etl_keyspace')
        
        try:
            # Получение количества строк из ClickHouse
            ch_count = ch_client.execute('SELECT COUNT(*) FROM etl_db.etl_table')[0][0]
            
            # Получение количества строк из Cassandra
            cass_count = cass_session.execute('SELECT COUNT(*) FROM etl_table')[0][0]
            
            logger.info(f"✓ Проверка целостности:")
            logger.info(f"  - ClickHouse: {ch_count} строк")
            logger.info(f"  - Cassandra: {cass_count} строк")
            
            if ch_count == cass_count:
                logger.info(f"✓ Количество строк совпадает!")
            else:
                logger.warning(f"⚠ Количество строк не совпадает!")
            
            return {
                'status': 'success',
                'clickhouse_count': ch_count,
                'cassandra_count': cass_count,
                'match': ch_count == cass_count
            }
            
        finally:
            ch_client.disconnect()
            cass_session.shutdown()
            cass_cluster.shutdown()
            
    except Exception as e:
        logger.error(f"✗ Ошибка при проверке целостности: {str(e)}")
        raise


# ============================================================
# TASK DEFINITIONS
# ============================================================

extract_task = PythonOperator(
    task_id='extract_postgres',
    python_callable=extract_from_postgres,
    provide_context=True,
    doc_md="Извлечение данных из PostgreSQL",
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    provide_context=True,
    doc_md="Трансформация и валидация данных",
)

load_clickhouse_task = PythonOperator(
    task_id='load_clickhouse',
    python_callable=load_to_clickhouse,
    provide_context=True,
    doc_md="Загрузка данных в ClickHouse",
)

load_cassandra_task = PythonOperator(
    task_id='load_cassandra',
    python_callable=load_to_cassandra,
    provide_context=True,
    doc_md="Загрузка данных в Cassandra",
)

verify_task = PythonOperator(
    task_id='verify_data',
    python_callable=verify_data_integrity,
    provide_context=True,
    doc_md="Проверка целостности данных",
)

# ============================================================
# DAG DEPENDENCIES
# ============================================================

extract_task >> transform_task >> [load_clickhouse_task, load_cassandra_task] >> verify_task
