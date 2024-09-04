from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.models import User


async def create_user(
    session: AsyncSession, username: str, email: str, password: str
) -> User:
    if await get_user_by_username(session, username):
        raise IntegrityError(None, None, ValueError("Username already exists"))
    if await get_user_by_email(session, email):
        raise IntegrityError(None, None, ValueError("Email already exists"))
    user = User(username=username, email=email)
    await user.set_password(password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None:
        return None
    if not await user.check_password(password):
        return None
    return user
