
# poc

# 📁 Project layout

```
quip-folder-suite/
├─ .env.example
├─ requirements.txt
├─ README.md
├─ Makefile
├─ src/
│  ├─ quip_api.py
│  ├─ folder_walk.py
│  ├─ document_ops.py
│  ├─ analyze.py
│  └─ utils.py
├─ scripts/
│  ├─ run_walk.py
│  ├─ run_ingest.py
│  └─ run_analyze.py
└─ tests/
   └─ test_smoke.py
```

---

## 🔐 `.env.example`

```
QUIP_BASE=https://platform.quip.com
QUIP_TOKEN=your_quip_access_token
QUIP_FOLDER_ID=your_root_folder_id

# Optional targets for direct ops
QUIP_DOC_THREAD_ID=doc_thread_id_if_you_want_to_append_html
QUIP_SHEET_THREAD_ID=spreadsheet_thread_id_if_applicable
```

---

## 📦 `requirements.txt`

```
python-dotenv>=1.0.1
requests>=2.32.0
beautifulsoup4>=4.12.3
pytest>=8.0.0
```

---

## 🧰 `src/utils.py`

```python
import logging, os, sys, time

def setup_logging():
    lvl = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, lvl, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        stream=sys.stdout,
    )
    return logging.getLogger("quip-suite")

def sleep_polite(seconds: float):
    time.sleep(max(0.0, seconds))
```

---

## 🌐 `src/quip_api.py` — minimal client with retries & rate-limit handling

```python
import os, time, requests, logging
from dotenv import load_dotenv

load_dotenv()
LOG = logging.getLogger("quip-suite")

QUIP_BASE = os.getenv("QUIP_BASE", "https://platform.quip.com").rstrip("/")
QUIP_TOKEN = os.getenv("QUIP_TOKEN")
if not QUIP_TOKEN:
    raise SystemExit("QUIP_TOKEN missing. Copy .env.example to .env and fill it.")

S = requests.Session()
S.headers.update({"Authorization": f"Bearer {QUIP_TOKEN}"})

def _backoff_wait(resp: requests.Response, attempt: int):
    # Honor Quip rate-limit headers if present; otherwise exponential backoff
    reset = None
    if resp is not None:
        reset = resp.headers.get("X-RateLimit-Reset") or resp.headers.get("X-Company-RateLimit-Reset")
    if reset:
        try:
            wait = max(2, int(reset) - int(time.time()))
        except Exception:
            wait = 2 * (attempt + 1)
    else:
        wait = 2 * (attempt + 1)
    wait = min(wait, 15)
    LOG.warning("Throttled (status=%s). Sleeping %ss before retry...", resp.status_code if resp else "?", wait)
    time.sleep(wait)

def request(method: str, path: str, **kwargs) -> requests.Response:
    url = f"{QUIP_BASE}{path}"
    attempts = 0
    while True:
        try:
            r = S.request(method, url, timeout=30, **kwargs)
        except requests.RequestException as e:
            if attempts >= 5:
                raise
            LOG.error("Network error: %s", e)
            _backoff_wait(None, attempts)
            attempts += 1
            continue

        if r.status_code in (200, 201, 204):
            return r

        if r.status_code in (429, 500, 502, 503, 504):
            if attempts >= 5:
                r.raise_for_status()
            _backoff_wait(r, attempts)
            attempts += 1
            continue

        # Unexpected error: surface details to caller
        msg = f"HTTP {r.status_code} on {url} :: {r.text[:300]}"
        LOG.error(msg)
        r.raise_for_status()

# --- Convenience wrappers (typed-ish) ---
def get_folder(folder_id: str, include_chats=False) -> dict:
    r = request("GET", f"/1/folders/{folder_id}", params={"include_chats": str(include_chats).lower()})
    return r.json().get("folder", {})

def get_thread_meta(thread_id_or_secret: str) -> dict:
    r = request("GET", f"/2/threads/{thread_id_or_secret}")
    return r.json().get("thread", {})

def get_thread_html(thread_id_or_secret: str) -> str:
    html, cursor = "", None
    data = request("GET", f"/2/threads/{thread_id_or_secret}/html").json()
    html += data.get("html", "")
    cursor = data.get("cursor")
    while cursor:
        data = request("GET", f"/2/threads/{thread_id_or_secret}/html", params={"cursor": cursor}).json()
        html += data.get("html", "")
        cursor = data.get("cursor")
    return html

def append_document_html(thread_id: str, html_snippet: str) -> dict:
    # ⚠️ Uses /1/threads/edit with operation=append (simple, test-friendly)
    payload = {"thread_id": thread_id, "content": html_snippet, "operation": "append"}
    r = request("POST", "/1/threads/edit", data=payload)
    return r.json()

def export_spreadsheet_csv(thread_id: str) -> str:
    r = request("GET", f"/1/threads/{thread_id}/export/csv", stream=True)
    return r.text
```

