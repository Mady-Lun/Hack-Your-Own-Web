# Testing Celery with test_multiply Task

This guide provides step-by-step instructions for testing Celery background task processing using the multiplication task demo.

## Overview

The `test_multiply_task.py` script demonstrates Celery's asynchronous task processing capabilities by:
- Running a multiplication task in the background
- Showing real-time progress updates
- Displaying the final result after completion

## Prerequisites

Ensure all dependencies are installed:
```bash
cd backend
pip install -r requirements.txt
```

## Step-by-Step Testing Instructions

### Step 1: Start Redis

Redis is required as the message broker for Celery.

**Using Docker Compose:**
```bash
docker-compose up redis
```

**Using Local Redis:**
Make sure Redis is running on your system (default port 6379).

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

---

### Step 2: Start the Celery Worker

Open a **new terminal window** and run:

```bash
cd backend
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

**Expected Output:**
```
 -------------- celery@YourComputerName v5.x.x
---- **** -----
--- * ***  * -- Windows-10.x.x
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         celery_app:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
*** --- * --- .> concurrency:  1 (solo)
-- ******* ---- .> task events: OFF
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . app.tasks.test_tasks.multiply_with_sleep

[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] celery ready.
```

**Keep this terminal open** - it will show task execution logs.

---

### Step 3: Start the FastAPI Application

Open **another new terminal window** and run:

```bash
cd backend
uvicorn main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The API is now available at: http://localhost:8000

**Keep this terminal open** - it will show API request logs.

---

### Step 4: Run the Test Script

Open a **third terminal window** and run:

```bash
cd backend
python test_multiply_task.py
```

**Expected Output:**
```
============================================================
Testing Celery Background Task Processing
============================================================

Starting multiplication task (7 x 8 with 10 seconds processing)...
Task started successfully!
   Task ID: abc123-def456-789ghi-012jkl
   Status: PENDING

Monitoring task progress...
------------------------------------------------------------
   [##############################] 100% - Processing... (10/10 seconds)

Task completed successfully!
------------------------------------------------------------
   Result: 7 x 8 = 56
   Message: Successfully calculated 7 x 8 = 56
   Processing time: 10 seconds
------------------------------------------------------------

============================================================
Test completed!
============================================================
```

---

## What to Observe in Each Terminal

### Terminal 1 (Celery Worker)
You should see:
```
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Task app.tasks.test_tasks.multiply_with_sleep[task-id] received
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Task app.tasks.test_tasks.multiply_with_sleep[task-id] succeeded in 10.0s: {'status': 'completed', 'x': 7, 'y': 8, 'result': 56, ...}
```

### Terminal 2 (FastAPI)
You should see:
```
INFO:     127.0.0.1:xxxxx - "POST /api/v1/test-celery/multiply HTTP/1.1" 200 OK
INFO:     127.0.0.1:xxxxx - "GET /api/v1/test-celery/status/task-id HTTP/1.1" 200 OK
(Multiple status check requests)
```

### Terminal 3 (Test Script)
You should see:
- Task initialization
- Real-time progress bar (updates every second)
- Final calculation result

---

## Alternative Testing Methods

### Option A: Using Swagger UI (Interactive API Documentation)

1. Open your browser and go to: http://localhost:8000/docs
2. Scroll to the **"Celery Testing"** section
3. Expand `POST /api/v1/test-celery/multiply`
4. Click **"Try it out"**
5. Enter the request body:
   ```json
   {
     "x": 7,
     "y": 8,
     "sleep_seconds": 10
   }
   ```
6. Click **"Execute"**
7. Copy the `task_id` from the response
8. Expand `GET /api/v1/test-celery/status/{task_id}`
9. Click **"Try it out"**, paste the task_id, and click **"Execute"**
10. Repeat step 9 every few seconds to see progress updates
11. Continue until the state is **"SUCCESS"**

### Option B: Using curl Commands

**Start a task:**
```bash
curl -X POST "http://localhost:8000/api/v1/test-celery/multiply" \
  -H "Content-Type: application/json" \
  -d '{"x": 7, "y": 8, "sleep_seconds": 10}'
```

**Response:**
```json
{
  "task_id": "abc123-def456-789ghi-012jkl",
  "status": "Task started",
  "message": "Multiplication task is processing in the background"
}
```

**Check task status (replace `TASK_ID` with actual task ID):**
```bash
curl "http://localhost:8000/api/v1/test-celery/status/TASK_ID"
```

