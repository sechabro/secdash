from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Optional

from pydantic import EmailStr
from pydantic.types import StringConstraints
from sqlalchemy import DateTime
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

# ----------- VISITOR-RELATED CLASSES ------------


class Visitor(SQLModel, table=True):
    __tablename__ = "visitors"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    acct_created: str
    ip: str
    port: str
    device_info: str
    browser_info: str
    is_bot: bool
    geo_info: str
    ipdb: dict = Field(sa_column=Column(JSON))
    last_active: Optional[str] = None
    time_idle: int = 0  # measured in seconds
    is_active: bool = False


@dataclass(slots=True, order=False)
class VisitorInMem():
    visitor_id: int
    username: str
    acct_created: str
    ip: str
    port: str
    device_info: str
    browser_info: str
    is_bot: bool
    geo_info: str
    ipdb: bool  # .getting "isTor" value only
    last_active: str
    time_idle: int
    is_active: bool

# -------------- VISITOR CASE-RELATED CLASSES ---------------


class VisitorsFlagged(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    visitor_id: Optional[int] = Field(default=None, foreign_key="visitors.id")
    risk_level: str  # ai risk assessment. e.g. "low", "medium", "high"
    justification: str  # ai explanation
    recommended_action: str  # ai suggestion
    created_at: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
        sa_column=Column(DateTime(timezone=True))
    )
    visitor_info: Optional[Visitor] = Relationship()

# ----------- SYSTEM PERFORMANCE-RELATED CLASSES ------------


class IOStatLine(SQLModel, table=True):
    __tablename__ = "iostats"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str
    time: str
    avg_io_size: float
    io_ops_sec: int
    throughput: float
    cpu_user_pct: float
    cpu_system_pct: float
    cpu_idle_pct: float
    load_avg_1m: float


@dataclass(slots=True, order=False)
class IoStatLineInMem:
    date: str
    time: str
    kbt: float
    tps: int
    throughput_mbs: float
    cpu_user_pct: float
    cpu_system_pct: float
    cpu_idle_pct: float
    load_avg_1m: float

# ----------- USER-RELATED CLASSES ------------


class User(SQLModel):
    email: EmailStr
    password: Annotated[str, Field(
        min_length=8, max_length=1000)] | None = None


class UserReg(User):
    username: Annotated[str, Field(min_length=8, max_length=20)]


class UserInDb(UserReg, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    regdate: str

# ------------- TOKEN-RELATED CLASSES -------------


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: str | None = None