---

## 🧭 `src/folder_walk.py` — recurse a folder safely

```python
import logging
from typing import List, Dict
from .quip_api import get_folder, get_thread_meta

LOG = logging.getLogger("quip-suite")

def walk_folder(folder_id: str, max_depth: int = 10) -> List[Dict]:
    """
    Returns a flat list of entries:
      { "kind": "thread"|"folder", "id": "...", "title": str|None, "type": "DOCUMENT|SPREADSHEET|CHAT|SLIDE|None" }
    Deduplicate by thread id if needed upstream.
    """
    seen_threads = set()
    results: List[Dict] = []

    def _recurse(fid: str, depth: int):
        if depth > max_depth:
            LOG.warning("Max depth reached at folder %s", fid)
            return
        fobj = get_folder(fid, include_chats=False)
        title = fobj.get("title")
        results.append({"kind": "folder", "id": fid, "title": title, "type": None})

        for child in fobj.get("children", []):
            if "folder_id" in child:
                _recurse(child["folder_id"], depth + 1)
            elif "thread_id" in child:
                tid = child["thread_id"]
                if tid in seen_threads:
                    continue
                seen_threads.add(tid)
                meta = get_thread_meta(tid)
                results.append({
                    "kind": "thread",
                    "id": tid,
                    "title": meta.get("title"),
                    "type": meta.get("type"),
                    "link": meta.get("link")
                })
    _recurse(folder_id, 0)
    return results
```

---

## 📝 `src/document_ops.py` — append + safe markers for validation

```python
import time, logging
from .quip_api import append_document_html, get_thread_html

LOG = logging.getLogger("quip-suite")

def append_marker(doc_thread_id: str, body_html: str = "<p>Appended via API.</p>") -> str:
    marker = f"<!-- test-marker:{int(time.time())} -->"
    snippet = f"{marker}<h2>Automated Test</h2>{body_html}"
    resp = append_document_html(doc_thread_id, snippet)
    if "thread" not in resp:
        raise RuntimeError(f"Unexpected append response: {resp}")
    html = get_thread_html(doc_thread_id)
    if marker not in html:
        raise AssertionError("Marker not found after append; document update may have failed.")
    LOG.info("Document ingestion validated. Marker %s found.", marker)
    return marker
```

---

## 🔍 `src/analyze.py` — tiny HTML analyzer (headings/word count)

```python
from bs4 import BeautifulSoup
from typing import Dict

def analyze_html(html: str) -> Dict:
    soup = BeautifulSoup(html or "", "html.parser")
    # Headings map
    headings = {
        "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
        "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
        "h3": [h.get_text(strip=True) for h in soup.find_all("h3")],
    }
    # Naive word count from text
    text = soup.get_text(" ", strip=True)
    words = len([w for w in text.split() if w])
    return {"headings": headings, "word_count": words}
```

---

## 🧪 Scripts (CLI)

### `scripts/run_walk.py`

```python
import os, json, logging
from dotenv import load_dotenv
from src.utils import setup_logging
from src.folder_walk import walk_folder

if __name__ == "__main__":
    load_dotenv()
    LOG = setup_logging()
    folder_id = os.getenv("QUIP_FOLDER_ID")
    if not folder_id:
        raise SystemExit("QUIP_FOLDER_ID not set in env.")

    items = walk_folder(folder_id)
    print(json.dumps(items, indent=2))
    LOG.info("Walked folder %s; found %d items.", folder_id, len(items))
```

### `scripts/run_ingest.py`

