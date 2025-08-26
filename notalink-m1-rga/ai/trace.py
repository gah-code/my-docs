from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from notalink.settings import get_settings

def write_trace(trace_id: str, record: Dict[str, Any]) -> None:
    s = get_settings()
    path = Path(s.TRACES_DIR) / f"{trace_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
