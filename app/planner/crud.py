from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.enums import PlanType
from ..db.models import Plan, Question


async def create_plan(
    async_session: AsyncSession, user_id: UUID, description: str, plan_type: PlanType
) -> Plan:
    plan = Plan(user_id=user_id, description=description, plan_type=plan_type)
    async_session.add(plan)
    await async_session.commit()
    await async_session.refresh(plan)
    return plan


async def get_plan(async_session: AsyncSession, plan_id: UUID) -> Plan | None:
    result = await async_session.execute(select(Plan).filter_by(id=plan_id))
    return result.scalar_one_or_none()


async def delete_plan(async_session: AsyncSession, plan_id: UUID) -> None:
    await async_session.execute(delete(Plan).filter_by(id=plan_id))
    await async_session.commit()


async def get_plans_by_user_id(
    async_session: AsyncSession, user_id: UUID
) -> list[Plan]:
    result = await async_session.execute(select(Plan).filter_by(user_id=user_id))
    return result.scalars().all()


async def delete_plans_by_user_id(async_session: AsyncSession, user_id: UUID) -> None:
    await async_session.execute(delete(Plan).filter_by(user_id=user_id))
    await async_session.commit()


async def create_question(
    async_session: AsyncSession, user_id: UUID, question: str, answer: str
) -> Question:
    question = Question(user_id=user_id, question=question, answer=answer)
    async_session.add(question)
    await async_session.commit()
    await async_session.refresh(question)
    return question


async def get_question(
    async_session: AsyncSession, question_id: UUID
) -> Question | None:
    result = await async_session.execute(select(Question).filter_by(id=question_id))
    return result.scalar_one_or_none()


async def get_questions_by_plan_id(
    async_session: AsyncSession, plan_id: UUID
) -> list[Question]:
    result = await async_session.execute(select(Question).filter_by(plan_id=plan_id))
    return result.scalars().all()


async def delete_question(async_session: AsyncSession, question_id: UUID) -> None:
    await async_session.execute(delete(Question).filter_by(id=question_id))
    await async_session.commit()


async def delete_questions_by_plan_id(
    async_session: AsyncSession, plan_id: UUID
) -> None:
    await async_session.execute(delete(Question).filter_by(plan_id=plan_id))
    await async_session.commit()
