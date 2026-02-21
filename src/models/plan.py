from enum import Enum
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class StepStatus(str, Enum):
    pending = "pending"
    done = "done"


class PlanStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    order: int
    title: str
    description: str
    status: StepStatus = StepStatus.pending

class Plan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    steps: list[PlanStep] = []
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class PlanVersion(BaseModel):
    version_number: int
    plan: Plan
    timestamp: datetime = Field(default_factory=datetime.now)
    change_summary: str

class DiffResult(BaseModel):
    added: list[PlanStep] = []
    removed: list[PlanStep] = []
    modified: list[PlanStep] = []
    change_summary: str = ""





