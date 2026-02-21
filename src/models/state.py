from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from models.intent import IntentType
from models.plan import Plan, PlanVersion

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_plan: Optional[Plan]
    plan_history: list[PlanVersion]
    token_count: int
    last_intent: Optional[IntentType]
    conversation_summary: Optional[str]
    user_preferences: dict
    needs_clarification: bool

