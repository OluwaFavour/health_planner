from typing import Annotated

from fastapi import Form

from ..db.enums import PlanType


class PlanCreateForm:
    def __init__(
        self,
        plan_type: Annotated[PlanType, Form(title="Plan Type")],
        description: Annotated[str, Form(title="Description")],
    ):
        self.plan_type = plan_type
        self.description = description

    def model_dump(self):
        return {
            "plan_type": self.plan_type,
            "description": self.description,
        }
