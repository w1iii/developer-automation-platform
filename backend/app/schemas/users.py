from datetime import datetime

from pydantic import BaseModel, Field

from .auth import Role


class UserResponse(BaseModel):
    id: int
    username: str
    role: Role = Role.USER
    created_at: datetime

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: Role = Role.USER


class UpdateUserRequest(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    role: Role | None = None