from __future__ import annotations
from typing import Literal, Optional, List
from pydantic import BaseModel, HttpUrl

class QuipSearchIn(BaseModel):
    query: str
    count: int = 8
    only_titles: bool = False
    filters: List[str] = []

class QuipSearchHit(BaseModel):
    id: str
    type: Literal["doc", "chat", "folder", "thread"]
    title: str
    path: str
    snippet: Optional[str] = None
    url: str

class QuipSearchOut(BaseModel):
    results: List[QuipSearchHit]
