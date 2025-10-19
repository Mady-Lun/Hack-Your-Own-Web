# Hack My Own Web Project — Backend

> A backend-focused web scanner platform for developers to run security scans, manage scan jobs, and retrieve results via REST API.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Why this project exists](#why-this-project-exists)
4. [Architecture & Components](#architecture--components)
5. [Tech Stack](#tech-stack)
6. [Getting Started (Developer setup)](#getting-started-developer-setup)
8. [Background Tasks & Long-running Scans](#background-tasks--long-running-scans)
9. [API Endpoints](#api-endpoints)
---

## Project Overview

"Hack My Own Web" backend provides APIs and task management for scanning web applications. It is built for asynchronous, high-performance operations and focuses solely on backend responsibilities.

## Key Features

* REST API for managing scans and results.
* Asynchronous scan processing to handle long-running jobs.
* Modular vulnerability checks (SQLi, XSS, insecure headers, directory listing).
* User authentication & role-based access.
* Scan scheduling, reporting, and history storage.

## Why this project exists

To allow developers to run security scans safely and learn about web vulnerabilities without needing a frontend. It is intended for educational, development, and internal security purposes.

## Architecture & Components

* **Backend API**: FastAPI async endpoints for managing users, scans, and results.
* **Database**: PostgreSQL for storing users, scan jobs, and results.
* **Worker / Background Tasks**: Celery to execute long-running scan jobs asynchronously.
* **Cache / Broker**: Redis for task queue and caching.

## Tech Stack

* **Language**: Python 3.11+
* **Framework**: FastAPI (async backend)
* **Database**: PostgreSQL (data)
* **ORM**: SQLAlchemy (async) + Alembic (DB + migrations)
* **Task Queue**: Celery + Redis (background tasks)
* **Container**: Docker & Docker Compose (for dev and deployment)

## Getting Started (Developer setup)

### Prerequisites

* Docker & Docker Compose
* Python 3.11+

### Environment Variables (.env)
Copy the .env.example into two different files to backend root folder:
* First file: "**.env.dev**" - for development.
* Second file: "**.env.prod**" - for production.

```
# Settings
ENV=development
DEBUG=True
JWT_SECRET=changeme_supersecret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=18

# DB
DATABASE_URL=changeme
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# MAIL
MAIL_USERNAME=changeme
MAIL_PASSWORD=changeme
MAIL_FROM=changeme
MAIL_FROM_NAME="no-reply"
MAIL_PORT=587
MAIL_SERVER=changeme
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
MAIL_DEBUG=True
USE_CREDENTIALS=True

# APP
APP_NAME="Hack Your Own Web"
```

### Local Development
```bash
# Clone the Repository
git clone https://github.com/Mady-Lun/Hack-Your-Own-Web

# Navigate to your project folder
cd Hack-Your-Own-Web/backend

# Build and Start the Containers
docker-compose up --build
```
**This will start:**
* FastAPI backend (api)
* Redis (redis)
* Celery worker (instace for each worker)

## Background Tasks & Long-running Scans

* **Celery**: Handles asynchronous, long-running scan jobs.
* Scan progress and results are stored in the database for retrieval via API.

## API Endpoints
The backend API endpoints are fully documented and can be imported into Postman for testing and interaction. You can check the Postman collection at:

> **backend/API_Endpoint-HYOW.postman_collection.json**

Interactive docs: `/docs` and `/redoc`.