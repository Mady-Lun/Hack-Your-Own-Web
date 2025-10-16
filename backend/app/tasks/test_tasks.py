"""
Test tasks for Celery background processing
"""
import time
from celery import shared_task
from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.test_tasks.multiply_with_sleep")
def multiply_with_sleep(self, x: int, y: int, sleep_seconds: int = 5):
    """
    Simple multiplication task with sleep to demonstrate background processing.

    Args:
        x: First number
        y: Second number
        sleep_seconds: Time to sleep in seconds (default: 5)

    Returns:
        dict with calculation result and metadata
    """
    # Update task state to show it's processing
    self.update_state(
        state='PROGRESS',
        meta={
            'current': 0,
            'total': sleep_seconds,
            'status': f'Starting multiplication of {x} × {y}...'
        }
    )

    # Simulate processing with sleep and progress updates
    for i in range(sleep_seconds):
        time.sleep(1)
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': sleep_seconds,
                'status': f'Processing... ({i + 1}/{sleep_seconds} seconds)',
                'progress_percent': int((i + 1) / sleep_seconds * 100)
            }
        )

    # Calculate result
    result = x * y

    # Return final result
    return {
        'status': 'completed',
        'x': x,
        'y': y,
        'result': result,
        'message': f'Successfully calculated {x} × {y} = {result}',
        'processing_time_seconds': sleep_seconds
    }
