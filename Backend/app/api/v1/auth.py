from fastapi import APIRouter, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_session
from ...schemas.user import UserSignUp
from ...crud.user import register_user
from ...schemas.user import UserModel


router = APIRouter()


@router.get("/ping")
async def ping():
    return {
        "message": "pong"
    }

@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up(data: UserSignUp, session: AsyncSession = Depends(get_session)):
    return await register_user(data, session)
    


auth_router = router
# from fastapi import FastAPI, Header
# from typing import Optional
# from pydantic import BaseModel

# app = FastAPI()

# @app.get("/")
# async def read_root():
#     return {
#         "message": "Hello, World!"
#     }

# # Path Parameter
# @app.get("/greet/{name}")
# async def greet(name: str) -> dict:
#     return {
#         "message": f"Hello, {name}!"
#     }

# # Query Parameter
# @app.get("/greet")
# async def greet(name: Optional[str] = "User", age: int = 0) -> dict:
#     return {
#         "message": f"Hello, {name}! You are {age} years old."
#     }

# class BookCreateModel(BaseModel):
#     title: str
#     author: str

# @app.post("/create_book")
# async def create_book(book_data: BookCreateModel):
#     return {
#         "title": book_data.title,
#         "author": book_data.author
#     }
    
# @app.get("/get_headers", status_code = 200)
# async def get_headers(
#     accept: str = Header(None),
#     content_type: str = Header(None)
# ):
#     request_headers = {}
#     request_headers["Accept"] = accept
#     request_headers["Content-Type"] = content_type
#     return request_headers