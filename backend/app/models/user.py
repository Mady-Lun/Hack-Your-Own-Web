from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.scan import Scan


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: int = Field(default=None, primary_key=True)
    token: str = Field(index=True, nullable=False, unique=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    expires_at: datetime = Field(nullable=False)
    user: "User" = Relationship(back_populates="refresh_tokens")


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
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    refresh_tokens: List[RefreshToken] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
    scans: List["Scan"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )


def __repr__(self):
    return f"<User {self.email}>"
