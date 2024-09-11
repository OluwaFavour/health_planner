from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..db.models import PlanType


class PlanBase(BaseModel):
    plan_type: PlanType
    description: str


class Plan(PlanBase):
    model_config: ConfigDict = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    questions: list["Question"] = []


class QuestionBase(BaseModel):
    question: str
    answer: str


class Question(QuestionBase):
    model_config: ConfigDict = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    plan_id: UUID | None = None
    created_at: datetime


class MealPlanItem(BaseModel):
    meal_type: str
    recipe: str
    ingredients: list[str]
    instructions: str


class DailyMealPlan(BaseModel):
    day: str
    meals: list[MealPlanItem]
    snacks: list[MealPlanItem]


class MealPlan(BaseModel):
    budget: str
    days: list[DailyMealPlan]


class ExerciseItem(BaseModel):
    exercise: str
    sets: int
    reps_per_set: int
    instructions: str | None = None  # Instructions are optional


class DurationExerciseItem(BaseModel):
    exercise: str
    duration: str
    instructions: str | None = None  # Instructions are optional


class DailyWorkoutPlan(BaseModel):
    day: str
    routine: list[dict[str, str]]


class WorkoutPlan(BaseModel):
    goals: list[str]
    days: list[DailyWorkoutPlan]


class CombinedPlan(BaseModel):
    meal_plan: MealPlan
    workout_plan: WorkoutPlan


class DecisionResponse(BaseModel):
    plan_type: PlanType | None
