from celery import Celery
from .config import get_settings

settings = get_settings()

REDIS_URL=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

# Initialize Celery with settings
celery = Celery(
    'sentiment_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.sentiment']  # Register the tasks module
)

# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)