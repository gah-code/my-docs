# NotaLink — M1 (Research-grade AI) Scaffolding

- Python + MCP + Flask, filesystem-first.
- Deterministic Pydantic contracts.
- Research-grade AI layer: prompt registry, seeds, tracing, reproducible outputs (dummy engine by default).

Python‑first, filesystem‑first notes with MCP‑exposed tools and a minimal Flask UI. This step delivers the base repo, deterministic Pydantic contracts, an MCP server skeleton, and an “Add Note 2.0” page. A small “research‑grade AI” layer (prompt registry + seeded dummy engine + tracing) is included for reproducible experiments.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
cp .env.example .env

# Flask UI
export FLASK_APP=app:create_app
flask run --debug

# MCP server (stdio)
python -m mcp_server.server
```

---

## What’s included

- **Repo structure** (core, MCP server, Flask UI, AI layer, tests)
- **`pyproject.toml`** with Black/Ruff/Isort/Mypy and pytest
- **pre‑commit** hooks
- **`.env` loader** via `pydantic-settings` that creates local dirs on first run
- **MCP server skeleton** (stdio transport), tools:

  - `notes_create(payload)`, `notes_get(note_id)`, `notes_list(limit)`
  - `ai_generate(payload)` (seeded, deterministic dummy engine)
- **Pydantic contracts** (deterministic JSON in/out)
- **Flask UI shell** with **“Add Note 2.0”** layout
- **Dockerfile** + **docker‑compose** for local container runs

---

## Requirements

- Python **3.10+** (tested on 3.11)
- macOS or Linux recommended
- Optional: Docker 24+, docker‑compose

---

## Quickstart (local)

```bash
# 1) Create venv
python3 -m venv .venv && source .venv/bin/activate

# 2) Install
pip install -e ".[dev]"

# 3) pre-commit
pre-commit install

# 4) Env
cp .env.example .env
```

### Run the Flask UI

```bash
export FLASK_APP=app:create_app
flask run --debug
# → http://127.0.0.1:5000
```

### Run the MCP server (stdio)

```bash
python -m mcp_server.server
```

> Tools are auto‑registered in `mcp_server/server.py`.

---

## Docker

```bash
# Build + run
docker compose up --build

# Data and traces are mounted from ./var to /app/var inside the container
```

---

## Repo layout

```
notalink/
  pyproject.toml
  .pre-commit-config.yaml
  .gitignore
  .env.example
  Dockerfile
  docker-compose.yml
  README.md
  app/                      # Flask UI
    __init__.py
    routes.py
    templates/{base,home,add_note,view_note}.html
    static/css/styles.css
    static/js/add_note.js
    static/img/spec/...
  notalink/                 # Core + contracts + storage
    __init__.py
    settings.py             # .env loader; creates var/data, var/traces/*
    ids.py                  # ULID ids
    storage.py              # atomic JSON writer
    contracts/
      __init__.py
      notes.py links.py index.py quip.py graph.py
  ai/                       # Research-grade AI layer
    __init__.py
    contracts.py            # GenerateIn/Out, TokenUsage
    repro.py                # fingerprint + Stopwatch
    trace.py                # JSONL traces to var/traces
    prompts/{summarization.md,link_suggestions.md}
    engines/{__init__.py,base.py,dummy.py}
  mcp_server/               # MCP server skeleton
    __init__.py
    server.py               # FastMCP + tool registration
    tools/{__init__.py,notes.py,ai.py}
  tests/
    test_env_smoke.py
    test_storage_smoke.py
    test_ai_smoke.py
```

---

## Environment

`.env.example`:

```env
DATA_DIR=./var/data
LOG_LEVEL=INFO
SECRET_KEY=dev-secret
MCP_TRANSPORT=stdio
MCP_SERVER_NAME=notalink
QUIP_TOKEN=changeme
```

On first load, these dirs are ensured:

```
var/
  data/
    notes/ links/ index/ graph/
  traces/
```

---

## MCP tools (contracts & sample payloads)

### `notes_create(payload: dict) -> NoteOut`

```json
{
  "title": "Optional title",
  "body": "Raw note text...",
  "category": "fleeting",
  "tags": ["example", "zettel"],
  "source_url": null,
  "source_kind": "manual",
  "citations": [],
  "provenance": []
}
```

**Returns** deterministic JSON (datetime serialized) including `id`, `created_at`, `updated_at`.

### `notes_get(note_id: str) -> NoteOut | null`

```json
{ "id": "01h..." }
```

### `notes_list(limit: int = 20) -> NoteOut[]`

```json
{ "limit": 10 }
```

### `ai_generate(payload: dict) -> GenerateOut`

```json
{
  "prompt_id": "summarization",
  "variables": { "text": "One. Two. Three. Four." },
  "temperature": 0.0,
  "seed": 42,
  "max_tokens": 256,
  "model": "dummy"
}
```

**Returns**:

- `text`: deterministic bullets
- `usage`: prompt/completion/total token counts (approx)
- `trace_id` & `prompt_fingerprint`: stable SHA‑256 prefix
- `elapsed_ms`: timing
- Trace is appended to `var/traces/<trace_id>.jsonl`.

---

## UI overview

- **Home**: shows recent notes (title or truncated body).
- **Add Note 2.0**: body textarea, segmented category (fleeting/literature/permanent), conditional title, tags, source fields. A right‑side panel indicates the research AI capability is scaffolded (wiring into UI is a next step).
- **View Note**: renders a stored note.

---

## Testing (smoke)

```bash
pytest -q
```

> Smoke tests exercise settings dir creation, note create/get, and AI tool basics.

---

## Security & ops notes

- Runs as non‑root user in Docker.
- Local data persisted in `./var/data` (mounted via compose). Keep this directory out of source control.
- Keep secrets in `.env` (or Docker/K8s secrets if you deploy).

---

## Next steps

- Wire `ai_generate` from UI (summarize textarea into bullets).
- Add `links.suggest` + link review flow.
- Introduce Quip knowledge lookup tools.
- Dash + Cytoscape graph view with degree sizing and 1‑hop focus.

---

## Troubleshooting

- **Cannot save note**: ensure `DATA_DIR` exists or let the app create `var/data` on first run.
- **No styles**: verify static files are served at `/static/...`.
- **Docker port**: ensure `localhost:5000` isn’t in use; change in compose if needed.

---

**That’s the M1 scaffold README for this step.**
