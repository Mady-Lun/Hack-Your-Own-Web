
from app.core.celery_app import celery_app

# Import tasks to ensure they're registered
from app.tasks import scan_tasks  # noqa: F401

if __name__ == "__main__":
    celery_app.start()
