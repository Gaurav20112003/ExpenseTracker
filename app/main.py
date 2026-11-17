from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import initialize_database
from app.routes import router

APP_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="AI Expense Tracker", lifespan=lifespan)
app.include_router(router)
app.mount(
    "/static",
    StaticFiles(directory=APP_DIR / "static"),
    name="static",
)


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(APP_DIR / "templates" / "index.html")
