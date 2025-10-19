from pydantic import EmailStr
from .base import BaseResponse
from typing import Optional


class UserResponse(BaseResponse):
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr