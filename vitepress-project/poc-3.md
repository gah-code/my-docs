
# Quip Ingestion Test: Quick Start

## 1) Folder layout

```
quip-ingestion-test/
├─ .env.example
├─ requirements.txt
├─ README.md
└─ test_quip_ingestion.py
```

**.env.example**

```
QUIP_BASE=https://platform.quip.com
QUIP_TOKEN=your_quip_access_token
QUIP_DOC_THREAD_ID=doc_thread_id_here           # target DOCUMENT thread
QUIP_SHEET_THREAD_ID=spreadsheet_thread_id_here # target SPREADSHEET thread
```

**requirements.txt**

```
python-dotenv>=1.0.1
requests>=2.32.0
pandas>=2.2.0
pytest>=8.0.0
```

---

## 2) What this “test file” includes (key components)

* **Client initialization** using `QUIP_BASE` + `QUIP_TOKEN`.
* **Data preparation** with Pandas (for spreadsheet rows) and HTML (for document).
* **API ingestion** examples:

  * Update a **DOCUMENT** by appending HTML content.
  * Update a **SPREADSHEET** by adding rows (simple CSV-to-cells approach).
* **Validation**: read back the content and assert what changed.
* **Error handling & rate-limit backoff**: basic retry and header-aware sleeping.
* **Rate limits**: gentle delays and simple exponential backoff.

---

## 3) The single test script

> Save as `test_quip_ingestion.py`.
> You can run it directly (`python test_quip_ingestion.py`) or with pytest (`pytest -q`).

```python
import os, time, json, math, csv, io, sys, typing
from dataclasses import dataclass
import requests
import pandas as pd
from dotenv import load_dotenv

# --- Load environment ---
load_dotenv()
QUIP_BASE = os.getenv("QUIP_BASE", "https://platform.quip.com").rstrip("/")
QUIP_TOKEN = os.getenv("QUIP_TOKEN")
DOC_THREAD_ID = os.getenv("QUIP_DOC_THREAD_ID")      # DOCUMENT thread
SHEET_THREAD_ID = os.getenv("QUIP_SHEET_THREAD_ID")  # SPREADSHEET thread

if not QUIP_TOKEN:
    print("ERROR: QUIP_TOKEN missing. Fill .env or environment variables.", file=sys.stderr)
    sys.exit(1)

S = requests.Session()
S.headers.update({"Authorization": f"Bearer {QUIP_TOKEN}"})


# ---------- Helpers: rate-limit-safe GET/POST ----------
def _backoff_wait(resp: requests.Response, attempt: int):
    # Respect HTTP 429/5xx and Quip X-RateLimit headers if present
    if resp is not None:
        # Soft hint from headers
        reset = resp.headers.get("X-RateLimit-Reset") or resp.headers.get("X-Company-RateLimit-Reset")
        if reset:
            try:
                # It's usually a unix epoch seconds; if not, just sleep minimally
                wait = max(2, int(reset) - int(time.time()))
                time.sleep(min(wait, 15))
                return
            except Exception:
                pass
    # Exponential fallback
    time.sleep(min(2 * (attempt + 1), 10))


def _req(method: str, url: str, **kwargs) -> requests.Response:
    attempts = 0
    while True:
        r = S.request(method, url, timeout=30, **kwargs)
        if r.status_code in (200, 201, 204):
            return r
        if r.status_code in (429, 500, 502, 503, 504):
            _backoff_wait(r, attempts)
            attempts += 1
            if attempts > 5:
                r.raise_for_status()
        else:
            r.raise_for_status()


# ---------- Core Quip calls (minimal) ----------
def get_thread_meta(thread_id: str) -> dict:
    url = f"{QUIP_BASE}/2/threads/{thread_id}"
    return _req("GET", url).json().get("thread", {})

def get_thread_html(thread_id: str) -> str:
    url = f"{QUIP_BASE}/2/threads/{thread_id}/html"
    data = _req("GET", url).json()
    html = data.get("html", "")
    cursor = data.get("cursor")
    # If long doc: paginate until no cursor
    while cursor:
        more = _req("GET", url, params={"cursor": cursor}).json()
        html += more.get("html", "")
        cursor = more.get("cursor")
    return html

def append_document_html(thread_id: str, html_snippet: str) -> dict:
    """
    Append HTML to the end of a DOCUMENT.
    Quip document updates typically use the "edits" endpoint with operations.
    For simplicity, we use /1/threads/edit to append at the end.

    NOTE: This uses a basic "append" op with 'content' in HTML.
    """
    url = f"{QUIP_BASE}/1/threads/edit"
    payload = {
        "thread_id": thread_id,
        "content": html_snippet,
        "operation": "append"  # "append" adds to end; "prepend" adds to start
    }
    return _req("POST", url, data=payload).json()

def export_spreadsheet_csv(thread_id: str) -> str:
    """
    Export a SPREADSHEET as CSV to let us read/validate quickly.
    If you prefer XLSX, use /1/threads/{id}/export/xlsx and open with pandas.
    """
    url = f"{QUIP_BASE}/1/threads/{thread_id}/export/csv"
    r = _req("GET", url, stream=True)
    return r.text

def add_rows_to_spreadsheet(thread_id: str, rows: typing.List[typing.List[str]]) -> dict:
    """
    Minimal approach: send a CSV “append” via the spreadsheets import endpoint.
    Depending on your tenant, you can use import endpoints that merge/append.

    Here we simulate an append-by-import to a new sheet (or bottom of sheet),
    which is a common pattern for test ingestion.
    """
    # Build CSV in-memory
    buf = io.StringIO()
    w = csv.writer(buf)
    for row in rows:
        w.writerow(row)
    buf.seek(0)

    files = {
        "file": ("append.csv", buf.read(), "text/csv"),
    }
    # Endpoint example: /1/threads/{id}/import/csv (varies by edition; if not available,
    # you can use specific cell/range endpoints. Replace below with your supported route.)
    url = f"{QUIP_BASE}/1/threads/{thread_id}/import/csv"
    return _req("POST", url, files=files).json()


# ---------- Test data (notation conventions made explicit) ----------
def make_test_dataframe() -> pd.DataFrame:
    return pd.DataFrame({
        "Column1": ["ValueA", "ValueB", "ValueC"],
        "Column2": ["ValueX", "ValueY", "ValueZ"]
    })

def df_to_rows(df: pd.DataFrame) -> typing.List[typing.List[str]]:
    # Convert to list-of-lists (strings) for CSV/spreadsheet cells
    rows = [list(map(str, df.columns.tolist()))]
    for _, r in df.iterrows():
        rows.append([str(x) for x in r.tolist()])
    return rows


# ---------- End-to-end “test” flows ----------
def test_ingest_document():
    if not DOC_THREAD_ID:
        print("Skipping document test (QUIP_DOC_THREAD_ID not set).")
        return

    # 1) Prepare content with a unique marker (for idempotent checks)
    marker = f"<!-- test-marker:{int(time.time())} -->"
    html_snippet = f"{marker}<h2>Automated Ingestion Test</h2><p>Appended via API.</p>"

    # 2) Append to doc
    resp = append_document_html(DOC_THREAD_ID, html_snippet)
    assert "thread" in resp, f"Unexpected response: {resp}"

    # 3) Read back and validate
    body = get_thread_html(DOC_THREAD_ID)
    assert marker in body, "Marker not found in document HTML after append."
    print("✅ Document ingestion validated (marker found).")

def test_ingest_spreadsheet():
    if not SHEET_THREAD_ID:
        print("Skipping spreadsheet test (QUIP_SHEET_THREAD_ID not set).")
        return

    # 1) Prepare test data as DataFrame
    df = make_test_dataframe()
    rows = df_to_rows(df)  # header + rows

    # 2) Append rows via import (or your supported API)
    resp = add_rows_to_spreadsheet(SHEET_THREAD_ID, rows)
    # A minimal success check—adjust based on your tenant’s import response
    assert resp, f"Empty import response: {resp}"

    # 3) Read back (CSV export) and validate a cell value
    csv_text = export_spreadsheet_csv(SHEET_THREAD_ID)
    assert "ValueA" in csv_text and "ValueZ" in csv_text, "Expected values not present in exported CSV."
    print("✅ Spreadsheet ingestion validated (values present in CSV export).")


if __name__ == "__main__":
    # Run both flows without pytest, handy for quick manual checks
    try:
        test_ingest_document()
    except Exception as e:
        print(f"Document test failed: {e}")
    try:
        test_ingest_spreadsheet()
    except Exception as e:
        print(f"Spreadsheet test failed: {e}")
```