**Response (while processing):**
```json
{
  "task_id": "TASK_ID",
  "state": "PROGRESS",
  "info": {
    "current": 5,
    "total": 10,
    "status": "Processing... (5/10 seconds)",
    "progress_percent": 50
  }
}
```

**Response (completed):**
```json
{
  "task_id": "TASK_ID",
  "state": "SUCCESS",
  "result": {
    "status": "completed",
    "x": 7,
    "y": 8,
    "result": 56,
    "message": "Successfully calculated 7 × 8 = 56",
    "processing_time_seconds": 10
  }
}
```

### Option C: Using Python Requests

```python
import requests
import time

# Start task
response = requests.post(
    "http://localhost:8000/api/v1/test-celery/multiply",
    json={"x": 7, "y": 8, "sleep_seconds": 10}
)
task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# Poll for status
while True:
    response = requests.get(f"http://localhost:8000/api/v1/test-celery/status/{task_id}")
    data = response.json()
    state = data["state"]

    if state == "SUCCESS":
        print(f"Result: {data['result']}")
        break
    elif state == "FAILURE":
        print(f"Failed: {data['info']}")
        break
    else:
        print(f"Status: {state}")

    time.sleep(1)
```

---

## Testing Different Scenarios

Modify the parameters to test various cases:

### Quick Test (3 seconds)
```json
{
  "x": 2,
  "y": 3,
  "sleep_seconds": 3
}
```

### Medium Test (15 seconds)
```json
{
  "x": 15,
  "y": 20,
  "sleep_seconds": 15
}
```

### Long Test (30 seconds)
```json
{
  "x": 100,
  "y": 200,
  "sleep_seconds": 30
}
```

---

## Troubleshooting

### Issue: "Could not connect to the API server"
**Solution:** Make sure the FastAPI app is running on http://localhost:8000
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # macOS/Linux
```

### Issue: Task stays in PENDING state
**Solution:** The Celery worker is not running or not connected
- Check Terminal 1 (Celery worker)
- Look for "celery ready" message
- Ensure no error messages about Redis connection

### Issue: "Redis connection error"
**Solution:** Redis is not running or not accessible
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Check Redis is running on default port
netstat -ano | findstr :6379  # Windows
lsof -i :6379                  # macOS/Linux
```

### Issue: Import errors or module not found
**Solution:**
1. Make sure you're in the `backend` directory
2. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Check your Python environment is activated (if using venv/conda)

### Issue: Task fails with error
**Solution:** Check the Celery worker terminal for detailed error messages

---

## Understanding the Test Flow

1. **Task Creation (Async)**
   - Client sends POST request to `/multiply` endpoint
   - FastAPI immediately returns a task ID (non-blocking)
   - Task is queued in Redis

2. **Task Execution (Background)**
   - Celery worker picks up the task from Redis
   - Task runs in the background for `sleep_seconds` duration
   - Progress updates are stored in Redis every second

3. **Status Monitoring (Polling)**
   - Client polls `/status/{task_id}` endpoint
   - Returns current state: PENDING → PROGRESS → SUCCESS/FAILURE
   - Progress includes: current step, total steps, percentage

4. **Result Retrieval**
   - When state is SUCCESS, result is available
   - Contains calculation result and metadata

---

## Task States Explained

| State | Description |
|-------|-------------|
| `PENDING` | Task is waiting in the queue |
| `PROGRESS` | Task is currently running |
| `SUCCESS` | Task completed successfully |
| `FAILURE` | Task failed with an error |

---

## Files Involved

- **[test_multiply_task.py](test_multiply_task.py)** - Python test script with progress visualization
- **[app/tasks/test_tasks.py](app/tasks/test_tasks.py)** - Multiplication task implementation
- **[app/api/v1/test_celery.py](app/api/v1/test_celery.py)** - API endpoints for Celery testing
- **[celery_worker.py](celery_worker.py)** - Celery worker application entry point
- **[app/core/celery_app.py](app/core/celery_app.py)** - Celery application configuration

---

## Next Steps

After successfully testing the multiplication task, you can:
1. Explore the scan tasks in `app/tasks/scan_tasks.py`
2. Create your own custom Celery tasks
3. Integrate Celery tasks into your application workflow
4. Implement more complex task chains and workflows

---

## Additional Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Redis Documentation](https://redis.io/documentation)
