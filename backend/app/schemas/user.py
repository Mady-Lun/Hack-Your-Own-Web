from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class UserSignUpRequest(BaseModel):
    first_name: str = Field(..., description="The first name of the user")
    last_name: Optional[str] = Field(None, description="The last name of the user")
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., min_length=6, description="The password for the user account")


class UserVerifyRequest(BaseModel):
    verification_code: str = Field(
        ...,
        description="The verification code sent to the user's email",
        pattern=r'^\d{6}$'  # Ensures exactly 6 digits
    )


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., description="The password for the user account")


class RequestUserPasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")


class UserPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6, description="The new password for the user account")
