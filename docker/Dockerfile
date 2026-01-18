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
    vim \
    default-jdk \
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
