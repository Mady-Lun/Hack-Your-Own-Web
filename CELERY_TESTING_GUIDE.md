# Celery Testing Guide with Flower Monitoring

This guide walks you through testing Celery background tasks with Flower monitoring for the Hack Your Own Web project.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Starting the Services](#starting-the-services)
- [Running the Celery Test](#running-the-celery-test)
- [Monitoring with Flower](#monitoring-with-flower)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before running the Celery tests, ensure you have:

1. **Docker and Docker Compose** installed
2. **Python 3.11+** installed (for running the test script)
3. **Required Python packages** installed:
   ```bash
   cd backend
   pip install requests
   ```

---

## Environment Configuration

### Step 1: Configure Redis Connection

The `.env` file must be configured correctly based on your deployment method:

**For Docker Deployment (recommended):**

Edit `backend/.env` and ensure the following lines are **uncommented**:

```env
# For Docker deployment: use service names (redis)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

And these lines are **commented out**:

```env
# For local development (uncomment if running without Docker):
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**For Local Development (without Docker):**

Do the opposite - use `localhost` instead of `redis`.

---

## Starting the Services

### Step 1: Navigate to Project Root

```bash
cd d:\Internship\Hack-Your-Own-Web
```

### Step 2: Start All Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- **PostgreSQL** database (port 5432)
- **Redis** broker (port 6379)
- **Backend API** (port 8000)
- **Celery Worker** (background processing)
- **Celery Beat** (scheduled tasks)
- **Flower** monitoring dashboard (port 5555)

### Step 3: Verify All Services Are Running

```bash
docker-compose ps
```

You should see all containers with status "Up":

```
NAME                 STATUS
hyow-backend         Up
hyow-celery-beat     Up
hyow-celery-worker   Up
hyow-flower          Up
hyow-postgres        Up (healthy)
hyow-redis           Up (healthy)
```

### Step 4: Wait for Services to Initialize

Give the services 5-10 seconds to fully start up and establish connections.

---

## Running the Celery Test

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Run the Test Script

```bash
python test_multiply_task.py
```

### Expected Output

You should see output like this:

```
============================================================
Testing Celery Background Task Processing
============================================================

Starting multiplication task (7 x 8 with 10 seconds processing)...
Task started successfully!
   Task ID: 8236b49e-07b5-44f7-8cdf-3213f76bb09b
   Status: started

Monitoring task progress...
------------------------------------------------------------
   [------------------------------] 0% - Starting multiplication of 7 × 8...
   [###---------------------------] 10% - Processing... (1/10 seconds)
   [######------------------------] 20% - Processing... (2/10 seconds)
   [#########---------------------] 30% - Processing... (3/10 seconds)
   [############------------------] 40% - Processing... (4/10 seconds)
   [###############---------------] 50% - Processing... (5/10 seconds)
   [##################------------] 60% - Processing... (6/10 seconds)
   [#####################---------] 70% - Processing... (7/10 seconds)
   [########################------] 80% - Processing... (8/10 seconds)
   [###########################---] 90% - Processing... (9/10 seconds)

Task completed successfully!
------------------------------------------------------------
   Result: 7 x 8 = 56
   Message: Successfully calculated 7 × 8 = 56
   Processing time: 10 seconds
------------------------------------------------------------

============================================================
Test completed!
============================================================
```

### What the Test Does

1. **Sends a task** to multiply 7 × 8 with a 10-second simulated processing time
2. **Polls the task status** every second
3. **Displays a progress bar** showing task completion percentage
4. **Shows the final result** when the task completes

---

## Monitoring with Flower

### Step 1: Open Flower Dashboard

Open your web browser and navigate to:

```
http://localhost:5555
```

### Step 2: Explore the Flower Interface

#### **Dashboard Tab**
- View real-time worker statistics
- See active tasks count
- Monitor broker connection status
- View worker uptime and performance

#### **Tasks Tab**
- See all tasks (active, successful, failed)
- Filter tasks by state
- View task details:
  - Task ID
  - Task name
  - Arguments
  - Result
  - Execution time
  - State (PENDING, PROGRESS, SUCCESS, FAILURE)

#### **Workers Tab**
- View all connected Celery workers
- See worker configuration
- Monitor worker health
- View active/processed/failed task counts per worker

#### **Broker Tab**
- Monitor Redis broker connection
- View queue statistics

#### **Monitor Tab**
- Real-time task execution monitoring
- Live task stream
- Task success/failure rates

### Step 3: View Your Test Task

1. Click on the **"Tasks"** tab
2. Look for task ID that was displayed in your test output
3. Click on the task to see detailed information:
   - Task name: `app.tasks.test_tasks.multiply_numbers`
   - Arguments: `(7, 8, 10)`
   - Result: `{"x": 7, "y": 8, "result": 56, ...}`
   - State: `SUCCESS`
   - Runtime: ~10 seconds

---

## Running Multiple Tests

You can run the test script multiple times to see multiple tasks in Flower:

```bash
# Run test 1
python test_multiply_task.py

# Wait for completion, then run test 2
python test_multiply_task.py

# And so on...
```

Each task will appear in the Flower dashboard with a unique Task ID.

---

## Understanding the Test Architecture

### Components Involved

1. **Test Script** (`test_multiply_task.py`)
   - Sends HTTP POST request to create a task
   - Polls task status endpoint
   - Displays progress

2. **Backend API** (`main.py`)
   - Receives task creation request
   - Submits task to Celery
   - Provides task status endpoint

3. **Celery Worker**
   - Picks up tasks from Redis queue
   - Executes the multiplication task
   - Updates task progress
   - Stores result in Redis

4. **Redis**
   - Acts as message broker (task queue)
   - Stores task results
   - Manages task state

5. **Flower**
   - Connects to Redis
   - Monitors all Celery activity
   - Provides web-based dashboard

### Task Flow

```
Test Script → Backend API → Redis Queue → Celery Worker → Redis Result
                                              ↓
                                           Flower
                                         (Monitoring)
```

---

## Troubleshooting

### Issue 1: "Could not connect to the API server"

**Symptoms:**
```
ERROR: Could not connect to the API server.
   Make sure the FastAPI app is running on http://localhost:8000
```

**Solutions:**
1. Check if backend is running:
   ```bash
   docker-compose ps backend
   ```
2. Check backend logs:
   ```bash
   docker logs hyow-backend
   ```
3. Restart backend:
   ```bash
   docker-compose restart backend
   ```

### Issue 2: "500 Internal Server Error"

**Symptoms:**
```
ERROR starting task: 500 Server Error: Internal Server Error
```

**Common Causes:**
- Redis connection issue
- Wrong Redis URL in `.env` file

**Solutions:**

1. **Check Redis connection from backend:**
   ```bash
   docker exec hyow-backend python -c "import redis; r = redis.Redis(host='redis', port=6379, db=0); print('PING:', r.ping())"
   ```
   Should output: `PING: True`

2. **Verify environment variables in container:**
   ```bash
   docker exec hyow-backend env | grep CELERY
   ```
   Should show:
   ```
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   ```

3. **If showing localhost instead of redis, fix .env file:**
   - Edit `backend/.env`
   - Change `redis://localhost:6379/0` to `redis://redis:6379/0`
   - Recreate containers:
     ```bash
     docker-compose up -d --force-recreate backend celery-worker flower
     ```

4. **Check backend logs for detailed error:**
   ```bash
   docker logs hyow-backend --tail 50
   ```

### Issue 3: Flower Not Accessible

**Symptoms:**
- Cannot open http://localhost:5555

**Solutions:**

1. **Check if Flower is running:**
   ```bash
   docker-compose ps flower
   ```

2. **Check Flower logs:**
   ```bash
   docker logs hyow-flower
   ```

3. **Restart Flower:**
   ```bash
   docker-compose restart flower
   ```

4. **Verify port is not in use:**
   ```bash
   netstat -ano | findstr :5555
   ```

### Issue 4: Task Stays in PENDING State

**Symptoms:**
- Task never progresses beyond "PENDING"

**Solutions:**

1. **Check if Celery worker is running:**
   ```bash
   docker-compose ps celery-worker
   ```

2. **Check worker logs:**
   ```bash
   docker logs hyow-celery-worker
   ```

3. **Restart worker:**
   ```bash
   docker-compose restart celery-worker
   ```

4. **Verify worker is connected in Flower:**
   - Open http://localhost:5555
   - Go to "Workers" tab
   - Should see at least one worker listed

### Issue 5: "Connection to Redis lost"

**Symptoms:**
```
ERROR - Connection to Redis lost: Retry (0/20) now.
CRITICAL - Retry limit exceeded while trying to reconnect to the Celery redis result store backend.
```

**Solutions:**

1. **Check if Redis is running:**
   ```bash
   docker-compose ps redis
   ```
   Status should be "Up (healthy)"

2. **Test Redis directly:**
   ```bash
   docker exec hyow-redis redis-cli ping
   ```
   Should output: `PONG`

3. **Restart Redis and dependent services:**
   ```bash
   docker-compose restart redis
   docker-compose restart backend celery-worker flower
   ```

4. **Check network connectivity:**
   ```bash
   docker network ls
   docker network inspect hyow-network
   ```

### Full Service Restart

If all else fails, perform a complete restart:

```bash
# Stop all services
docker-compose down

# Start all services fresh
docker-compose up -d

# Wait 10 seconds for initialization
timeout 10

# Run the test
cd backend
python test_multiply_task.py
```

---

## Advanced Testing

### Custom Test Parameters

You can modify `test_multiply_task.py` to test different scenarios:

```python
# Change the numbers to multiply
response = requests.post(
    f"{base_url}/multiply",
    json={
        "x": 15,        # Change this
        "y": 23,        # Change this
        "sleep_seconds": 5  # Reduce processing time
    }
)
```

### Test Multiple Concurrent Tasks

Create a script to send multiple tasks simultaneously:

```python
import requests
import concurrent.futures

base_url = "http://localhost:8000/api/v1/test-celery"

def create_task(x, y):
    response = requests.post(
        f"{base_url}/multiply",
        json={"x": x, "y": y, "sleep_seconds": 5}
    )
    return response.json()

# Send 5 tasks concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(create_task, i, i*2)
        for i in range(1, 6)
    ]

    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        print(f"Task created: {result['task_id']}")
```

Watch all 5 tasks execute in Flower!

---

## API Endpoints Reference

### Start a Multiplication Task

**Endpoint:** `POST /api/v1/test-celery/multiply`

**Request Body:**
```json
{
  "x": 7,
  "y": 8,
  "sleep_seconds": 10
}
```

**Response:**
```json
{
  "task_id": "8236b49e-07b5-44f7-8cdf-3213f76bb09b",
  "status": "started",
  "message": "Task submitted successfully"
}
```

### Get Task Status

**Endpoint:** `GET /api/v1/test-celery/status/{task_id}`

**Response (In Progress):**
```json
{
  "task_id": "8236b49e-07b5-44f7-8cdf-3213f76bb09b",
  "state": "PROGRESS",
  "info": {
    "current": 5,
    "total": 10,
    "status": "Processing... (5/10 seconds)",
    "progress_percent": 50
  }
}
```

**Response (Success):**
```json
{
  "task_id": "8236b49e-07b5-44f7-8cdf-3213f76bb09b",
  "state": "SUCCESS",
  "result": {
    "x": 7,
    "y": 8,
    "result": 56,
    "message": "Successfully calculated 7 × 8 = 56",
    "processing_time_seconds": 10
  }
}
```

---

## Next Steps

Now that you've successfully tested Celery with Flower monitoring, you can:

1. **Create your own background tasks** in `backend/app/tasks/`
2. **Monitor real security scans** using the same Flower dashboard
3. **Configure task queues** for different priority levels
4. **Set up scheduled tasks** using Celery Beat
5. **Implement task retry logic** for failed tasks
6. **Add task result persistence** to the database

For more information on Celery configuration, see the official documentation:
- Celery: https://docs.celeryproject.org/
- Flower: https://flower.readthedocs.io/

---

## Summary

You've learned how to:
- Configure Celery with Redis in Docker
- Start all required services
- Run background task tests
- Monitor tasks in real-time with Flower
- Troubleshoot common issues

The Celery + Flower setup is now ready for production security scanning tasks!
