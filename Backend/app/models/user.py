from sqlmodel import SQLModel, Field
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(default=None, primary_key=True)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=True)
    email: str = Field(index=True, nullable=False)
    password_hash: str = Field(exclude=True, nullable=False)
    is_verified: bool = Field(default=False)
    verification_code: str = Field(default=None, nullable=True)
    verification_code_expires_at: datetime = Field(default=None, nullable=True)
    reset_code: str = Field(default=None, nullable=True)
    reset_code_expires_at: datetime = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


def __repr__(self):
    return f"<User {self.email}>"
