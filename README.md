# Airflow ETL Pipeline: PostgreSQL → ClickHouse & Cassandra

Полнофункциональная система оркестрации данных с использованием Apache Airflow, Docker и контейнеризацией.

## 🚀 Быстрый старт

### Предварительные требования

- Docker (версия 20.10+)
- Docker Compose (версия 1.29+)
- Git
- Python 3.8+ (для локальной разработки)

### Установка и запуск

```bash
# 1. Клонирование репозитория
git clone https://github.com/your-org/airflow-etl.git
cd airflow-etl

# 2. Копирование файла конфигурации
cp .env.example .env

# 3. Генерация Fernet ключа (для шифрования)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Поместить результат в AIRFLOW__CORE__FERNET_KEY в .env

# 4. Запуск Docker Compose
docker-compose up -d

# 5. Проверка статуса контейнеров
docker-compose ps

# 6. Доступ к Web UI
# Перейти на http://localhost:8080
# Username: airflow
# Password: airflow
```

## 📊 Архитектура системы

```
┌──────────────────────────────────────────────────────────────┐
│                    ИСТОЧНИКИ ДАННЫХ                          │
├──────────────────────────────────────────────────────────────┤
│ PostgreSQL │ CSV файлы │ HDFS │ Другие БД                   │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│            APACHE AIRFLOW (Оркестратор)                      │
├──────────────────────────────────────────────────────────────┤
│ - Scheduler    - Web UI    - Worker    - DAG    - Flower     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│          ЦЕЛЕВЫЕ БАЗЫ ДАННЫХ (Хранилища)                    │
├──────────────────────────────────────────────────────────────┤
│    ClickHouse    │    Cassandra    │   PostgreSQL            │
└──────────────────────────────────────────────────────────────┘
```

## 🏗️ Структура проекта

```
airflow-etl-project/
├── dags/                          # DAG файлы
│   ├── etl_postgres_to_multi_db.py
│   ├── etl_csv_to_databases.py
│   └── etl_hdfs_to_databases.py
├── plugins/                       # Пользовательские плагины и хуки
│   ├── operators/
│   ├── hooks/
│   └── utils/
├── config/                        # Конфигурационные файлы
│   ├── airflow.cfg
│   └── logging_config.py
├── scripts/                       # Вспомогательные скрипты
│   ├── init_databases.sh
│   ├── clickhouse_init.sql
│   ├── cassandra_init.cql
│   └── create_tables.sql
├── tests/                         # Тесты
│   ├── test_dags.py
│   ├── test_operators.py
│   └── conftest.py
├── ci-cd/                         # CI/CD конфиги
│   ├── .github/workflows/
│   ├── .gitlab-ci.yml
│   └── Jenkinsfile
├── docker/                        # Docker файлы
│   └── Dockerfile
├── logs/                          # Логи (создаются автоматически)
├── docker-compose.yml             # Docker Compose конфигурация
├── Dockerfile                     # Docker конфигурация
├── requirements.txt               # Python зависимости
├── .env.example                   # Пример конфигурации
├── .gitignore                     # Исключения для Git
└── README.md                      # Этот файл
```

## 🔧 Конфигурация

### Окружение (.env)

Скопируйте `.env.example` в `.env` и отредактируйте:

```bash
cp .env.example .env
```

Важные переменные:
- `AIRFLOW__CORE__FERNET_KEY` - Ключ шифрования (генерируется)
- `POSTGRES_PASSWORD` - Пароль PostgreSQL
- `CLICKHOUSE_DATABASE` - База данных ClickHouse
- `CASSANDRA_KEYSPACE` - Keyspace Cassandra

## 📦 Компоненты системы

### Apache Airflow

**Webserver** (Веб-интерфейс)
- Доступен на http://localhost:8080
- Управление и мониторинг DAG
- Просмотр истории выполнения

**Scheduler** (Планировщик)
- Отслеживает состояние DAG
- Запускает задачи в установленное время
- Управляет переиспытаниями

**Worker** (Рабочий процесс)
- Выполняет фактические задачи
- Celery для распределенной обработки

**Flower** (Мониторинг Celery)
- Доступен на http://localhost:5555
- Отслеживание задач на workers

### PostgreSQL

- Хранение метаданных Airflow
- Источник данных для ETL
- Порт: 5432

### ClickHouse

- OLAP хранилище для аналитики
- Оптимизирована для аналитических запросов
- Порты: 9000 (native), 8123 (HTTP)

### Cassandra

- NoSQL распределенное хранилище
- Горизонтальное масштабирование
- Порт: 9042

### Redis

- Message broker для очереди задач
- Коммуникация scheduler-worker
- Порт: 6379

## 🚦 Команды Docker Compose

