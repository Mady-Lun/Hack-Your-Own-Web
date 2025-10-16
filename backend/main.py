import sys
from pathlib import Path
# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from app.api.v1.auth import auth_router
from app.api.v1.scan import scan_router
from app.api.v1.test_celery import router as test_celery_router
from app.core.db import async_engine
from sqlalchemy import text
# from fastapi.middleware.cors import CORSMiddleware


version = "v1"
app = FastAPI(
    title="Hack Your Own Web API",
    description="Security scanning platform API with OWASP ZAP integration",
    version=version,
)

# origins = [
#     "http://localhost:8000",  # your frontend
#     "http://127.0.0.1:8000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,  # important for cookies
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Include routers
app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=["Authentication"])
app.include_router(scan_router, prefix=f"/api/{version}/scans", tags=["Security Scans"])
app.include_router(test_celery_router, prefix=f"/api/{version}/test-celery", tags=["Celery Testing"])


@app.get("/")
async def root():
    return {
        "message": "Hack Your Own Web API",
        "version": version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")