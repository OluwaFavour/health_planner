from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, Request

from .crud import authenticate_user, get_user_by_id
from .forms import LoginForm

from ..core.config import get_settings
from ..db.config import get_async_session
from ..db.models import User


async def authenticate(
    form: Annotated[LoginForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User | None:
    return await authenticate_user(session, form.email, form.password)


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_async_session)], request: Request
) -> User | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return await get_user_by_id(session, user_id)


async def get_current_active_user(
    current_user: Annotated[User | None, Depends(get_current_user)],
) -> User | None:
    if current_user is None or not current_user.is_active:
        return None
    return current_user
