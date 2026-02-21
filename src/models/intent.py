from enum import Enum
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    create_plan = "create_plan"
    edit_plan = "edit_plan"
    clarify = "clarify"
    summarize = "summarize"
    chat = "chat"


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float
    reasoning: str