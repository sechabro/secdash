from fastapi import FastAPI, Request, Response, Form, HTTPException, Depends, status, Cookie
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from utils import stream_delivery, iostats, running_ps, established_connections, visitor_info, host_info_async, ps_stream, io_stream, password_hasher, password_verify
from datetime import timedelta, datetime, timezone
import asyncio
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import EmailStr
import os
from sqlmodel import SQLModel
import schemas
import logging
import crud
from database import temp_sync_engine, database_check, get_session
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")
SessionDep = Annotated[AsyncSession, Depends(get_session)]
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def get_current_user(access_token: str = Cookie(None)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if access_token is None:
        logger.info(f' \n\n access token is None for some reason...\n\n')
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            access_token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            logger.info(
                f' \n\n username from token is None, for some reason...\n\n')
            raise credentials_exception
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.now():
            credentials_exception.detail = "Token expired. Please login again."
            raise credentials_exception
        return username

    except InvalidTokenError:
        logger.info(
            f' \n\nInvalidTokenError exception raised for some reason...\n\n')
        raise credentials_exception


@app.on_event("startup")
async def on_startup():
    if await database_check():
        async with temp_sync_engine.begin() as conn:
            conn.run_sync(SQLModel.metadata.create_all)
    app.state.iostat_task = asyncio.create_task(
        io_stream(script="./scripts/iostat_logger.sh"))
    app.state.ps_task = asyncio.create_task(
        ps_stream(script="./scripts/ps_logger.sh"))
    logger.info(f' System metrics streaming started...')


@app.on_event("shutdown")
async def shutdown_async():
    app.state.iostat_task.cancel()
    app.state.ps_task.cancel()


@app.get("/", response_class=HTMLResponse, response_model=None)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/login")
async def login(request: Request, response: Response,
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                session: SessionDep) -> RedirectResponse:

    # does the user exist, and are their creds correct?
    user = await authenticate_user(session=session,
                                   email=form_data.username,
                                   password=form_data.password)
    # if not, raise exception.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # if user is authenticated, we'll build out the token, and prepare the redirect to /dashboard.
    token_response = await token(email=form_data.username,
                                 session=session,
                                 response=response)
    redirect_response = RedirectResponse(
        url="/dashboard", status_code=303
    )

    # before the redirect, we need to grab our "set-cookie" list from token response. that's where the token lives.
    set_cookie_headers = token_response.headers.getlist("set-cookie")

    # and then we need to append it as "set-cookie" in the redirect response.
    for cookie_header in set_cookie_headers:
        redirect_response.headers.append("set-cookie", cookie_header)

    # after, we can safely return the redirect response.
    return redirect_response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,  # <- change to True before pushing to production
        samesite="strict"
    )
    return response


@app.post("/register", response_class=HTMLResponse, response_model=schemas.User)
async def register(request: Request,
                   username: Annotated[str, Form()],
                   email: Annotated[EmailStr, Form()],
                   password: Annotated[str, Form()],
                   session: SessionDep):

    # does this user already exist? if so, raise an exception.
    db_user = await crud.get_user_by_email(session, email=email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # if confirmed user does not exist, let's hash & salt the password, and create the user object.
    pswd_hash_salt = await password_hasher(password=password)
    user = schemas.UserReg(username=username, email=email,
                           password=pswd_hash_salt)

    # then register the user in the database.
    reg_user = await crud.register_user(session=session, user=user)

    return RedirectResponse(url=f"/registered?username={reg_user.username}", status_code=303)


@app.get("/registered", response_class=HTMLResponse)
async def registered(request: Request, username: str, session: SessionDep):
    return templates.TemplateResponse("registered.html", {"request": request, "user": username})


@app.get("/dashboard", response_class=HTMLResponse, response_model=None)
async def dashboard(request: Request, session: SessionDep, current_user: str = Depends(get_current_user)):

    return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user})


@app.get("/visitor")
async def visitor(request: Request, session: SessionDep, current_user: str = Depends(get_current_user)) -> dict:
    return await visitor_info(request=request, session=session)


@app.get("/connections")
async def connections(current_user: str = Depends(get_current_user)) -> list:
    return await established_connections()


@app.get("/host")
async def host_status(current_user: str = Depends(get_current_user)) -> dict:
    return await host_info_async()


@app.get("/iostat-stream")
async def iostat_stream(current_user: str = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(stream_delivery(data_stream=iostats), media_type="text/event-stream")


@app.get("/process-stream")
async def process_stream(current_user: str = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(stream_delivery(data_stream=running_ps), media_type="text/event-stream")


##### OAUTH2 #######################################################################################
########## LOGIN ###################################################################################
############## FLOW ################################################################################
################# NOTES ############################################################################
# Technically, this is known as a Resource Owner Password Credentials (ROPC) grant. However, although
# it doesn’t involve an intermediate authorization code or redirecting to a third-party login page,
# it’s still one of the flows outlined in the OAuth2 specification. But it's my server that crafts
# and grants the authorization token.

EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECD', default=None)


@app.post("/token")
async def token(response: Response, email: EmailStr, session: SessionDep) -> Response:

    # set our token expiration, and create our token.
    access_token_expires = timedelta(minutes=EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": email}, expires_delta=access_token_expires)

    # set the token as a cookie in our response object, then return it.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=False,  # change to True before heading to production!
        max_age=access_token_expires.total_seconds()
    )

    return response


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

###################################################################################################
###################################################################################################
###################################################################################################
