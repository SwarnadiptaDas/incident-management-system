from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models import SeverityEnum, StateEnum

class SignalCreate(BaseModel):
    component_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: str
    severity: SeverityEnum

class RCASubmit(BaseModel):
    rca_category: str
    fix_applied: str
    prevention_steps: str

class WorkItemResponse(BaseModel):
    id: int
    component_id: str
    state: StateEnum
    severity: SeverityEnum
    start_time: datetime
    end_time: Optional[datetime] = None
    mttr_minutes: Optional[float] = None
    signal_count: int
    rca_category: Optional[str] = None
    fix_applied: Optional[str] = None
    prevention_steps: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SignalResponse(BaseModel):
    component_id: str
    timestamp: datetime
    error: str
    severity: str
    work_item_id: int

    class Config:
        from_attributes = True
