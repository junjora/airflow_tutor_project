# Полное руководство по развертыванию Airflow DAG в Docker
## ETL-система для миграции данных: PostgreSQL → ClickHouse и Cassandra

**Версия:** 1.0  
**Дата:** Январь 2026  
**Язык:** Русский (Russian/Cyrillic)  
**Кодировка:** UTF-8

---

## ОГЛАВЛЕНИЕ

1. [Введение и архитектура](#введение-и-архитектура)
2. [Предварительные требования](#предварительные-требования)
3. [Компоненты системы](#компоненты-системы)
4. [Пошаговое развертывание](#пошаговое-развертывание)
5. [Конфигурация Airflow](#конфигурация-airflow)
6. [Создание DAG](#создание-dag)
7. [Интеграция ClickHouse](#интеграция-clickhouse)
8. [Интеграция Cassandra](#интеграция-cassandra)
9. [Обработка CSV и HDFS](#обработка-csv-и-hdfs)
10. [CI/CD процесс](#cicd-процесс)
11. [Мониторинг и логирование](#мониторинг-и-логирование)
12. [Решение проблем](#решение-проблем)

---

## Введение и архитектура

### Что такое Apache Airflow?

**Apache Airflow** — это платформа с открытым исходным кодом для программного создания, планирования и мониторинга рабочих процессов. Это инструмент оркестрации данных, используемый для:

- **Автоматизации ETL процессов** (Extract-Transform-Load)
- **Управления зависимостями между задачами**
- **Мониторинга выполнения рабочих процессов**
- **Обработки ошибок и повторных попыток**
- **Планирования регулярного выполнения задач**

### Архитектура решения

```
┌─────────────────────────────────────────────────────────────┐
│                    ИСТОЧНИКИ ДАННЫХ                         │
├─────────────────────────────────────────────────────────────┤
│ PostgreSQL │ CSV файлы │ HDFS │ Другие БД                  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              APACHE AIRFLOW (Оркестратор)                   │
├─────────────────────────────────────────────────────────────┤
│ - Scheduler (Планировщик)                                   │
│ - Web UI (Web интерфейс)                                    │
│ - Worker (Рабочий процесс)                                  │
│ - DAG (Направленный ациклический граф)                      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         ЦЕЛЕВЫЕ БАЗЫ ДАННЫХ (Хранилища)                    │
├─────────────────────────────────────────────────────────────┤
│   ClickHouse    │    Cassandra    │   PostgreSQL            │
└─────────────────────────────────────────────────────────────┘
```

### Основные компоненты

#### 1. **PostgreSQL** (источник данных)
- Реляционная база данных
- Хранит исходные данные для ETL
- Поддерживает сложные запросы и транзакции

#### 2. **ClickHouse** (целевое хранилище OLAP)
- Columnar хранилище для аналитики
- Оптимизирована для быстрых аналитических запросов
- Эффективна для больших объемов данных

#### 3. **Cassandra** (распределенное хранилище)
- NoSQL база данных
- Высокая масштабируемость и отказоустойчивость
- Для горизонтального масштабирования

#### 4. **Apache Airflow**
- Оркестрирует весь ETL процесс
- Управляет расписанием выполнения
- Обеспечивает мониторинг и логирование

#### 5. **Docker и Docker Compose**
- Контейнеризация всех сервисов
- Упрощение развертывания и масштабирования
- Изоляция окружения

---

## Предварительные требования

### Системные требования

```
Минимум:
- CPU: 4 ядра
- RAM: 8 GB
- Дисковое пространство: 50 GB

Рекомендуется:
- CPU: 8+ ядер
- RAM: 16+ GB
- Дисковое пространство: 100+ GB
```

### Установленное ПО

1. **Docker** (версия 20.10 и выше)
   ```bash
   docker --version
   ```

2. **Docker Compose** (версия 1.29 и выше)
   ```bash
   docker-compose --version
   ```

3. **Git** (для версионирования)
   ```bash
   git --version
   ```

4. **Python** (версия 3.8+, для локального тестирования)
   ```bash
   python3 --version
   ```

### Linux дополнительно

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## Компоненты системы

### 1. Apache Airflow компоненты

**Webserver** (Веб-сервер)
- Предоставляет UI на порту 8080
- Для управления и мониторинга DAG
- Аутентификация и управление пользователями

**Scheduler** (Планировщик)
- Отслеживает состояние DAG и задач
- Запускает задачи в установленное время
- Управляет переиспытаниями при ошибках

**Worker** (Рабочий процесс)
- Выполняет фактические задачи
- Может быть несколько workers для параллелизма
- Использует Celery для распределенной обработки

**Database (Metadata Database)**
- PostgreSQL или MySQL
- Хранит метаданные Airflow
- История выполнения DAG и задач

**Flower** (опционально)
- Веб-интерфейс для мониторинга Celery
- Отслеживание задач на workers
- Доступен на порту 5555

**Redis** (Message Broker)
- Промежуточный слой для очереди задач
- Связь между scheduler и workers
- Высокая производительность

### 2. Операторы Airflow для нашей системы

```python
# Операторы для работы с PostgreSQL
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.transfers.postgres_to_hive import PostgresToHiveOperator

# Операторы для работы с ClickHouse
from airflow.providers.clickhouse.operators.clickhouse import ClickHouseOperator

# Операторы Python
from airflow.operators.python_operator import PythonOperator

# Операторы для работы с файлами
from airflow.operators.bash_operator import BashOperator

# Операторы для работы с Cassandra
from airflow.providers.cassandra.operators.cassandra_query import CassandraOperator
```

### 3. Провайдеры (Providers)

Провайдеры расширяют функционал Airflow:

- **postgres-provider** - работа с PostgreSQL
- **clickhouse-provider** - работа с ClickHouse
- **cassandra-provider** - работа с Cassandra
- **apache-airflow[postgres]** - встроенная поддержка PostgreSQL
- **pyspark** - работа с Spark (опционально)

### 4. Инструменты и библиотеки

| Инструмент | Версия | Назначение |
|------------|--------|-----------|
| apache-airflow | 2.7+ | Платформа оркестрации |
| psycopg2-binary | latest | Драйвер PostgreSQL |
| clickhouse-driver | 0.4+ | Драйвер ClickHouse |
| cassandra-driver | 3.29+ | Драйвер Cassandra |
| pandas | 2.0+ | Обработка данных |
| sqlalchemy | 2.0+ | ORM для БД |
| python-dotenv | latest | Работа с переменными окружения |

---

## Пошаговое развертывание

### ШАГ 1: Создание структуры проекта

```bash
# Создание корневой директории проекта
mkdir -p airflow-etl-project
cd airflow-etl-project

# Создание основных папок
mkdir -p dags
mkdir -p plugins
mkdir -p logs
mkdir -p config
mkdir -p scripts
mkdir -p docker
mkdir -p tests
mkdir -p ci-cd

# Создание файлов конфигурации
touch docker-compose.yml
touch Dockerfile
touch requirements.txt
touch .env
touch .gitignore
```

Структура проекта:

```
airflow-etl-project/
├── dags/                          # DAG файлы
│   ├── etl_postgres_to_clickhouse.py
│   ├── etl_postgres_to_cassandra.py
│   ├── etl_csv_to_clickhouse.py
│   └── etl_hdfs_to_databases.py
├── plugins/                       # Пользовательские плагины
│   ├── operators/
│   └── hooks/
├── config/                        # Конфигурационные файлы
│   ├── airflow.cfg
│   └── log_config.py
├── scripts/                       # Вспомогательные скрипты
│   ├── init_databases.sh
│   ├── create_tables.sql
│   └── seed_data.py
├── docker/                        # Docker файлы
│   ├── Dockerfile
│   └── requirements.txt
├── logs/                          # Логи (создаются автоматически)
├── tests/                         # Тесты
│   └── test_dags.py
├── ci-cd/                         # CI/CD конфиги
│   ├── .gitlab-ci.yml
│   ├── .github/workflows/
│   └── Jenkinsfile
├── docker-compose.yml             # Docker Compose конфигурация
├── .env                           # Переменные окружения
├── .gitignore                     # Исключения для Git
├── requirements.txt               # Python зависимости
└── README.md                      # Документация
```

### ШАГ 2: Создание файла .env

Файл для хранения конфиденциальных данных:

```env
# === AIRFLOW CONFIGURATION ===
AIRFLOW_UID=50000
AIRFLOW_GID=0
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0
AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres:5432/airflow
AIRFLOW__CORE__FERNET_KEY=your-fernet-key-here
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true
AIRFLOW__CORE__LOAD_EXAMPLES=false

# === POSTGRESQL CONFIGURATION ===
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=source_database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# === CLICKHOUSE CONFIGURATION ===
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=9000
CLICKHOUSE_HTTP_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=default

# === CASSANDRA CONFIGURATION ===
CASSANDRA_HOST=cassandra
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=etl_keyspace
CASSANDRA_USER=cassandra
CASSANDRA_PASSWORD=cassandra

# === REDIS CONFIGURATION ===
REDIS_HOST=redis
REDIS_PORT=6379

# === ETL PARAMETERS ===
ETL_BATCH_SIZE=10000
ETL_RETRY_ATTEMPTS=3
ETL_RETRY_DELAY=300
```

### ШАГ 3: Создание requirements.txt

```txt
# === CORE AIRFLOW ===
apache-airflow==2.8.0
apache-airflow-providers-postgres==5.10.0
apache-airflow-providers-clickhouse==1.0.2
apache-airflow-providers-cassandra==3.6.0
apache-airflow-providers-celery==3.5.0
apache-airflow-providers-redis==3.5.0

# === DATABASE DRIVERS ===
psycopg2-binary==2.9.9
clickhouse-driver==0.4.6
cassandra-driver==3.29.1
sqlalchemy==2.0.23

# === DATA PROCESSING ===
pandas==2.1.3
numpy==1.26.3
pyarrow==14.0.1

# === UTILITIES ===
python-dotenv==1.0.0
requests==2.31.0
pyyaml==6.0.1
pytz==2023.3
python-dateutil==2.8.2

# === LOGGING & MONITORING ===
python-json-logger==2.0.7
prometheus-client==0.19.0

# === DEVELOPMENT ===
pytest==7.4.3
pytest-cov==4.1.0
black==23.12.0
flake8==6.1.0
```

### ШАГ 4: Создание Dockerfile

```dockerfile
# === BASE IMAGE ===
FROM apache/airflow:2.8.0-python3.11

# === INSTALL SYSTEM DEPENDENCIES ===
USER root

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# === SWITCH BACK TO AIRFLOW USER ===
USER airflow

# === COPY REQUIREMENTS ===
COPY requirements.txt /tmp/requirements.txt

# === INSTALL PYTHON DEPENDENCIES ===
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# === COPY PROJECT FILES ===
COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins
COPY config /opt/airflow/config

# === SET WORKING DIRECTORY ===
WORKDIR /opt/airflow

# === EXPOSE PORTS ===
# 8080 - Web UI
# 5555 - Flower (Celery monitoring)
EXPOSE 8080 5555

# === HEALTH CHECK ===
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

### ШАГ 5: Создание docker-compose.yml

```yaml
version: '3.9'

services:
  # === POSTGRESQL (Metadata Database & Source) ===
  postgres:
    image: postgres:16-alpine
    container_name: airflow-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_databases.sh:/docker-entrypoint-initdb.d/init.sh
    networks:
      - airflow_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # === REDIS (Message Broker) ===
  redis:
    image: redis:7-alpine
    container_name: airflow-redis
    command: redis-server --requirepass ""
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - airflow_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # === CLICKHOUSE (OLAP Database) ===
  clickhouse:
    image: clickhouse/clickhouse-server:24.1
    container_name: airflow-clickhouse
    environment:
      CLICKHOUSE_DB: ${CLICKHOUSE_DATABASE}
    ports:
      - "9000:9000"
      - "8123:8123"
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    networks:
      - airflow_network
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # === CASSANDRA (NoSQL Database) ===
  cassandra:
    image: cassandra:5.0
    container_name: airflow-cassandra
    environment:
      CASSANDRA_CLUSTER_NAME: "AirflowCluster"
      CASSANDRA_DC: "datacenter1"
    ports:
      - "9042:9042"
    volumes:
      - cassandra_data:/var/lib/cassandra
    networks:
      - airflow_network
    healthcheck:
      test: ["CMD-SHELL", "cqlsh -e 'SELECT release_version FROM system.local;'"]
      interval: 15s
      timeout: 10s
      retries: 5

  # === AIRFLOW INIT ===
  airflow-init:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: airflow-init
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: airflow
      _AIRFLOW_WWW_USER_PASSWORD: airflow
      AIRFLOW_UID: ${AIRFLOW_UID}
      AIRFLOW_GID: ${AIRFLOW_GID}
    networks:
      - airflow_network
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:${AIRFLOW_GID}" /sources/logs /sources/dags /sources/plugins
        airflow db upgrade
        airflow users create \
          --username airflow \
          --password airflow \
          --firstname Airflow \
          --lastname Admin \
          --role Admin \
          --email admin@example.com

  # === AIRFLOW WEBSERVER ===
  airflow-webserver:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: airflow-webserver
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      airflow-init:
        condition: service_completed_successfully
    environment:
      AIRFLOW_UID: ${AIRFLOW_UID}
      AIRFLOW_GID: ${AIRFLOW_GID}
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - ./logs:/opt/airflow/logs
      - ./config:/opt/airflow/config
    networks:
      - airflow_network
    command: airflow webserver
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === AIRFLOW SCHEDULER ===
  airflow-scheduler:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: airflow-scheduler
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      airflow-init:
        condition: service_completed_successfully
    environment:
      AIRFLOW_UID: ${AIRFLOW_UID}
      AIRFLOW_GID: ${AIRFLOW_GID}
    volumes:
      - ./dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - ./logs:/opt/airflow/logs
      - ./config:/opt/airflow/config
    networks:
      - airflow_network
    command: airflow scheduler
    healthcheck:
      test: ["CMD-SHELL", "airflow jobs check --job-type SchedulerJob --hostname $$(hostname)"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === CELERY WORKER ===
  airflow-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: airflow-worker
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      airflow-init:
        condition: service_completed_successfully
    environment:
      AIRFLOW_UID: ${AIRFLOW_UID}
      AIRFLOW_GID: ${AIRFLOW_GID}
    volumes:
      - ./dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - ./logs:/opt/airflow/logs
      - ./config:/opt/airflow/config
    networks:
      - airflow_network
    command: airflow celery worker
    healthcheck:
      test: ["CMD-SHELL", "celery -A airflow.executors.celery_executor inspect active_queues || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === FLOWER (Celery Monitoring) ===
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: airflow-flower
    depends_on:
      - redis
      - airflow-worker
    environment:
      AIRFLOW_UID: ${AIRFLOW_UID}
      AIRFLOW_GID: ${AIRFLOW_GID}
    ports:
      - "5555:5555"
    volumes:
      - ./logs:/opt/airflow/logs
    networks:
      - airflow_network
    command: airflow celery flower
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5555/health"]
      interval: 30s
      timeout: 10s
      retries: 3

# === VOLUMES ===
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  clickhouse_data:
    driver: local
  cassandra_data:
    driver: local

# === NETWORKS ===
networks:
  airflow_network:
    driver: bridge
```

### ШАГ 6: Запуск системы

```bash
# Создание .env файла (уже выполнено на ШАГ 2)
# Размещение в корне проекта

# Генерация Fernet key для шифрования
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Поместить результат в AIRFLOW__CORE__FERNET_KEY в .env

# Установка UID текущего пользователя (для Linux)
echo -e "AIRFLOW_UID=$(id -u)" >> .env

# Запуск Docker Compose
docker-compose up -d

# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f airflow-webserver

# Доступ к Web UI
# http://localhost:8080
# Username: airflow
# Password: airflow
```

---

## Конфигурация Airflow

### Основной конфигурационный файл (airflow.cfg)

```ini
[core]
# Тип исполнителя
executor = CeleryExecutor

# Подключение к metadata database
sql_alchemy_conn = postgresql+psycopg2://airflow:airflow@postgres:5432/airflow

# Директория с DAG файлами
dags_folder = /opt/airflow/dags

# Базовое логирование
base_log_folder = /opt/airflow/logs

# Максимальное количество active DAG runs
max_active_runs_per_dag = 16

# Минимальное время между запусками
min_serialized_dag_update_interval = 30

# Включить примеры DAG
load_examples = False

# Ключ шифрования
fernet_key = ${AIRFLOW__CORE__FERNET_KEY}

# DAG паузируются при создании
dags_are_paused_at_creation = True

[webserver]
# Порт веб-интерфейса
web_server_port = 8080

# Базовая аутентификация
authenticate = True
auth_backend = airflow.api.auth.backend.basic_auth

# Лимит логов в UI
log_fetch_timeout_sec = 5
log_auto_tailing_enabled = True

[scheduler]
# Интервал проверки DAG
dag_dir_list_interval = 300

# Интервал проверки новых DAG файлов
scheduler_loop_interval = 1

# Максимальное количество активных задач
max_active_tasks_per_dag = 16

[celery]
# Redis как broker
broker_url = redis://:@redis:6379/0

# PostgreSQL как backend для результатов
result_backend = db+postgresql://airflow:airflow@postgres:5432/airflow

# Таймауты
task_time_limit = 1200
task_soft_time_limit = 900

[logging]
# Удаленное логирование (опционально)
remote_logging = False

# Формат логов
log_format = [%%(asctime)s] {%%(filename)s:%%(lineno)d} %%(levelname)s - %%(message)s
```

### Переменные окружения Airflow

```python
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
```

---

## Создание DAG

### DAG 1: PostgreSQL → ClickHouse

```python
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
```

### DAG 2: CSV → ClickHouse

```python
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
```

---

## Интеграция ClickHouse

### Создание таблиц в ClickHouse

```sql
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
```

### Python код для работы с ClickHouse

```python
# plugins/clickhouse_utils.py

from clickhouse_driver import Client
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ClickHouseManager:
    def __init__(self, host: str = 'clickhouse', port: int = 9000):
        self.client = Client(host, port=port)
    
    def create_table(self, table_name: str, schema: Dict[str, str]):
        """Create table in ClickHouse"""
        columns = ', '.join([f'{col} {dtype}' for col, dtype in schema.items()])
        query = f'''
            CREATE TABLE IF NOT EXISTS {table_name}
            ({columns})
            ENGINE = MergeTree()
            ORDER BY (id)
        '''
        self.client.execute(query)
        logger.info(f"Table {table_name} created successfully")
    
    def insert_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Insert data into ClickHouse"""
        if not data:
            logger.warning("No data to insert")
            return
        
        columns = list(data[0].keys())
        values = [tuple(row.values()) for row in data]
        
        self.client.execute(
            f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES',
            values
        )
        logger.info(f"Inserted {len(data)} rows into {table_name}")
    
    def query(self, sql: str) -> List[Any]:
        """Execute SELECT query"""
        return self.client.execute(sql)
    
    def close(self):
        """Close connection"""
        self.client.disconnect()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

---

## Интеграция Cassandra

### Создание таблиц в Cassandra

```cassandra
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
```

### Python код для работы с Cassandra

```python
# plugins/cassandra_utils.py

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CassandraManager:
    def __init__(self, host: str = 'cassandra', port: int = 9042,
                 keyspace: str = 'etl_keyspace', user: str = None, 
                 password: str = None):
        auth_provider = None
        if user and password:
            auth_provider = PlainTextAuthProvider(username=user, password=password)
        
        self.cluster = Cluster([host], port=port, auth_provider=auth_provider)
        self.session = self.cluster.connect()
        self.keyspace = keyspace
        self.session.set_keyspace(keyspace)
    
    def insert_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Insert data into Cassandra"""
        if not data:
            logger.warning("No data to insert")
            return
        
        for row in data:
            columns = ', '.join(row.keys())
            placeholders = ', '.join(['%s'] * len(row))
            query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
            self.session.execute(query, tuple(row.values()))
        
        logger.info(f"Inserted {len(data)} rows into {table_name}")
    
    def query(self, sql: str) -> List[Any]:
        """Execute SELECT query"""
        return self.session.execute(sql).all()
    
    def close(self):
        """Close connection"""
        self.session.shutdown()
        self.cluster.shutdown()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

---

## Обработка CSV и HDFS

### DAG для HDFS

```python
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
```

---

## CI/CD процесс

### GitHub Actions Configuration

```yaml
# .github/workflows/deploy.yml

name: Airflow ETL Pipeline CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black
    
    - name: Lint with flake8
      run: |
        flake8 dags/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 dags/ --count --exit-zero --max-complexity=10 --max-line-length=127
    
    - name: Format check with black
      run: |
        black --check dags/
    
    - name: Run unit tests
      run: |
        pytest tests/ --cov=dags --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/airflow-etl:latest
          ${{ secrets.DOCKER_USERNAME }}/airflow-etl:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
        DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
      run: |
        mkdir -p ~/.ssh
        echo "$DEPLOY_KEY" > ~/.ssh/deploy_key
        chmod 600 ~/.ssh/deploy_key
        ssh-keyscan -H $DEPLOY_HOST >> ~/.ssh/known_hosts
        ssh -i ~/.ssh/deploy_key $DEPLOY_USER@$DEPLOY_HOST \
          "cd /opt/airflow && docker-compose pull && docker-compose up -d"
```

### GitLab CI Configuration

```yaml
# .gitlab-ci.yml

stages:
  - lint
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: registry.gitlab.com/$CI_PROJECT_NAMESPACE/$CI_PROJECT_NAME
  DOCKER_DRIVER: overlay2

before_script:
  - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

lint:
  stage: lint
  image: python:3.11
  script:
    - pip install flake8 black
    - flake8 dags/ --max-line-length=127
    - black --check dags/
  only:
    - merge_requests
    - main
    - develop

test:
  stage: test
  image: python:3.11
  services:
    - postgres:16-alpine
  variables:
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: test_db
  script:
    - pip install -r requirements.txt
    - pip install pytest pytest-cov
    - pytest tests/ --cov=dags --cov-report=term --cov-report=html
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  coverage: '/TOTAL.*\s+(\d+%)$/'

build:
  stage: build
  image: docker:20.10
  services:
    - docker:20.10-dind
  script:
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA
    - |
      if [ "$CI_COMMIT_BRANCH" = "main" ]; then
        docker tag $DOCKER_IMAGE:$CI_COMMIT_SHA $DOCKER_IMAGE:latest
        docker push $DOCKER_IMAGE:latest
      fi
  only:
    - main
    - develop

deploy_staging:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$DEPLOY_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - ssh-keyscan -H $STAGING_HOST >> ~/.ssh/known_hosts
    - ssh -i ~/.ssh/deploy_key $DEPLOY_USER@$STAGING_HOST \
        "cd /opt/airflow-staging && docker-compose pull && docker-compose up -d"
  environment:
    name: staging
  only:
    - develop

deploy_production:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$DEPLOY_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - ssh-keyscan -H $PROD_HOST >> ~/.ssh/known_hosts
    - ssh -i ~/.ssh/deploy_key $DEPLOY_USER@$PROD_HOST \
        "cd /opt/airflow && docker-compose pull && docker-compose up -d"
  environment:
    name: production
  only:
    - main
  when: manual
```

---

## Мониторинг и логирование

### Конфигурация логирования

```python
# config/logging_config.py

import logging
import logging.config
import os

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
        },
        'detailed': {
            'format': '[%(asctime)s] %(name)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': '/opt/airflow/logs/airflow.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'json_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': '/opt/airflow/logs/airflow_json.log',
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file', 'json_file'],
            'level': 'INFO',
            'propagate': True
        },
        'airflow': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'airflow.task': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### Мониторинг Prometheus

```python
# plugins/prometheus_exporter.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
dag_runs_total = Counter(
    'airflow_dag_runs_total',
    'Total number of DAG runs',
    ['dag_id', 'status']
)

task_duration_seconds = Histogram(
    'airflow_task_duration_seconds',
    'Task duration in seconds',
    ['dag_id', 'task_id', 'status']
)

dag_run_duration_seconds = Gauge(
    'airflow_dag_run_duration_seconds',
    'DAG run duration in seconds',
    ['dag_id']
)

active_tasks = Gauge(
    'airflow_active_tasks',
    'Number of active tasks',
    ['dag_id']
)

def record_dag_run(dag_id, status, duration):
    """Record DAG run metrics"""
    dag_runs_total.labels(dag_id=dag_id, status=status).inc()
    dag_run_duration_seconds.labels(dag_id=dag_id).set(duration)

def record_task_run(dag_id, task_id, status, duration):
    """Record task run metrics"""
    task_duration_seconds.labels(
        dag_id=dag_id,
        task_id=task_id,
        status=status
    ).observe(duration)
```

---

## Решение проблем

### Частые проблемы и их решение

#### 1. PostgreSQL недоступен

**Признак:** Ошибка подключения к PostgreSQL
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Решение:**
```bash
# Проверить статус контейнера
docker-compose ps postgres

# Просмотреть логи PostgreSQL
docker-compose logs postgres

# Перезапустить контейнер
docker-compose restart postgres

# Проверить подключение
docker-compose exec postgres psql -U postgres -d source_database -c "SELECT 1"
```

#### 2. ClickHouse недоступен

**Признак:** Таймаут подключения к ClickHouse
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Решение:**
```bash
# Проверить статус
docker-compose ps clickhouse

# Проверить конфигурацию ClickHouse
docker-compose exec clickhouse clickhouse-client --query "SELECT version()"

# Проверить логи
docker-compose logs clickhouse
```

#### 3. Cassandra не инициализируется

**Признак:** Cassandra зависает при запуске
```
Cassandra starting up... (hang)
```

**Решение:**
```bash
# Увеличить timeout в docker-compose.yml
healthcheck:
  test: ["CMD-SHELL", "cqlsh -e 'SELECT release_version FROM system.local;'"]
  interval: 30s  # Увеличить интервал
  timeout: 20s   # Увеличить таймаут
  retries: 10    # Увеличить переиспытания

# Очистить данные Cassandra и перезапустить
docker-compose down
docker volume rm airflow-etl-project_cassandra_data
docker-compose up -d
```

#### 4. DAG не появляется в Airflow

**Причина:** DAG файл не загружен или содержит ошибки

**Решение:**
```bash
# Проверить синтаксис DAG
python3 -m py_compile dags/your_dag.py

# Проверить загруженные DAG
docker-compose exec airflow-webserver airflow dags list

# Просмотреть логи парсера DAG
docker-compose logs airflow-scheduler | grep "DAG File Processing"

# Проверить права доступа
docker-compose exec airflow-webserver ls -la /opt/airflow/dags/
```

#### 5. Task выполняется слишком долго

**Проблема:** Timeout задачи
```
AirflowTaskTimeout: Task exceeded max_tries or execution_timeout
```

**Решение:**
```python
# Увеличить timeout в DAG
from datetime import timedelta

default_args = {
    'execution_timeout': timedelta(hours=4),  # Увеличить
}

# Увеличить timeout в конфиге Airflow
AIRFLOW__CELERY__TASK_TIME_LIMIT = 14400  # 4 часа
```

---

## Заключение

Эта система обеспечивает:

✓ **Надежность** - обработка ошибок и повторные попытки  
✓ **Масштабируемость** - горизонтальное масштабирование workers  
✓ **Мониторинг** - полное отслеживание и логирование  
✓ **Гибкость** - поддержка множества источников и целевых хранилищ  
✓ **Простота** - контейнеризация Docker для легкого развертывания  
✓ **Безопасность** - шифрование и управление доступом  

Для получения дополнительной помощи обратитесь к документации:
- Apache Airflow: https://airflow.apache.org/docs/
- ClickHouse: https://clickhouse.com/docs/
- Cassandra: https://cassandra.apache.org/doc/
- Docker: https://docs.docker.com/
