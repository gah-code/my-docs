from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

class CreateLinkIn(BaseModel):
    source_id: str
    target_id: str
    relation: Literal["mentions", "supports", "contradicts", "cites"] = "mentions"
    context: Optional[str] = None

class CreateLinkOut(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation: str
