from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.database as database
from app.config import ALLOWED_ORIGINS
from app.models import Expense, User  # noqa: F401
from app.routes.expenses import router as expenses_router
from app.routes.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.Base.metadata.create_all(bind=database.engine)
    yield


app = FastAPI(title="Expense AI API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(expenses_router)
app.include_router(users_router)

# Serve the simple frontend placed in `frontend/`
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/health")
def health_check():
    return {"status": "ok"}
