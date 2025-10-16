"""
Test script to demonstrate Celery background task processing
with the multiplication task.

Usage:
1. Make sure Redis is running
2. Start the Celery worker: celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
3. Start the FastAPI app: uvicorn main:app --reload
4. Run this script: python test_multiply_task.py
"""
import requests
import time
import json


def test_multiplication_task():
    """Test the multiplication background task with progress tracking"""

    base_url = "http://localhost:8000/api/v1/test-celery"

    print("=" * 60)
    print("Testing Celery Background Task Processing")
    print("=" * 60)
    print()

    # Step 1: Start the task
    print("Starting multiplication task (7 x 8 with 10 seconds processing)...")
    try:
        response = requests.post(
            f"{base_url}/multiply",
            json={
                "x": 7,
                "y": 8,
                "sleep_seconds": 10
            }
        )
        response.raise_for_status()
        task_data = response.json()

        task_id = task_data["task_id"]
        print(f"Task started successfully!")
        print(f"   Task ID: {task_id}")
        print(f"   Status: {task_data['status']}")
        print()

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API server.")
        print("   Make sure the FastAPI app is running on http://localhost:8000")
        return
    except Exception as e:
        print(f"ERROR starting task: {e}")
        return

    # Step 2: Monitor task progress
    print("Monitoring task progress...")
    print("-" * 60)

    while True:
        try:
            response = requests.get(f"{base_url}/status/{task_id}")
            response.raise_for_status()
            status_data = response.json()

            state = status_data["state"]

            if state == "PENDING":
                print("Task is pending (waiting in queue)...")

            elif state == "PROGRESS":
                info = status_data.get("info", {})
                current = info.get("current", 0)
                total = info.get("total", 0)
                status_msg = info.get("status", "Processing...")
                progress = info.get("progress_percent", 0)

                # Create progress bar
                bar_length = 30
                filled = int(bar_length * progress / 100)
                bar = "#" * filled + "-" * (bar_length - filled)

                print(f"\r   [{bar}] {progress}% - {status_msg}", end="", flush=True)

            elif state == "SUCCESS":
                print("\n")
                print("Task completed successfully!")
                result = status_data.get("result", {})
                print("-" * 60)
                print(f"   Result: {result.get('x')} x {result.get('y')} = {result.get('result')}")
                print(f"   Message: {result.get('message')}")
                print(f"   Processing time: {result.get('processing_time_seconds')} seconds")
                print("-" * 60)
                break

            elif state == "FAILURE":
                print("\n")
                print("Task failed!")
                info = status_data.get("info", {})
                print(f"   Error: {info}")
                break

            else:
                print(f"   Unknown state: {state}")

            time.sleep(1)

        except Exception as e:
            print(f"\nERROR checking status: {e}")
            break

    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_multiplication_task()
