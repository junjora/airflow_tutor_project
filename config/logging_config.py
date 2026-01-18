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
