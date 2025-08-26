from __future__ import annotations
import hashlib, json, time
from typing import Dict, Any

def fingerprint(prompt_text: str, variables: Dict[str, str], params: Dict[str, Any]) -> str:
    data = {"prompt": prompt_text, "vars": variables, "params": params}
    b = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()[:16]

class Stopwatch:
    def __enter__(self):
        import time
        self.t0 = time.perf_counter()
        return self
    def __exit__(self, *exc):
        self.elapsed_ms = int((time.perf_counter() - self.t0) * 1000)
