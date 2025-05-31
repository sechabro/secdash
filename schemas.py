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
    count: int  # total attempts on this server at time of analysis
    risk: str | None = None
    status: str | None = None
    reco_action: str | None = None
    country: str | None = None
    first_seen: str | None = None  # first attempt against server
    last_seen: str | None = None  # last attempt against server


class FailedLoginIPBan(SQLModel):
    ip: str
    status: str


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
    user: float
    nice: float
    system: float
    iowait: float
    steal: float
    idle: float

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
