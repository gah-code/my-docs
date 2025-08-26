from __future__ import annotations
from typing import Dict
from pydantic import BaseModel, Field

class GenerateIn(BaseModel):
    prompt_id: str = "summarization"
    variables: Dict[str, str]
    temperature: float = 0.0
    seed: int = 0
    max_tokens: int = 256
    model: str = "dummy"

class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0

class GenerateOut(BaseModel):
    text: str
    usage: TokenUsage
    trace_id: str
    elapsed_ms: int
    prompt_fingerprint: str