---

## 4) Running it

```bash
# 1) Setup
cp .env.example .env
# fill in: QUIP_TOKEN, QUIP_DOC_THREAD_ID, QUIP_SHEET_THREAD_ID

# 2) Install deps
pip install -r requirements.txt

# 3) Run directly (prints success lines)
python test_quip_ingestion.py

# OR with pytest (clean pass/fail)
pytest -q
```

---

## 5) Notation & IDs (what you’ll *see* in responses)

* **Thread IDs**: 12-char mixed case (e.g., `abcdEfGHijkL`), same slug in URLs.
* **Types**: `DOCUMENT`, `SPREADSHEET`, `CHAT`, `SLIDE` (from `/2/threads/{id}`).
* **HTML body**: paginates via `cursor` (script handles loop).
* **CSV/XLSX**: spreadsheets export with `/export/csv` or `/export/xlsx`.

---

## 6) Validation strategy (simple → solid)

* **Simple** (included):

  * Document: inject a unique `<!-- test-marker:TIMESTAMP -->` and assert presence in HTML.
  * Spreadsheet: append rows and check for known values in CSV export.

* **Stronger** (optional):

  * Record the **pre** size (characters/rows) → ingest → confirm **post** size increased by expected delta.
  * Idempotency flag: include a UUID marker and skip if found (avoid duplicate test writes).
  * Tidy-up: add a “Test Data” section in docs to isolate noise, or schedule cleanups.

---

## 7) Error handling & rate limiting

* Retries on `429/5xx` with exponential backoff.
* Honors `X-RateLimit-Reset` when present (polite sleeping).
* Suggestion for bulk tests: add `time.sleep(0.2–0.5s)` between calls, or batch requests.

---

## 8) Security & safety notes

* Keep tokens in **.env** (never commit).
* Consider a **non-production** Quip space or a **sandbox folder** for test content.
* Avoid PII in test data. Use neutral sample values (`ValueA`, `ValueB`, etc.).

---

## 9) What to change if your tenant differs

* Some editions expose different import endpoints for spreadsheets.

  * If `/1/threads/{id}/import/csv` isn’t available, switch to a **cell/range update** endpoint or maintain a **local CSV → HTML table** append into a document for smoke testing.
* If your spreadsheet lives as a **sheet embedded inside a document**, you’ll likely validate via **document HTML** or use a **document export** instead of the standalone spreadsheet export.

---

### Want this turned into a tiny Git repo with a `Makefile` and VS Code debug config?

Say the word and I’ll drop those scaffolds in the same style—ready to run with `make test` and a one-click VS Code debug profile.
