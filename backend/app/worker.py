"""
Celery Worker Entry Point

This module initializes and configures the Celery worker for handling
background tasks such as security scans.

Usage:
    celery -A app.worker worker --loglevel=info --concurrency=11
"""

from app.core.celery_app import celery_app

# Import tasks to ensure they're registered
from app.tasks import scan_tasks  # noqa: F401

if __name__ == "__main__":
    celery_app.start()
