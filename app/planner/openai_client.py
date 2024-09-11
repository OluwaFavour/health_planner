from typing import Any

from openai import OpenAI, LengthFinishReasonError, ContentFilterFinishReasonError

from ..core.config import get_settings

from .schemas import DecisionResponse, PlanType, MealPlan, WorkoutPlan


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        organization: str,
        project: str,
        model: str,
        max_tokens: int = 300,
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            organization=organization,
            project=project,
        )
        self.model = model
        self.max_tokens = max_tokens

    def get_plan_choice(self, text: str) -> PlanType:
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Get the plan choice from this text. It can only be one of the following: 'meal', 'workout', 'both', or 'None'.",
                    },
                    {"role": "user", "content": text},
                ],
                response_format=DecisionResponse,
            )
            response = completion.choices[0].message
            if response.refusal:
                return response.refusal
            decision: DecisionResponse = response.parsed
            return decision.plan_type
        except Exception as e:
            if type(e) == LengthFinishReasonError:
                raise ValueError(
                    {
                        "error": e,
                        "message": "Too many tokens have been used. Please try again later.",
                    }
                )
            elif type(e) == ContentFilterFinishReasonError:
                raise ValueError(
                    {
                        "error": e,
                        "message": "Content filter has blocked this request.",
                    }
                )
            else:
                raise ValueError({"error": e, "message": "An error occurred."})

    def generate_meal_plan(self, answers: dict[str, str]) -> str:
        try:
            answers_str = "\n".join(
                [f"{key}: {value}" for key, value in answers.items()]
            )
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate a meal plan based on the user's answers. The user has provided the following answers to the questions: {answers.keys()}. For example, from the answers the user has a budget of {answers['What is your weekly or monthly budget for groceries and meals? Reply with an estimate if unsure.']} NGN.",
                    },
                    {"role": "user", "content": answers_str},
                ],
                response_format=MealPlan,
            )
            plan: MealPlan | None = completion.choices[0].message.parsed
            if not plan:
                return "Could not generate a meal plan based on the answers provided."
            response = f"Here is a meal plan based on your answers:\n\n"
            response += f"Budget: {plan.budget}\n\n"
            for day in plan.days:
                response += f"{day.day}\n"
                for meal in day.meals:
                    response += f"\n{meal.meal_type.capitalize()}\n"
                    response += f"Recipe: {meal.recipe}\n"
                    response += f"Ingredients: {', '.join(meal.ingredients)}\n"
                    response += f"Instructions: {meal.instructions}\n"
                for snack in day.snacks:
                    response += f"\nSnack\n"
                    response += f"Recipe: {snack.recipe}\n"
                    response += f"Ingredients: {', '.join(snack.ingredients)}\n"
                    response += f"Instructions: {snack.instructions}\n"
            return response
        except Exception as e:
            if type(e) == LengthFinishReasonError:
                raise ValueError(
                    {
                        "error": e,
                        "message": "Too many tokens have been used. Please try again later.",
                    }
                )
            elif type(e) == ContentFilterFinishReasonError:
                raise ValueError(
                    {
                        "error": e,
                        "message": "Content filter has blocked this request.",
                    }
                )
            else:
                raise ValueError({"error": e, "message": "An error occurred."})

    def generate_workout_plan(self, answers: dict[str, str]) -> str:
        try:
            answers_str = "\n".join(
                [f"{key}: {value}" for key, value in answers.items()]
            )
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate a workout plan based on the user's answers. The user has provided the following answers to the questions: {answers.keys()}. For example, from the answers the user can do {answers['How many push-ups can you perform in one set?']} in one set.",
                    },
                    {"role": "user", "content": answers_str},
                ],
                response_format=WorkoutPlan,
            )
            plan: WorkoutPlan | None = completion.choices[0].message.parsed
            if not plan:
                return (
                    "Could not generate a workout plan based on the answers provided."
                )
            response = f"Here is a workout plan based on your answers:\n\n"
            response += f"Goals: {', '.join(plan.goals)}\n\n"
            for day in plan.days:
                response += f"{day.day}\n"
                for item in day.routine:
                    response += f"\n{item.exercise}\n"
                    response += f"Sets: {item.sets}\n"
                    response += f"Reps per set: {item.reps_per_set}\n"
                    if item.instructions:
                        response += f"Instructions: {item.instructions}\n"
            return response
        except Exception as e:
            if type(e) == LengthFinishReasonError:
                raise ValueError(
                    {
                        "error": e,
                        "message": "Too many tokens have been used. Please try again later.",
                    }
                )
            elif type(e) == ContentFilterFinishReasonError:
                raise ValueError(
                    {
                        "error": e,
                        "message": "Content filter has blocked this request.",
                    }
                )
            else:
                raise ValueError({"error": e, "message": "An error occurred."})


def get_openai_client() -> OpenAIClient:
    settings = get_settings()
    return OpenAIClient(
        api_key=settings.openai_key,
        organization=settings.openai_organization_id,
        project=settings.openai_project_id,
        model=settings.openai_model,
        max_tokens=settings.openai_max_tokens,
    )