```python
import os, logging
from dotenv import load_dotenv
from src.utils import setup_logging
from src.document_ops import append_marker

if __name__ == "__main__":
    load_dotenv()
    LOG = setup_logging()
    doc_id = os.getenv("QUIP_DOC_THREAD_ID")
    if not doc_id:
        raise SystemExit("QUIP_DOC_THREAD_ID not set. Provide a DOCUMENT thread id.")
    marker = append_marker(doc_id, "<p>Smoke test content.</p>")
    LOG.info("Ingestion complete. Marker: %s", marker)
```

### `scripts/run_analyze.py`

```python
import os, json, logging
from dotenv import load_dotenv
from src.utils import setup_logging
from src.quip_api import get_thread_html
from src.analyze import analyze_html

if __name__ == "__main__":
    load_dotenv()
    LOG = setup_logging()
    thread_id = os.getenv("QUIP_DOC_THREAD_ID")
    if not thread_id:
        raise SystemExit("QUIP_DOC_THREAD_ID not set. Point to a document to analyze.")
    html = get_thread_html(thread_id)
    report = analyze_html(html)
    print(json.dumps(report, indent=2))
    LOG.info("Analysis done: %s words; h1=%d h2=%d h3=%d",
             report["word_count"],
             len(report["headings"]["h1"]),
             len(report["headings"]["h2"]),
             len(report["headings"]["h3"]))
```

---

## 🧪 `tests/test_smoke.py` (pytest)

```python
import os, pytest
from dotenv import load_dotenv
from src.quip_api import get_thread_html
from src.document_ops import append_marker
from src.analyze import analyze_html

load_dotenv()

DOC_ID = os.getenv("QUIP_DOC_THREAD_ID")

@pytest.mark.skipif(not DOC_ID, reason="Set QUIP_DOC_THREAD_ID in env to run this test.")
def test_append_and_readback():
    marker = append_marker(DOC_ID, "<p>Test row</p>")
    html = get_thread_html(DOC_ID)
    assert marker in html

@pytest.mark.skipif(not DOC_ID, reason="Set QUIP_DOC_THREAD_ID in env to run this test.")
def test_analyze():
    html = get_thread_html(DOC_ID)
    report = analyze_html(html)
    assert "word_count" in report and report["word_count"] >= 0
```

---

## 🧰 `Makefile`

```make
.PHONY: install walk ingest analyze test lint

install:
\tpip install -r requirements.txt

walk:
\tpython scripts/run_walk.py

ingest:
\tpython scripts/run_ingest.py

analyze:
\tpython scripts/run_analyze.py

test:
\tpytest -q
```

---

## 📖 `README.md` (short version)

```md
# Quip Folder Suite (Ingest • View • Analyze)

This scaffold lets you:
- **Walk a Quip folder** (recursively) and list documents/spreadsheets with IDs
- **Append test content** to a document (with a unique marker) to validate ingestion
- **Read back HTML** and **analyze** basic structure (headings, word count)
- Includes **error handling**, **rate-limit backoff**, and **pytest smoke tests**

## Setup
1. `cp .env.example .env` and fill `QUIP_TOKEN`, `QUIP_FOLDER_ID`, and optionally `QUIP_DOC_THREAD_ID`.
2. `make install`

## Commands
- `make walk` — prints JSON list of folders/threads under `QUIP_FOLDER_ID`
- `make ingest` — appends a marker + snippet to `QUIP_DOC_THREAD_ID` and verifies
- `make analyze` — fetches HTML for `QUIP_DOC_THREAD_ID` and prints headings/word count
- `make test` — runs pytest smoke tests

## Notes
- Ensure your token has access to the folder and threads you target.
- Large docs paginate in HTML; handled automatically.
- Folders may contain subfolders and multiple references to the same thread; dedupe upstream if needed.
```

---

## ✅ What this gives you out-of-the-box

* **Testing ingestion:** `make ingest` appends a *unique* HTML marker and asserts it’s present after read-back.
* **Viewing:** `make walk` enumerates a folder tree so you can see IDs/titles/types in one JSON payload.
* **Analyzing:** `make analyze` returns a tiny report (heading lists + word count) so you can confirm downstream parsing.
* **Error handling:** network retries, rate-limit aware backoff, explicit exits on missing env, and meaningful log lines.

If you want, I can also add a **VS Code debug profile** (`.vscode/launch.json`) and a **pre-commit** config.
