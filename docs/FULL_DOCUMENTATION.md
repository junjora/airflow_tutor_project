# СИСТЕМА AIRFLOW ETL: ПОЛНАЯ ДОКУМЕНТАЦИЯ И ИНСТРУКЦИИ

## 📋 СОДЕРЖАНИЕ

1. [Обзор проекта](#обзор-проекта)
2. [Архитектура и компоненты](#архитектура-и-компоненты)
3. [Установка и запуск](#установка-и-запуск)
4. [Описание всех файлов проекта](#описание-всех-файлов-проекта)
5. [Подробное описание компонентов](#подробное-описание-компонентов)
6. [DAG примеры и объяснения](#dag-примеры-и-объяснения)
7. [CI/CD процесс](#cicd-процесс)
8. [Мониторинг и логирование](#мониторинг-и-логирование)
9. [Тестирование](#тестирование)
10. [Решение проблем](#решение-проблем)
11. [Масштабирование](#масштабирование)

---

## ОБЗОР ПРОЕКТА

### Цель

Создать надежную, масштабируемую систему оркестрации данных (ETL pipeline) с использованием Apache Airflow для:

- Извлечения данных из PostgreSQL
- Трансформации и валидации данных
- Загрузки в ClickHouse (OLAP) и Cassandra (NoSQL)
- Поддержки CSV и HDFS источников
- Автоматизации с CI/CD процессом

### Ключевые особенности

✓ **Контейнеризация** - Полная Docker Compose конфигурация  
✓ **Масштабируемость** - Celery executor с multiple workers  
✓ **Надежность** - Обработка ошибок, retry логика  
✓ **Мониторинг** - Flower, логирование, metrics  
✓ **Безопасность** - Шифрование, управление доступом  
✓ **CI/CD** - GitHub Actions, GitLab CI, Jenkins  

---

## АРХИТЕКТУРА И КОМПОНЕНТЫ

### Системная архитектура

```
层 1: ИСТОЧНИКИ (SOURCES)
├─ PostgreSQL (транзакционные данные)
├─ CSV файлы (batch данные)
├─ HDFS (big data)
└─ Другие БД

        ↓

層 2: ОРКЕСТРАТОР (ORCHESTRATOR)
├─ Apache Airflow (DAG оркестрация)
├─ Scheduler (запланирование)
├─ Worker (выполнение задач)
├─ Webserver (UI управления)
└─ Flower (мониторинг Celery)

        ↓

層 3: ХРАНИЛИЩА (STORAGE)
├─ ClickHouse (OLAP аналитика)
├─ Cassandra (NoSQL масштабирование)
└─ PostgreSQL (метаданные)

        ↓

層 4: ПОДДЕРЖКА (INFRASTRUCTURE)
├─ Docker (контейнеризация)
├─ Redis (message broker)
├─ PostgreSQL (metadata DB)
└─ Network (связность)
```

### Компоненты системы

| Компонент | Роль | Порт | Технология |
|-----------|------|------|-----------|
| **Airflow Webserver** | Управление DAG | 8080 | Python/Flask |
| **Airflow Scheduler** | Планирование задач | - | Python |
| **Celery Worker** | Выполнение задач | - | Python/Celery |
| **Flower** | Мониторинг Celery | 5555 | Python |
| **PostgreSQL** | Metadata DB | 5432 | PostgreSQL 16 |
| **Redis** | Message Broker | 6379 | Redis 7 |
| **ClickHouse** | OLAP хранилище | 9000/8123 | ClickHouse 24 |
| **Cassandra** | NoSQL хранилище | 9042 | Cassandra 5 |

---

## УСТАНОВКА И ЗАПУСК

### Требования к системе

```
Минимум для DEV:
- CPU: 4 ядра
- RAM: 8 GB
- Диск: 50 GB

Рекомендуется для PROD:
- CPU: 8+ ядер
- RAM: 16+ GB
- Диск: 100+ GB
```

### Пошаговая установка

#### Шаг 1: Установка Docker

```bash
# macOS
brew install docker docker-compose

# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

#### Шаг 2: Клонирование проекта

```bash
git clone https://github.com/your-org/airflow-etl-project.git
cd airflow-etl-project
```

#### Шаг 3: Конфигурация

```bash
# Копирование файла конфигурации
cp .env.example .env

# Редактирование критических параметров
nano .env  # или vim .env

# Генерация Fernet ключа
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Вставить в AIRFLOW__CORE__FERNET_KEY
```

#### Шаг 4: Запуск

```bash
# Запуск всех контейнеров в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps

# Проверка логов инициализации
docker-compose logs -f airflow-init
```

#### Шаг 5: Первоначальная настройка

```bash
# Подождать пока все контейнеры будут healthy (2-3 минуты)
sleep 180

# Создание дополнительного пользователя (опционально)
docker-compose exec airflow-webserver \
  airflow users create \
  --username admin \
  --password admin123 \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

#### Шаг 6: Доступ

```
Web UI:   http://localhost:8080
User:     airflow
Password: airflow

Flower:   http://localhost:5555
```

---

## ОПИСАНИЕ ВСЕХ ФАЙЛОВ ПРОЕКТА

### Структура директорий

```
airflow-etl-project/
│
├── dags/                                  # DAG файлы
│   ├── __init__.py                        # Python пакет маркер
│   ├── etl_postgres_to_multi_db.py        # Основной DAG: PostgreSQL → Multi DB
│   ├── etl_csv_to_databases.py            # DAG: CSV → Databases
│   └── etl_hdfs_to_databases.py           # DAG: HDFS → Databases
│
├── plugins/                               # Пользовательские плагины
│   ├── __init__.py
│   ├── operators/                         # Custom операторы
│   │   ├── __init__.py
│   │   └── custom_operators.py
│   ├── hooks/                             # Custom хуки
│   │   ├── __init__.py
│   │   └── custom_hooks.py
│   ├── utils/                             # Утилиты
│   │   ├── __init__.py
│   │   ├── clickhouse_utils.py
│   │   ├── cassandra_utils.py
│   │   └── postgres_utils.py
│   └── sensors/                           # Custom сенсоры
│       ├── __init__.py
│       └── file_sensors.py
│
├── config/                                # Конфигурационные файлы
│   ├── airflow.cfg                        # Основная конфиг Airflow
│   ├── logging_config.py                  # Конфиг логирования
│   └── connections_config.py              # Конфиг подключений
│
├── scripts/                               # Вспомогательные скрипты
│   ├── init_databases.sh                  # Инит PostgreSQL
│   ├── clickhouse_init.sql                # Инит ClickHouse
│   ├── cassandra_init.cql                 # Инит Cassandra
│   ├── create_tables.sql                  # Создание таблиц
│   ├── seed_data.py                       # Заполнение тестовых данных
│   └── backup.sh                          # Backup скрипт
│
├── tests/                                 # Тесты
│   ├── __init__.py
│   ├── test_dags.py                       # Тесты DAG
│   ├── test_operators.py                  # Тесты операторов
│   ├── test_utils.py                      # Тесты утилит
│   └── conftest.py                        # Pytest конфигурация
│
├── ci-cd/                                 # CI/CD конфигурации
│   ├── .github/
│   │   └── workflows/
│   │       └── deploy.yml                 # GitHub Actions workflow
│   ├── .gitlab-ci.yml                     # GitLab CI конфигурация
│   └── Jenkinsfile                        # Jenkins pipeline
│
├── docker/                                # Docker конфигурации
│   ├── Dockerfile                         # Dockerfile для Airflow
│   └── docker-compose-dev.yml             # Dev конфиг (опционально)
│
├── logs/                                  # Логи (создаются автоматически)
│   ├── airflow.log
│   ├── scheduler/
│   ├── webserver/
│   └── celery/
│
├── .github/                               # GitHub конфигурация
│   └── workflows/
│       └── deploy.yml
│
├── docker-compose.yml                     # ОСНОВНАЯ конфигурация
├── Dockerfile                             # Dockerfile для образа Airflow
├── requirements.txt                       # Python зависимости
├── .env.example                           # Пример переменных окружения
├── .env                                   # Переменные окружения (НЕ КОММИТИТЬ)
├── .gitignore                             # Git исключения
├── README.md                              # Основная документация
├── QUICK_START.md                         # Краткий гайд
├── ARCHITECTURE.md                        # Подробное описание архитектуры
└── LICENSE                                # Лицензия
```

### Ключевые файлы и их назначение

#### `docker-compose.yml`

Основной файл для управления контейнерами. Определяет:
- Все сервисы (Airflow, БД, Redis)
- Порты и маппинг томов
- Переменные окружения
- Зависимости и healthchecks
- Сетевые конфигурации

```yaml
services:
  postgres:       # Metadata DB + Source DB
  redis:          # Message broker
  clickhouse:     # OLAP хранилище
  cassandra:      # NoSQL хранилище
  airflow-init:   # Инициализация Airflow
  airflow-webserver:  # UI управления
  airflow-scheduler:  # Планировщик
  airflow-worker: # Celery worker
  flower:         # Мониторинг
```

#### `Dockerfile`

Создает Docker образ для Airflow с:
- Базовый образ Apache Airflow
- Системные зависимости
- Python пакеты из requirements.txt
- Копирование DAG и плагинов
- Health check конфигурация

#### `requirements.txt`

Все Python зависимости:
- Apache Airflow 2.8.0
- Провайдеры (Postgres, ClickHouse, Cassandra)
- Драйверы БД
- Утилиты для обработки данных
- Инструменты тестирования

#### `.env` файл

Критические переменные окружения:
- Пароли БД (НИКОГДА НЕ КОММИТИТЬ!)
- Конфигурация Airflow
- Параметры ETL
- Хосты и порты сервисов

#### `dags/*.py`

DAG файлы - определение рабочих процессов:
- Задачи (tasks)
- Зависимости между задачами
- График выполнения
- Параметры обработки

---

## ПОДРОБНОЕ ОПИСАНИЕ КОМПОНЕНТОВ

### 1. Apache Airflow

#### Webserver

```python
# Запускается на порту 8080
http://localhost:8080

Функции:
- Управление DAG (включить/отключить)
- Триггер запуска DAG
- Просмотр истории выполнения
- Просмотр логов задач
- Управление переменными и подключениями
- Просмотр SLA (Service Level Agreements)
```

#### Scheduler

```python
# Основной процесс оркестрации

Роль:
- Отслеживание всех DAG
- Определение готовности к запуску
- Создание task instances
- Передача в очередь
- Управление retry логикой

Конфигурация:
dag_dir_list_interval = 300          # Проверка новых DAG каждые 5 мин
scheduler_loop_interval = 1          # Цикл планирования каждую секунду
max_active_runs_per_dag = 16         # Макс активных запусков
```

#### Worker (Celery)

```python
# Выполнение фактических задач

Конфигурация:
executor = CeleryExecutor            # Распределенное выполнение
broker_url = redis://:@redis:6379/0  # Redis для очереди
result_backend = PostgreSQL           # Хранение результатов

Процесс:
1. Scheduler отправляет task в Redis очередь
2. Свободный Worker берет task из очереди
3. Worker выполняет task логику
4. Результат отправляется в PostgreSQL
5. Scheduler получает уведомление
```

#### Flower (Celery Monitoring)

```
http://localhost:5555

Функции:
- Визуализация workers
- Просмотр активных задач
- Статистика выполнения
- Управление workers
- Диагностика проблем
```

### 2. PostgreSQL

```
Роль:
1. Metadata Database для Airflow
   - История DAG runs
   - Статусы задач
   - Variables и Connections
   - Logs

2. Source Database
   - Исходные данные для ETL
   - Таблица: source_table
   - Индексы для быстрого доступа

Подключение:
Host: postgres
Port: 5432
User: postgres
Password: postgres (меняется в .env)
Database: 
  - airflow (метаданные)
  - source_database (исходные данные)
```

### 3. ClickHouse

```
Роль:
- OLAP хранилище для аналитики
- Columnar формат для быстрых запросов
- Оптимизирована для SELECT
- Партиционирование по времени

Подключение:
Native: localhost:9000
HTTP: localhost:8123

Таблицы:
- etl_db.etl_table (основная)
- etl_db.csv_loaded_table
- etl_db.hdfs_loaded_table

Engine: MergeTree
- ORDER BY для быстрого поиска
- PRIMARY KEY для индексирования
- PARTITION BY для разделения
```

### 4. Cassandra

```
Роль:
- NoSQL распределенное хранилище
- Горизонтальное масштабирование
- High availability (HA)
- Реплицирование данных

Подключение:
Host: cassandra
Port: 9042
Keyspace: etl_keyspace

Таблицы:
- etl_keyspace.etl_table
- etl_keyspace.csv_loaded_table

Replication: SimpleStrategy
Replication Factor: 1 (DEV), 3 (PROD)
```

### 5. Redis

```
Роль:
- Message Broker для Celery
- Очередь задач (queue)
- Временное хранилище

Конфигурация:
Host: redis
Port: 6379
Database: 0

Использование:
- Airflow → Redis: отправка task
- Redis → Worker: передача task
- Worker → Redis: отправка результата
```

---

## DAG ПРИМЕРЫ И ОБЪЯСНЕНИЯ

### DAG 1: PostgreSQL → ClickHouse & Cassandra

**Файл:** `dags/etl_postgres_to_multi_db.py`

```python
Этапы выполнения:

1. extract_postgres
   ↓
   Подключается к PostgreSQL
   Выполняет SELECT за последний день
   Конвертирует в DataFrame
   Сохраняет в XCom

2. transform_data
   ↓
   Получает данные из XCom
   Удаляет null значения
   Нормализует типы данных
   Добавляет служебные колонки
   Удаляет дубликаты

3. load_clickhouse & load_cassandra (параллельно)
   ↓
   ClickHouse:
   - Создает таблицу если ее нет
   - Вставляет данные
   - Использует MergeTree engine
   
   Cassandra:
   - Создает keyspace
   - Вставляет данные по строкам
   - Использует UUID как primary key

4. verify_data
   ↓
   Проверяет количество строк
   Сравнивает ClickHouse ↔ Cassandra
   Логирует результаты
```

**Использование:**

```bash
# Просмотр DAG в Web UI
http://localhost:8080/dag/etl_postgres_to_multi_db

# Запуск вручную
docker-compose exec airflow-webserver \
  airflow dags trigger etl_postgres_to_multi_db

# Просмотр логов
docker-compose exec airflow-webserver \
  airflow tasks log etl_postgres_to_multi_db extract_postgres 2026-01-18
```

### DAG 2: CSV → ClickHouse & Cassandra

**Файл:** `dags/etl_csv_to_databases.py`

```python
Этапы:
1. read_csv - Чтение CSV файла
2. validate - Валидация данных
3. load_clickhouse - Загрузка в ClickHouse
4. load_cassandra - Загрузка в Cassandra
5. verify - Проверка целостности
```

### DAG 3: HDFS → ClickHouse & Cassandra

**Файл:** `dags/etl_hdfs_to_databases.py`

```python
Этапы:
1. read_hdfs - Чтение Parquet из HDFS
2. transform_spark - Трансформация через Spark
3. load_clickhouse - Загрузка в ClickHouse
4. load_cassandra - Загрузка в Cassandra
5. verify - Проверка целостности
```

---

## CI/CD ПРОЦЕСС

### GitHub Actions

**Файл:** `.github/workflows/deploy.yml`

```yaml
Этапы:

1. lint-and-test
   - Lint флаг (flake8)
   - Форматирование (black)
   - Unit тесты (pytest)
   - Coverage отчет

2. build-docker
   - Сборка Docker образа
   - Push в Docker Hub (если main)

3. deploy-staging
   - Запуск на staging при commit в develop
   - SSH подключение
   - docker-compose pull && up

4. deploy-production
   - Запуск на production при commit в main
   - Manual approval требуется
   - Notification в Slack
```

### GitLab CI

**Файл:** `.gitlab-ci.yml`

```yaml
Stages:
- lint
- test
- build
- deploy_staging
- deploy_production

Artifacts:
- coverage.xml
- test reports
```

---

## МОНИТОРИНГ И ЛОГИРОВАНИЕ

### Логирование

```python
# Уровни логирования (логирование_config.py)
DEBUG   - Детальная информация для диагностики
INFO    - Основная информация о выполнении
WARNING - Предупреждения о потенциальных проблемах
ERROR   - Ошибки, требующие внимания
CRITICAL - Критические ошибки, требующие немедленного действия

# Форматы логов
standard - Человеко-читаемый формат
detailed - Расширенный формат с деталями
json - JSON формат для парсирования
```

### Мониторинг

```python
# Metrics через Prometheus
- airflow_dag_runs_total (counter)
- airflow_task_duration_seconds (histogram)
- airflow_active_tasks (gauge)

# Доступ к метрикам
/admin/xcom - XCom переменные
Flower - Celery метрики
PostgreSQL - История выполнения
```

---

## ТЕСТИРОВАНИЕ

### Unit тесты

```bash
# Запуск тестов
docker-compose exec airflow-webserver pytest tests/ -v

# С отчетом о покрытии
pytest tests/ --cov=dags --cov-report=html

# Тестирование конкретного DAG
pytest tests/test_dags.py::test_etl_postgres_to_multi_db
```

### DAG валидация

```bash
# Проверка синтаксиса
python3 -m py_compile dags/your_dag.py

# Проверка загрузки
docker-compose exec airflow-webserver airflow dags list

# Проверка конкретного DAG
docker-compose exec airflow-webserver \
  airflow dags info etl_postgres_to_multi_db
```

---

## РЕШЕНИЕ ПРОБЛЕМ

### Проблема 1: PostgreSQL не запускается

```bash
# Проверка логов
docker-compose logs postgres

# Причины:
- Порт уже занят
- Недостаточно памяти
- Файлы БД повреждены

# Решение:
docker-compose down
docker volume rm airflow-etl-project_postgres_data
docker-compose up -d postgres
```

### Проблема 2: DAG не появляется

```bash
# Проверки:
1. Синтаксис Python
   python3 -m py_compile dags/my_dag.py

2. Правильная структура DAG
   - Должен быть объект DAG
   - Должны быть задачи (tasks)
   - Должны быть зависимости

3. Логирование
   docker-compose logs airflow-scheduler | grep -i DAG

4. Права доступа
   docker-compose exec airflow-webserver \
     ls -la /opt/airflow/dags/
```

### Проблема 3: Task падает с ошибкой

```bash
# Просмотр логов задачи
docker-compose exec airflow-webserver \
  airflow tasks log DAG_ID TASK_ID DATE

# Проверка:
1. Подключение к БД
2. Достаточно памяти
3. Синтаксис SQL/Python
4. Файлы/данные доступны

# Debugging:
- Добавить print() в коде
- Использовать logging.info()
- Проверить XCom переменные
```

---

## МАСШТАБИРОВАНИЕ

### Горизонтальное масштабирование Workers

```bash
# Добавить нового worker
docker-compose up -d --scale airflow-worker=3
```

### Увеличение пула задач

```env
# В .env
AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=32  # Вместо 16
AIRFLOW__CELERY__WORKER_CONCURRENCY=8       # Задач на worker
```

### Оптимизация ClickHouse

```sql
-- Параллельное выполнение
SET max_threads = 8;

-- Кэширование результатов
SET enable_http_compression = 1;

-- Партиции по времени
ALTER TABLE etl_db.etl_table
MODIFY ORDER BY (created_at, id);
```

### Оптимизация Cassandra

```cql
-- Replication factor для HA
ALTER KEYSPACE etl_keyspace
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};

-- Consistency level
CONSISTENCY QUORUM;
```

---

## ЗАКЛЮЧЕНИЕ

Эта система обеспечивает:

✓ **Надежность** - Retry логика, error handling  
✓ **Масштабируемость** - Горизонтальное расширение  
✓ **Мониторинг** - Полная видимость процессов  
✓ **Гибкость** - Поддержка множества источников/целей  
✓ **Безопасность** - Шифрование, управление доступом  
✓ **Простота** - Docker Compose для быстрого старта  

**Для получения помощи:**
- Документация: https://airflow.apache.org/docs/
- Issues: GitHub Issues
- Slack: #data-engineering

---

**Версия:** 1.0  
**Дата:** 18 января 2026  
**Язык:** Русский (UTF-8)  
**Статус:** ✓ Готово
