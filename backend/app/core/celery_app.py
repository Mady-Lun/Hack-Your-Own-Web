from celery import Celery
from kombu import Queue, Exchange
from app.core.config import CeleryConfig

celery_app = Celery(
    "hack_your_own_web",
    broker=CeleryConfig.CELERY_BROKER_URL,
    backend=CeleryConfig.CELERY_RESULT_BACKEND,
    include=["app.tasks.scan_tasks", "app.tasks.domain_verification"]
)

# Define priority queues for scans
default_exchange = Exchange('default', type='direct')

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,

    # Define queues (FIFO - First In First Out)
    task_queues=(
        Queue('scan_queue', exchange=default_exchange, routing_key='scan_queue'),
        Queue('domain_verification_queue', exchange=default_exchange, routing_key='domain_verification_queue'),
    ),
)

# Task routes for different queues (must match docker-compose worker -Q flag)
celery_app.conf.task_routes = {
    "app.tasks.scan_tasks.run_scan": {"queue": "scan_queue"},
    "app.tasks.scan_tasks.cancel_scan": {"queue": "scan_queue"},
    "app.tasks.domain_verification.verify_domain_task": {"queue": "domain_verification_queue"},
}
