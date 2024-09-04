from enum import Enum


class PlanType(Enum):
    MEAL = "meal"
    WORKOUT = "workout"
    BOTH = "both"


class PlanStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    DELETED = "deleted"
