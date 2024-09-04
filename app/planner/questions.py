import json


def load_questions(plan_type: str) -> list[dict[str, str]]:
    with open("app/planner/questions.json", "r") as file:
        questions = json.load(file)
    return [q for q in questions if q["plan_type"] == plan_type]
