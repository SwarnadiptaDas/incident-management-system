import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class StateEnum(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class SeverityEnum(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

class WorkItem(Base):
    __tablename__ = "work_items"

    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(String, index=True, nullable=False)
    state = Column(Enum(StateEnum), default=StateEnum.OPEN, nullable=False)
    severity = Column(Enum(SeverityEnum), nullable=False)
    
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    mttr_minutes = Column(Float, nullable=True)
    signal_count = Column(Integer, default=1, nullable=False)
    
    rca_category = Column(String, nullable=True)
    fix_applied = Column(Text, nullable=True)
    prevention_steps = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
