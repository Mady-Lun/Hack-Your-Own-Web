# Celery Background Task Test

This is a simple test to demonstrate Celery's background task processing capabilities using a multiplication task with sleep delay.

## Test Task Overview

The test task (`multiply_with_sleep`) does the following:
- Takes two numbers (x and y) and a sleep duration
- Simulates processing by sleeping for the specified duration
- Updates progress every second
- Returns the multiplication result after completion

## Setup Instructions

### 1. Make sure Redis is running

If you're using Docker:
```bash
docker-compose up redis
```

Or start Redis locally if installed.

### 2. Start the Celery Worker

Open a terminal and run:
```bash
cd backend
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

You should see output indicating the worker is ready and connected to Redis.

### 3. Start the FastAPI Application

Open another terminal and run:
```bash
cd backend
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### 4. Run the Test

#### Option A: Using the Python Test Script (Recommended)

Open a third terminal and run:
```bash
cd backend
python test_multiply_task.py
```

This will:
- Start a multiplication task (7 × 8 with 10 seconds processing)
- Display a progress bar showing real-time status
- Show the final result when complete

Expected output:
```
============================================================
Testing Celery Background Task Processing
============================================================

📤 Starting multiplication task (7 × 8 with 10 seconds processing)...
✅ Task started successfully!
   Task ID: abc123-def456-...
   Status: started

🔄 Monitoring task progress...
------------------------------------------------------------
   [██████████████████████████████] 100% - Processing... (10/10 seconds)

✅ Task completed successfully!
------------------------------------------------------------
   Result: 7 × 8 = 56
   Message: Successfully calculated 7 × 8 = 56
   Processing time: 10 seconds
------------------------------------------------------------
```

#### Option B: Using the API Directly

You can also test using the FastAPI docs at http://localhost:8000/docs

1. Navigate to the "Celery Testing" section
2. Use the `POST /api/v1/test-celery/multiply` endpoint to start a task
3. Copy the `task_id` from the response
4. Use the `GET /api/v1/test-celery/status/{task_id}` endpoint to check progress
5. Keep checking until the state is "SUCCESS"

#### Option C: Using curl

Start a task:
```bash
curl -X POST "http://localhost:8000/api/v1/test-celery/multiply" \
  -H "Content-Type: application/json" \
  -d '{"x": 7, "y": 8, "sleep_seconds": 10}'
```

Check status (replace TASK_ID with the actual task ID):
```bash
curl "http://localhost:8000/api/v1/test-celery/status/TASK_ID"
```

## What to Observe

### In the Celery Worker Terminal:
You should see:
- Task received: `app.tasks.test_tasks.multiply_with_sleep`
- Task progress updates
- Task success with result

### In the Test Script:
- Real-time progress bar updating every second
- Final result displayed when complete

### In the API:
- Task ID returned immediately (non-blocking)
- Status endpoint shows PENDING → PROGRESS → SUCCESS
- Progress info includes current step, total steps, and percentage

## Troubleshooting

1. **Connection Error**: Make sure the FastAPI app is running on port 8000
2. **Task stays PENDING**: Make sure the Celery worker is running
3. **Redis Connection Error**: Make sure Redis is running and accessible
4. **Import Errors**: Make sure you're in the backend directory and all dependencies are installed

## Testing Different Scenarios

Modify the test script or API request to test:
- Different numbers: `{"x": 15, "y": 3, "sleep_seconds": 5}`
- Longer processing: `{"x": 100, "y": 200, "sleep_seconds": 20}`
- Quick test: `{"x": 2, "y": 3, "sleep_seconds": 3}`

## Files Created

- `app/tasks/test_tasks.py` - The multiplication task implementation
- `app/api/v1/test_celery.py` - API endpoints for testing
- `test_multiply_task.py` - Python test script with progress visualization
- `CELERY_TEST_INSTRUCTIONS.md` - This file
