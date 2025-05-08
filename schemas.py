from sqlmodel import SQLModel, Field, JSON, Column
from pydantic import EmailStr
from pydantic.types import StringConstraints
from typing import Optional, Annotated
from dataclasses import dataclass

# ----------- VISITOR-RELATED CLASSES ------------


class Visitor(SQLModel, table=True):
    __tablename__ = "visitors"  # optional, but I want to override default 'visitor'

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    acct_created: str  # or datetime if you're storing as an actual datetime
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

# ----------- STREAM-RELATED CLASSES ------------


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
