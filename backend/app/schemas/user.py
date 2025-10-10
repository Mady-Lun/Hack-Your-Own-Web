from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class UserModel(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserSignUp(BaseModel):
    first_name: str = Field(..., description="The first name of the user")
    last_name: Optional[str] = Field(None, description="The last name of the user")
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., min_length=6, description="The password for the user account")


class UserVerify(BaseModel):
    verification_code: str = Field(
        ...,
        description="The verification code sent to the user's email",
        pattern=r'^\d{6}$'  # Ensures exactly 6 digits
    )


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., description="The password for the user account")


class UserPasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")


class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, description="The new password for the user account")