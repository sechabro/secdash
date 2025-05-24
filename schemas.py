import enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, List, Optional

from pydantic import EmailStr
from sqlalchemy import JSON, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, Relationship, SQLModel

# ------- ENUMERATED VALUES FOR DB-LEVEL CONSTRAINTS --------


class RiskLevel(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    orange = "orange"
    red = "red"
    black = "black"


class ActionType(str, enum.Enum):
    none = "none"
    flagged = "flagged"
    suspend = "suspend"
    ban = "ban"
    autoban = "autobanned"
    
class CurrentStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    banned = "banned"

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
# DRAGON [2025-05-19]: Use RiskLevel and *possibly* ActionType enums.
# Constrain risk-level str to RiskLevel class. Replace `justificaton`
# column with `analysis`, for consistency. Add `action` column to display
# the action taken against the case.


class VisitorsFlaggedSummary(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    visitor_id: Optional[int] = Field(default=None, foreign_key="visitors.id")
    risk_level: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
        sa_column=Column(DateTime(timezone=True))
    )


class VisitorsFlagged(VisitorsFlaggedSummary, table=True):
    justification: str  # ai explanation
    recommended_action: str  # ai suggestion
    visitor_info: Optional[Visitor] = Relationship()

# ------------ BOT LOGIN ATTEMPT-RELATED CLASSES ------------


class FailedLoginRA(SQLModel):
    analysis: Optional[str] = None
    risk: Optional[RiskLevel] = Field(
        default=None,
        sa_column=Column(SAEnum(RiskLevel, name="risklevel_enum"))
    )
    action: ActionType = Field(
        default=ActionType.none,
        sa_column=Column(SAEnum(ActionType, name="actiontype_enum"))
    )

class FailedLoginIntel(FailedLoginRA, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ip_address: str

    server_attempts: Optional[List[dict]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )

    count: int = 0
    first_seen: datetime
    last_seen: datetime

    ipdb: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    status: CurrentStatus = Field(
        default=CurrentStatus.active,
        sa_column=Column(SAEnum(CurrentStatus, name="currentstatus_enum"))
    )
    status_change_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)) 
    )

@dataclass(slots=True, order=False)
class FailedLoginInMem:
    ip: str  # ip address in question
    score: int  # IPDB Abuse Confidence Score
    is_tor: bool  # IPDB isTor value
    total_reports: int  # IPDB report tally
    first_seen: str  # first attempt against server
    last_seen: str  # last attempt against server
    count: int  # total attempts on this server at time of analysis


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
