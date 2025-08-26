from __future__ import annotations
from pathlib import Path
from string import Template
from ai.contracts import GenerateIn, GenerateOut, TokenUsage
from ai.engines.dummy import DummyEngine
from ai.repro import fingerprint, Stopwatch
from ai.trace import write_trace

def _load_prompt(prompt_id: str) -> str:
    root = Path(__file__).resolve().parents[2] / "ai" / "prompts"
    path = root / f"{prompt_id}.md"
    return path.read_text(encoding="utf-8")

def register_tools(mcp) -> None:
    engine = DummyEngine()

    @mcp.tool()
    def ai_generate(payload: dict) -> dict:
        req = GenerateIn.model_validate(payload)
        prompt_text = _load_prompt(req.prompt_id)
        with Stopwatch() as sw:
            text, usage = engine.generate(req, prompt_text)
        fid = fingerprint(prompt_text, req.variables, {
            "temperature": req.temperature, "seed": req.seed, "max_tokens": req.max_tokens, "model": req.model
        })
        write_trace(fid, {"req": req.model_dump(), "out": text, "usage": usage.model_dump(), "elapsed_ms": sw.elapsed_ms})
        out = GenerateOut(text=text, usage=usage, trace_id=fid, elapsed_ms=sw.elapsed_ms, prompt_fingerprint=fid)
        return out.model_dump()
