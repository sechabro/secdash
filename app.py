from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from utils import established_connections, visitor_info, host_info_async, ps_stream, io_stream, password_hasher, password_verify
from datetime import timedelta, datetime, timezone
from fastapi.concurrency import run_in_threadpool
import jwt
from jwt.exceptions import InvalidTokenError
import os
import base64
from sqlmodel import SQLModel
import schemas
import logging
import crud
from database import engine, database_check, get_session
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")
SessionDep = Annotated[AsyncSession, Depends(get_session)]
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


@app.on_event("startup")
async def on_startup():
    if database_check():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


@app.get("/", response_class=HTMLResponse, response_model=None)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/login", response_class=JSONResponse, response_model=None)
async def login(request: Request, user: schemas.User, session: SessionDep) -> schemas.Token:
    oauth2_form = OAuth2PasswordRequestForm(
        username=user.email, password=user.password)
    return await token(form_data=oauth2_form, session=session)


@app.post("/register", response_class=HTMLResponse, response_model=schemas.User)
async def register(request: Request, user: schemas.UserReg, session: SessionDep):
    db_user = await crud.get_user_by_email(session, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    pswd_hash_salt = await password_hasher(password=user.password)
    user.password = pswd_hash_salt

    reg_user = await crud.register_user(session=session, user=user)

    return templates.TemplateResponse("registered.html", {"request": request, "user": reg_user})


@app.get("/dashboard", response_class=HTMLResponse, response_model=None)
async def dashboard(request: Request, session: SessionDep):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/visitor")
async def visitor(request: Request, session: SessionDep) -> dict:
    return await visitor_info(request=request, session=session)


@app.get("/connections")
async def connections() -> list:
    return await established_connections()


@app.get("/host")
async def host_status() -> dict:
    return await host_info_async()


@app.get("/iostat-stream")
async def iostat_stream() -> dict:
    return StreamingResponse(io_stream(script="./scripts/iostat_logger.sh"), media_type="text/event-stream")


@app.get("/process-stream")
async def process_stream() -> dict:
    return StreamingResponse(ps_stream(script="./scripts/ps_logger.sh"), media_type="text/event-stream")


##### OAUTH2 #######################################################################################
########## LOGIN ###################################################################################
############## FLOW ################################################################################

EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECD', default=None)


@app.post("/token")
async def token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> schemas.Token:
    user = await authenticate_user(
        session=session, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires)
    return schemas.Token(access_token=access_token, token_type="bearer")


async def authenticate_user(session: SessionDep, email: str, password: str):
    user = await crud.get_user_by_email(session=session, email=email)
    if not user:
        return False
    if not await password_verify(password=password, hashed=user.password):
        return False
    return user


async def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})

    encoded_jwt = await run_in_threadpool(
        func=jwt.encode, payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(session=SessionDep, email=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_user(session: AsyncSession, email: str) -> schemas.UserInDb:
    user = crud.get_user_by_email(
        session=session, email=email)
    if user:
        user_dict = {
            "id": user.id,
            "regdate": user.regdate,
            "hashed_password": user.password,
            "email": user.email,
            "username": user.username
        }
        return schemas.UserInDb(**user_dict)


current_user = Annotated[schemas.UserInDb, Depends(get_current_user)]

###################################################################################################
###################################################################################################
###################################################################################################
