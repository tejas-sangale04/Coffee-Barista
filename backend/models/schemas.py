from pydantic import BaseModel
from typing import Optional


class RecommendationRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    chat_id: Optional[str] = None

class RecommendationResponse(BaseModel):
    message: str
    prompt_count: int | None = None
    limit_reached: bool = False
