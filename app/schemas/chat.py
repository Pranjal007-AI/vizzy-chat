from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    count: int = 1  # number of image variants, default 1


class RefineRequest(BaseModel):
    asset_id: int
    instruction: str
    count: int = 1  # number of refined variants