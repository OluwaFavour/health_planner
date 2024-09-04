from datetime import datetime
from uuid import uuid4, UUID

from email_validator import validate_email, EmailNotValidError

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped, validates

from ..core.utils import generate_password_hash, verify_password
from .config import Base
from .enums import PlanType


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), index=True
    )

    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="user"
    )
    plans: Mapped[list["Plan"]] = relationship(
        "Plan", back_populates="user", lazy="selectin"
    )

    @validates("email")
    def validate_email(self, key, email):
        try:
            validate_email(email)
        except EmailNotValidError as e:
            raise ValueError(str(e))
        return email

    async def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    async def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    plan_type: Mapped[PlanType] = mapped_column()
    description: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)

    user: Mapped["User"] = relationship("User", back_populates="plans")
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="plan", lazy="selectin"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plans.id"), index=True, nullable=True
    )
    question: Mapped[str] = mapped_column()
    answer: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)

    user: Mapped["User"] = relationship("User", back_populates="questions")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="questions")
