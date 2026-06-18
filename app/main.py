from fastapi import FastAPI

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