# КРАТКИЙ ГАЙД: БЫСТРЫЙ СТАРТ

## 5 МИНУТ НА ЗАПУСК

### Шаг 1: Подготовка (2 минуты)

```bash
# Установка Docker и Docker Compose (если еще не установлены)
# Linux:
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка версий
docker --version
docker-compose --version
```

### Шаг 2: Клонирование и конфигурация (2 минуты)

```bash
# Клонирование репозитория
git clone https://github.com/your-org/airflow-etl-project.git
cd airflow-etl-project

# Создание .env файла
cp .env.example .env

# Генерация Fernet ключа
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s/7T0tK_HZ5j1H5l7j9m2v5p8s3w1q4t6u9/$FERNET_KEY/" .env

# Установка UID (для Linux)
echo "AIRFLOW_UID=$(id -u)" >> .env
```

### Шаг 3: Запуск (1 минута)

```bash
# Запуск всех контейнеров
docker-compose up -d

# Проверка статуса
docker-compose ps

# Ожидание инициализации (1-2 минуты)
docker-compose logs -f airflow-webserver | grep "Airflow is ready"
```

### Готово! ✓

**Доступ к интерфейсам:**

```
Airflow Web UI:     http://localhost:8080
Username:           airflow
Password:           airflow

Flower (Celery):    http://localhost:5555
PostgreSQL:         localhost:5432
ClickHouse:         localhost:9000 (native)
                    localhost:8123 (HTTP)
Cassandra:          localhost:9042
Redis:              localhost:6379
```

---

## ОСНОВНЫЕ ОПЕРАЦИИ

### Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Логи Airflow Webserver
docker-compose logs -f airflow-webserver

# Логи Scheduler
docker-compose logs -f airflow-scheduler

# Логи Worker
docker-compose logs -f airflow-worker

# Последние 100 строк
docker-compose logs --tail=100
```

### Управление DAG

```bash
# Список DAG
docker-compose exec airflow-webserver airflow dags list

# Информация о DAG
docker-compose exec airflow-webserver airflow dags info etl_postgres_to_multi_db

# Запуск DAG вручную
docker-compose exec airflow-webserver \
  airflow dags trigger etl_postgres_to_multi_db

# Список задач в DAG
docker-compose exec airflow-webserver \
  airflow tasks list etl_postgres_to_multi_db

# Просмотр логов задачи
docker-compose exec airflow-webserver \
  airflow tasks log etl_postgres_to_multi_db extract_postgres 2026-01-18
```

### Управление переменными и подключениями

```bash
# Установить переменную
docker-compose exec airflow-webserver \
  airflow variables set MY_VARIABLE "my_value"

# Получить переменную
docker-compose exec airflow-webserver \
  airflow variables get MY_VARIABLE

# Создать подключение PostgreSQL
docker-compose exec airflow-webserver \
  airflow connections add 'postgres_conn' \
  --conn-type 'postgres' \
  --conn-host 'postgres' \
  --conn-port '5432' \
  --conn-login 'postgres' \
  --conn-password 'postgres' \
  --conn-schema 'source_database'

# Список подключений
docker-compose exec airflow-webserver airflow connections list
```

### Проверка БД

```bash
# PostgreSQL
docker-compose exec postgres \
  psql -U postgres -d source_database -c "SELECT * FROM source_table LIMIT 5;"

# ClickHouse
docker-compose exec clickhouse \
  clickhouse-client --query "SELECT * FROM etl_db.etl_table LIMIT 5;"

# Cassandra
docker-compose exec cassandra \
  cqlsh -e "SELECT * FROM etl_keyspace.etl_table LIMIT 5;"
```

### Остановка и перезапуск

```bash
# Остановка всех контейнеров
docker-compose stop

# Перезапуск конкретного сервиса
docker-compose restart airflow-scheduler

# Полное удаление (осторожно - удалит данные!)
docker-compose down -v

# Пересборка образов
docker-compose build --no-cache
docker-compose up -d
```

---

## СОЗДАНИЕ СОБСТВЕННОГО DAG

### Простой пример

```python
# dags/my_first_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'my-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def my_task():
    print("✓ Моя первая задача в Airflow!")
    return "Success"

dag = DAG(
    dag_id='my_first_dag',
    default_args=default_args,
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
)

task1 = PythonOperator(
    task_id='my_task',
    python_callable=my_task,
    dag=dag,
)
```

Сохраните в `dags/my_first_dag.py` и он автоматически загрузится!

---

## РЕШЕНИЕ ЧАСТЫХ ПРОБЛЕМ

### Проблема: "Контейнер не запускается"

```bash
# Проверить логи
docker-compose logs [service_name]

# Пересоздать контейнер
docker-compose down
docker-compose up -d
```

### Проблема: "DAG не появляется в UI"

```bash
# Проверить синтаксис Python
python3 -m py_compile dags/your_dag.py

# Проверить загруженные DAG
docker-compose exec airflow-webserver airflow dags list

# Проверить логи парсера
docker-compose logs airflow-scheduler | grep "DAG"
```

### Проблема: "Недостаточно памяти"

```bash
# Уменьшить переменные в .env
ETL_BATCH_SIZE=5000  # Вместо 10000
ETL_RETRY_ATTEMPTS=2  # Вместо 3

# Перезапустить
docker-compose down
docker-compose up -d
```

### Проблема: "Порт уже занят"

```bash
# Найти процесс, занимающий порт 8080
lsof -i :8080

# Изменить порт в docker-compose.yml или .env
AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8081

# Или убить процесс
kill -9 <PID>
```

---

## ФАЙЛЫ ПРОЕКТА

### Основные файлы

| Файл | Описание |
|------|---------|
| `docker-compose.yml` | Конфигурация контейнеров |
| `Dockerfile` | Docker образ для Airflow |
| `requirements.txt` | Python зависимости |
| `.env` | Переменные окружения |
| `dags/` | DAG файлы |
| `plugins/` | Пользовательские плагины |
| `logs/` | Логи (смонтировано с контейнера) |
| `scripts/` | Вспомогательные скрипты |

### DAG файлы

| DAG | Описание |
|-----|---------|
| `etl_postgres_to_multi_db.py` | PostgreSQL → ClickHouse + Cassandra |
| `etl_csv_to_databases.py` | CSV → ClickHouse + Cassandra |
| `etl_hdfs_to_databases.py` | HDFS → ClickHouse + Cassandra |

---

## КОНТАКТЫ

**Team:** Data Engineering  
**Email:** data-eng@example.com  
**Slack:** #data-engineering  

**Documentation:** [Полное руководство](./airflow_setup_guide.md)

---

**Версия:** 1.0  
**Дата:** 18 января 2026  
**Статус:** ✓ Готово к использованию
