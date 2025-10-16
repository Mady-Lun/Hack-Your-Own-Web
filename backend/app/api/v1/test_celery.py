"""
API endpoints for testing Celery tasks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from celery.result import AsyncResult
from app.core.celery_app import celery_app
from app.tasks.test_tasks import multiply_with_sleep

router = APIRouter()


@router.get("/health")
def health_check():
    """Simple health check to verify the router is working"""
    return {"status": "ok", "message": "Test Celery router is working"}


class MultiplyRequest(BaseModel):
    x: int = Field(..., description="First number to multiply")
    y: int = Field(..., description="Second number to multiply")
    sleep_seconds: int = Field(default=5, ge=1, le=30, description="Processing time in seconds (1-30)")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    result: dict | None = None
    info: dict | None = None


@router.post("/multiply", response_model=TaskResponse)
def start_multiplication_task(request: MultiplyRequest):
    """
    Start a background multiplication task with sleep delay.

    This endpoint demonstrates Celery's background task processing.
    It will multiply two numbers after sleeping for the specified duration,
    updating progress along the way.
    """
    try:
        task = multiply_with_sleep.apply_async(
            args=[request.x, request.y, request.sleep_seconds]
        )

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Task started to multiply {request.x} × {request.y}. Check status with task_id: {task.id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Failed to start task. Make sure Celery worker and Redis are running."
            }
        )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """
    Get the status of a background task.

    Returns the current state (PENDING, PROGRESS, SUCCESS, FAILURE)
    and any available result or progress information.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    response = TaskStatusResponse(
        task_id=task_id,
        state=task_result.state,
        result=None,
        info=None
    )

    if task_result.state == 'PENDING':
        response.info = {
            'status': 'Task is waiting to be processed...'
        }
    elif task_result.state == 'PROGRESS':
        response.info = task_result.info
    elif task_result.state == 'SUCCESS':
        response.result = task_result.result
    elif task_result.state == 'FAILURE':
        response.info = {
            'status': 'Task failed',
            'error': str(task_result.info)
        }
    else:
        response.info = {
            'status': f'Task state: {task_result.state}'
        }

    return response


@router.get("/result/{task_id}")
def get_task_result(task_id: str):
    """
    Get the final result of a completed task.
    Raises an error if the task is not yet complete.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    if not task_result.ready():
        raise HTTPException(
            status_code=202,
            detail={
                "message": "Task is still processing",
                "state": task_result.state,
                "info": task_result.info if task_result.state == 'PROGRESS' else None
            }
        )

    if task_result.failed():
        raise HTTPException(
            status_code=500,
            detail={"message": "Task failed", "error": str(task_result.info)}
        )

    return {
        "task_id": task_id,
        "state": task_result.state,
        "result": task_result.result
    }
