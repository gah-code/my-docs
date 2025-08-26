from __future__ import annotations
from pydantic import BaseModel

class IndexRebuildIn(BaseModel):
    full: bool = False

class IndexRebuildOut(BaseModel):
    items: int
    took_ms: int
