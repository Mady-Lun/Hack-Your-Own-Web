from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class UserSignUp(BaseModel):
    first_name: str = Field(..., description="The first name of the user")
    last_name: Optional[str] = Field(None, description="The last name of the user")
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., min_length=6, description="The password for the user account")

class UserModel(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    is_verified: bool
    created_at: datetime
    updated_at: datetime