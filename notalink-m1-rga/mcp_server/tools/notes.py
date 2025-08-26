from __future__ import annotations
from notalink.storage import NoteStore

def register_tools(mcp) -> None:
    store = NoteStore()

    @mcp.tool()
    def notes_create(payload: dict) -> dict:
        note_out = store.create(payload)
        return note_out.model_dump(mode="json")

    @mcp.tool()
    def notes_get(note_id: str) -> dict | None:
        note = store.get(note_id)
        return note.model_dump(mode="json") if note else None

    @mcp.tool()
    def notes_list(limit: int = 20) -> list[dict]:
        return [n.model_dump(mode="json") for n in store.list_recent(limit=limit)]
