import os

from celery import Celery
from celery.schedules import crontab
from structlog import get_logger

logger = get_logger(__name__)

# Default to local Redis if not specified
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"  # Using a different DB for results

# Initialize Celery
celery_app = Celery(
    "oil_gas_pipeline_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["src.tasks"],  # Points to the module where tasks are defined
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",  # Important for crontab schedules
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Celery Beat Schedules
celery_app.conf.beat_schedule = {
    "daily-data-ingestion": {
        "task": "src.tasks.run_daily_data_ingestion",  # Name of the task
        # "schedule": crontab(hour=1, minute=0),  # Run daily at 1:00 AM UTC
        "schedule": crontab(minute="*/5"),  # Every 5 minutes for testing
    },
}

logger.info(
    "Celery application configured",
    broker_url=CELERY_BROKER_URL,
    beat_schedule=celery_app.conf.beat_schedule,
)

if __name__ == "__main__":
    # This allows running celery worker/beat directly for development if needed,
    # though Docker is preferred.
    # Example: python -m src.celery_app worker -l info
    # Example: python -m src.celery_app beat -l info
    celery_app.start()
