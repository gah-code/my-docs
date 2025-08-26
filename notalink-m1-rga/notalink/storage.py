from __future__ import annotations
import json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from .settings import get_settings
from .contracts.notes import NoteIn, NoteOut
from .ids import new_id

def _atomic_write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)

def atomic_write_json(path: Path, content: Dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(content, ensure_ascii=False, indent=2))

def read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class NoteStore:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        s = get_settings()
        self.base = Path(base_dir) if base_dir else Path(s.DATA_DIR)
        self.notes_dir = self.base / "notes"

    def _note_path(self, note_id: str, created_at: datetime) -> Path:
        return self.notes_dir / created_at.strftime("%Y/%m") / f"{note_id}.json"

    def create(self, payload: Dict[str, Any]) -> NoteOut:
        note_in = NoteIn.model_validate(payload)
        now = datetime.now(timezone.utc)
        note_id = note_in.id or new_id()
        path = self._note_path(note_id, now)
        note_out = NoteOut(
            id=note_id,
            title=note_in.title,
            body=note_in.body,
            category=note_in.category,
            tags=note_in.tags,
            source_url=note_in.source_url,
            source_kind=note_in.source_kind,
            created_at=now,
            updated_at=now,
            backlinks=[],
            citations=note_in.citations,
            provenance=note_in.provenance,
        )
        atomic_write_json(path, note_out.model_dump(mode="json"))
        return note_out

    def get(self, note_id: str) -> Optional[NoteOut]:
        for p in self.notes_dir.rglob(f"{note_id}.json"):
            return NoteOut.model_validate(read_json(p))
        return None

    def list_recent(self, limit: int = 20) -> List[NoteOut]:
        files = sorted(self.notes_dir.rglob("*.json"), key=os.path.getmtime, reverse=True)
        return [NoteOut.model_validate(read_json(p)) for p in files[:limit]]