```bash
# Запуск контейнеров
docker-compose up -d

# Остановка контейнеров
docker-compose down

# Просмотр логов
docker-compose logs -f airflow-webserver

# Просмотр логов конкретного сервиса
docker-compose logs -f postgres

# Запуск команды в контейнере
docker-compose exec airflow-webserver airflow dags list

# Перезапуск сервиса
docker-compose restart airflow-scheduler

# Удаление контейнеров и томов (осторожно!)
docker-compose down -v
```

## 📝 DAG примеры

### 1. PostgreSQL → ClickHouse & Cassandra

```python
# dags/etl_postgres_to_multi_db.py

Основной DAG для ETL процесса:
1. Извлечение данных из PostgreSQL
2. Трансформация и валидация
3. Загрузка в ClickHouse
4. Загрузка в Cassandra
5. Проверка целостности
```

### 2. CSV → ClickHouse & Cassandra

```python
# dags/etl_csv_to_databases.py

Загрузка данных из CSV файлов в оба хранилища
```

### 3. HDFS → ClickHouse & Cassandra

```python
# dags/etl_hdfs_to_databases.py

Загрузка данных из HDFS с использованием Spark
```

## 🔐 Безопасность

### Конфиденциальные данные

Используйте Airflow Variables для хранения конфиденциальных данных:

```bash
# Через Web UI: Admin > Variables
# Или через CLI:
docker-compose exec airflow-webserver \
  airflow variables set SENSITIVE_KEY "sensitive_value"
```

### Шифрование

Fernet ключ используется для шифрования конфиденциальных данных в Airflow:

```python
# Автоматически обрабатывается Airflow
from airflow.models import Variable
secret = Variable.get("MY_SECRET", deserialize_json=False)
```

## 📊 Мониторинг

### Prometheus метрики

Метрики доступны на `/admin/xcom` в Airflow UI.

### Логирование

Логи сохраняются в:
- `/opt/airflow/logs/` - в контейнере
- `./logs/` - на хосте (смонтировано)

## 🧪 Тестирование

```bash
# Запуск тестов
docker-compose exec airflow-webserver pytest tests/

# С отчетом о покрытии
docker-compose exec airflow-webserver \
  pytest tests/ --cov=dags --cov-report=html

# Проверка DAG синтаксиса
docker-compose exec airflow-webserver \
  python -m py_compile dags/*.py

# Список загруженных DAG
docker-compose exec airflow-webserver airflow dags list
```

## 🚚 CI/CD

### GitHub Actions

Конфигурация: `.github/workflows/deploy.yml`

Функции:
- Lint и format проверка
- Unit тесты
- Docker build
- Развертывание на staging
- Развертывание в production

### GitLab CI

Конфигурация: `.gitlab-ci.yml`

### Jenkins

Конфигурация: `Jenkinsfile`

## 🐛 Решение проблем

### PostgreSQL недоступна

```bash
# Проверить статус
docker-compose ps postgres

# Просмотреть логи
docker-compose logs postgres

# Перезапустить
docker-compose restart postgres

# Проверить подключение
docker-compose exec postgres \
  psql -U postgres -c "SELECT 1"
```

### ClickHouse недоступна

```bash
# Проверить статус
docker-compose ps clickhouse

# Проверить версию
docker-compose exec clickhouse \
  clickhouse-client --query "SELECT version()"

# Просмотреть логи
docker-compose logs clickhouse
```

### Cassandra не инициализируется

```bash
# Очистить данные и перезапустить
docker-compose down
docker volume rm airflow-etl-project_cassandra_data
docker-compose up -d

# Проверить статус кластера
docker-compose exec cassandra \
  nodetool status
```

### DAG не появляется

```bash
# Проверить синтаксис
python3 -m py_compile dags/your_dag.py

# Список DAG
docker-compose exec airflow-webserver airflow dags list

# Логи парсера
docker-compose logs airflow-scheduler | grep "DAG"

# Права доступа
docker-compose exec airflow-webserver \
  ls -la /opt/airflow/dags/
```

## 📚 Документация

- [Apache Airflow](https://airflow.apache.org/docs/)
- [ClickHouse](https://clickhouse.com/docs/)
- [Cassandra](https://cassandra.apache.org/doc/)
- [Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## 📞 Контакты и поддержка

- **Team:** Data Engineering
- **Email:** data-eng@example.com
- **Slack:** #data-engineering

## 📄 Лицензия

MIT License - см. LICENSE файл

## 🤝 Как способствовать проекту

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 🔄 История изменений

### Version 1.0 (2026-01-18)

- Инициальный релиз
- Поддержка PostgreSQL, ClickHouse, Cassandra
- CI/CD интеграция (GitHub Actions, GitLab CI)
- Docker Compose конфигурация
- DAG примеры
- Документация

---

**Последнее обновление:** 18 января 2026
**Автор:** Data Engineering Team
**Язык:** Русский (Russian)
**Кодировка:** UTF-8
