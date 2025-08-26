from __future__ import annotations
from typing import Tuple
from ai.contracts import GenerateIn, TokenUsage

class BaseEngine:
    def generate(self, req: GenerateIn, prompt_text: str) -> tuple[str, TokenUsage]:
        raise NotImplementedError
