from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, Field

from ..planner.schemas import Plan


class UserBase(BaseModel):
    username: Annotated[
        str, Field(max_length=20, min_length=3, examples=["johndoe123"])
    ]
    email: EmailStr

    @field_validator("username", mode="before")
    @classmethod
    def username_validator(cls, value: str):
        if not value.isalnum():
            raise ValueError("Username must contain only alphanumeric characters")
        return value


class UserCreate(UserBase):
    password: Annotated[
        str, Field(max_length=100, min_length=8, examples=["Password123)"])
    ]

    @field_validator("password", mode="before")
    @classmethod
    def password_validator(cls, value: str):
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char in "!@#$%^&*()-_+=" for char in value):
            raise ValueError("Password must contain at least one special character")
        if " " in value:
            raise ValueError("Password must not contain spaces")
        return value


class User(UserBase):
    model_config: ConfigDict = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

    plans: list[Plan] = []
