from typing import Annotated

from fastapi import APIRouter, Depends, Request, status, Response
from fastapi.responses import JSONResponse

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import create_user

from ..db.config import get_async_session
from ..db.models import User as UserModel
from .dependencies import authenticate, get_current_active_user
from .forms import SignupForm
from .schemas import User as UserSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    summary="Create a new user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Username already exists",
            "content": {
                "application/json": {"example": {"detail": "Username already exists"}}
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Email already exists",
            "content": {
                "application/json": {"example": {"detail": "Email already exists"}}
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Invalid input",
            "content": {
                "application/json": {
                    "example": {"detail": "Password must contain at least one digit"}
                }
            },
        },
    },
)
async def signup(
    async_session: Annotated[AsyncSession, Depends(get_async_session)],
    form: Annotated[SignupForm, Depends()],
):
    try:
        user = await create_user(async_session, **form.model_dump())
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(e)}
        )
    except IntegrityError as e:
        if "Username" in str(e):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Username already exists"},
            )
        if "Email" in str(e):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Email already exists"},
            )

    return user


@router.post(
    "/login",
    summary="Login to the application",
    status_code=status.HTTP_200_OK,
    response_model=UserSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {"example": {"message": "Invalid credentials"}}
            },
        }
    },
)
async def login(
    user: Annotated[UserModel | None, Depends(authenticate)],
    request: Request,
):
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid credentials"},
        )

    # Create a new session for the user
    request.session.update({"user_id": str(user.id)})

    return user


@router.post(
    "/logout",
    summary="Logout from the application",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {"application/json": {"example": {"message": "Unauthorized"}}},
        }
    },
)
async def logout(
    request: Request,
    user: Annotated[UserModel | None, Depends(get_current_active_user)],
):
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Unauthorized"},
        )

    # Remove the session for the user
    request.session.pop("user_id")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
