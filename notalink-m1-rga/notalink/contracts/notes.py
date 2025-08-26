from __future__ import annotations
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, AnyUrl, Field

NoteType = Literal["fleeting", "literature", "permanent"]

class Citation(BaseModel):
    id: str
    url: AnyUrl
    title: str
    at: datetime

class NoteIn(BaseModel):
    title: Optional[str] = None
    body: str = Field(min_length=1)
    category: NoteType
    tags: List[str] = []
    source_url: Optional[AnyUrl] = None
    source_kind: Optional[Literal["manual", "url", "quip"]] = "manual"
    id: Optional[str] = None
    citations: List[Citation] = []
    provenance: List[str] = []

class NoteOut(BaseModel):
    id: str
    title: Optional[str] = None
    body: str
    category: NoteType
    tags: List[str] = []
    source_url: Optional[AnyUrl] = None
    source_kind: Optional[Literal["manual", "url", "quip"]] = "manual"
    created_at: datetime
    updated_at: datetime
    backlinks: List[str] = []
    citations: List[Citation] = []
    provenance: List[str] = []
