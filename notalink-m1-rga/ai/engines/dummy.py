from __future__ import annotations
import re, random
from ai.contracts import GenerateIn, TokenUsage
from .base import BaseEngine

class DummyEngine(BaseEngine):
    def generate(self, req: GenerateIn, prompt_text: str):
        text = req.variables.get("text") or " ".join(req.variables.values())
        sents = [s.strip() for s in re.split(r"[\.!?]\s+", text) if s.strip()]
        random.seed(req.seed)
        picks = (sents[:3] if len(sents) <= 3 else [sents[i % len(sents)] for i in random.sample(range(len(sents)), 3)])
        bullets = "- " + "\n- ".join(picks) if picks else "- (no content)"
        usage = TokenUsage(prompt=len(prompt_text.split()), completion=len(bullets.split()))
        usage.total = usage.prompt + usage.completion
        return bullets, usage
