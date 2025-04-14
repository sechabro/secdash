from fastapi import FastAPI, Request, Response, HTTPException, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from utils import established_connections, visitor_info, host_info_async, ps_stream, io_stream, password_hasher
from database import engine, database_check, get_session
from sqlmodel import SQLModel
import schemas
import logging
import crud
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")
SessionDep = Annotated[AsyncSession, Depends(get_session)]
app = FastAPI()


@app.on_event("startup")
async def on_startup():
    if database_check():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


@app.get("/", response_class=HTMLResponse, response_model=None)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


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
