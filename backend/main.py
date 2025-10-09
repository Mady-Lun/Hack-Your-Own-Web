import sys
from pathlib import Path
# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from app.api.v1.auth import auth_router
from app.core.db import async_engine
from sqlalchemy import text


version = "v1"
app = FastAPI(
    version=version,
)

app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=["auth"])


@app.on_event("startup")
async def startup_event():
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")