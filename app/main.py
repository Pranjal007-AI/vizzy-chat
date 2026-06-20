import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.database import (
    engine,
    Base
)

from app.api.chat import router

Base.metadata.create_all(
    bind=engine
)

app = FastAPI(
    title="Vizzy Chat API"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(os.path.join(STATIC_DIR, "generated"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(
    router,
    prefix="/chat",
    tags=["Chat"]
)


@app.get("/")
def root():
    return {
        "message": "Vizzy Chat Running"
    }