from fastapi import APIRouter, status, Depends, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_session
from app.schemas.user import UserSignUpRequest, UserVerifyRequest, UserLoginRequest, UserPasswordResetRequest, RequestUserPasswordResetRequest
from ...responses.user import UserResponse
from ...crud.user import sign_up_crud, verify_email_crud, login_crud, reset_password_request_crud, reset_password_verify_crud, reset_password_crud, logout_crud, resend_verification_code_crud, resend_reset_password_request_crud
from ...middleware.auth_middleware import get_current_user, verify_verification


router = APIRouter()


@router.get("/ping")
async def ping():
    return {
        "message": "pong"
    }

@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up(data: UserSignUpRequest, response: Response, session: AsyncSession = Depends(get_session)):
    return await sign_up_crud(data, response, session)
    

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_email(response: Response, data: UserVerifyRequest, user_cookie = Depends(verify_verification()), session: AsyncSession = Depends(get_session)):
    return await verify_email_crud(response, data, user_cookie, session)


@router.post("/resend-verification-code", status_code=status.HTTP_200_OK)
async def resend_verification_code(response: Response, user_cookie = Depends(verify_verification()), session: AsyncSession = Depends(get_session)):
    return await resend_verification_code_crud(response, user_cookie, session)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(data: UserLoginRequest, response: Response,session: AsyncSession = Depends(get_session)):
    return await login_crud(data, response, session)


@router.post("/reset-password-request", status_code=status.HTTP_200_OK)
async def reset_password_request(data: RequestUserPasswordResetRequest, response: Response, session: AsyncSession = Depends(get_session)):
    return await reset_password_request_crud(data, response, session)


@router.post("/resend-reset-password-request", status_code=status.HTTP_200_OK)
async def resend_password_reset_request(response: Response, user_cookie = Depends(verify_verification()), session: AsyncSession = Depends(get_session)):
    return await resend_reset_password_request_crud(response, user_cookie, session)


@router.post("/reset-password-verify", status_code=status.HTTP_200_OK)
async def reset_password_verify(data: UserVerifyRequest, response: Response, user_cookie = Depends(verify_verification()), session: AsyncSession = Depends(get_session)):
    return await reset_password_verify_crud(data, response, user_cookie, session)


@router.patch("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: UserPasswordResetRequest, response: Response, user_cookie=Depends(verify_verification("resetPasswordVerificationToken")), session: AsyncSession = Depends(get_session)):
    return await reset_password_crud(data, response, user_cookie, session)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response, user_cookie=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await logout_crud(response, user_cookie, session)


@router.get("/profile", status_code=status.HTTP_200_OK)
def get_profile(user = Depends(get_current_user)):
    return user


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