from typing import Annotated

from fastapi import Form

from pydantic import EmailStr

from .schemas import UserCreate


class LoginForm:
    def __init__(
        self,
        email: Annotated[EmailStr, Form(title="Email", description="Your email")],
        password: Annotated[str, Form(title="Password", description="Your password")],
    ):
        self.email = email
        self.password = password

    def model_dump(self):
        return {
            "email": self.email,
            "password": self.password,
        }


class SignupForm:
    def __init__(
        self,
        username: Annotated[
            str,
            Form(title="Username", description="Your username", example="johndoe123"),
        ],
        email: Annotated[EmailStr, Form(title="Email", description="Your email")],
        password: Annotated[
            str,
            Form(title="Password", description="Your password", example="Password123)"),
        ],
    ):
        self.username = username
        self.email = email
        self.password = password

    def model_dump(self):
        user = UserCreate(
            username=self.username,
            email=self.email,
            password=self.password,
        )
        return {
            "username": user.username,
            "email": user.email,
            "password": user.password,
        }
