
# What “folder reads” mean in Quip

- Quip’s core content unit is a **thread** (document, spreadsheet, or chat). Most reads are “get thread(s) → get body (HTML) → optionally export spreadsheet”. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- Folders are **tags**, not a strict filesystem, and a thread can live in multiple folders. Still, `/folders/{id}` returns a **children** list you can traverse (and it can contain both `thread_id` and `folder_id` items). ([Quip](https://quip.com/api/reference "Quip Automation API Reference"), [GitHub](https://github.com/quip/quip-api/blob/master/samples/baqup/main.py?utm_source=chatgpt.com "quip-api/samples/baqup/main.py at master - GitHub"))

- Useful rate limits: default **50 req/min/user**, **750 req/hour/user**, and **600 req/min/company**; responses include helpful `X-RateLimit-*` headers. Build backoff. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

---

# Endpoints you’ll use (quick map)

- **Find your folder IDs (and special folders):** `GET /1/users/current` (returns `desktop_folder_id`, `private_folder_id`, etc.). ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- **Read a folder (and its children):** `GET /1/folders/{id}` (set `include_chats=true` if you want chats). The response includes `children` with `thread_id` **and** possibly `folder_id`. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- **Read thread metadata:** `GET /2/threads/{id-or-secret}` and **HTML body:** `GET /2/threads/{id-or-secret}/html`. Paginate with `cursor`. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- **Spreadsheet export (if needed):** `GET /1/threads/{thread_id}/export/xlsx`. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

> Tip: If you only have a URL, you can pass the **secret path** (the 12-char slug in the URL) in place of the thread/folder ID to the v2 “Get Thread” and “Get Folder Link Sharing Settings” calls; both v2 and v1 docs explain this. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

---

# cURL “smoke test”

Replace `{{TOKEN}}` with your API token and `{{FOLDER_ID}}` with the folder you want to read.

```bash
# 1) Who am I? (helps discover special folder IDs)
curl -s -H "Authorization: Bearer {{TOKEN}}" \
  "https://platform.quip.com/1/users/current"

# 2) Read a folder’s children (threads & subfolders)
curl -s -H "Authorization: Bearer {{TOKEN}}" \
  "https://platform.quip.com/1/folders/{{FOLDER_ID}}?include_chats=false"

# 3) For each thread_id from #2, get metadata
curl -s -H "Authorization: Bearer {{TOKEN}}" \
  "https://platform.quip.com/2/threads/AVN9AAeqq5w"

# 4) Get the HTML body (documents & spreadsheets-in-docs)
curl -s -H "Authorization: Bearer {{TOKEN}}" \
  "https://platform.quip.com/2/threads/AVN9AAeqq5w/html"

# 5) If a thread is a standalone spreadsheet, export to .xlsx
curl -L -H "Authorization: Bearer {{TOKEN}}" \
  -o sheet.xlsx \
  "https://platform.quip.com/1/threads/THREADID/export/xlsx"
```

These calls and fields are straight from Quip’s current Automation API reference. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

---

# Python script (walk a folder, recurse, and read content)

This script:

- Recursively walks a folder’s children,

- Fetches thread metadata,

- Pulls HTML for docs,

- Exports spreadsheets to disk.

```python
import os, time, requests, pathlib

BASE = os.getenv("QUIP_BASE", "https://platform.quip.com")
TOKEN = os.environ["QUIP_TOKEN"]        # put your token in env
FOLDER_ID = os.environ["QUIP_FOLDER_ID"]  # the folder you want to read

S = requests.Session()
S.headers.update({"Authorization": f"Bearer {TOKEN}"})

def backoff(resp):
    # naive politeness/backoff using headers documented by Quip
    rl_rem = resp.headers.get("X-Ratelimit-Remaining")
    co_rem = resp.headers.get("X-Company-RateLimit-Remaining")
    if rl_rem == "0" or co_rem == "0":
        reset = resp.headers.get("X-Ratelimit-Reset") or resp.headers.get("X-Company-RateLimit-Reset")
        time.sleep(2)  # minimal wait; production: compute from reset
    if resp.status_code in (429, 503, 504):
        time.sleep(2)

def get_json(url, **params):
    while True:
        r = S.get(url, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        backoff(r)

def get_folder(folder_id, include_chats=False):
    url = f"{BASE}/1/folders/{folder_id}"
    return get_json(url, include_chats=str(include_chats).lower())

def get_thread(thread_id_or_secret):
    url = f"{BASE}/2/threads/{thread_id_or_secret}"
    return get_json(url)

def get_thread_html(thread_id_or_secret):
    url = f"{BASE}/2/threads/{thread_id_or_secret}/html"
    data = get_json(url)
    return data.get("html", "")

def export_spreadsheet_xlsx(thread_id, out_path):
    url = f"{BASE}/1/threads/{thread_id}/export/xlsx"
    with S.get(url, stream=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

def walk_folder(folder_id, depth=0, max_depth=10):
    assert depth <= max_depth, "Exceeded max depth"
    folder = get_folder(folder_id)
    children = folder.get("children", [])
    results = []

    for child in children:
        if "folder_id" in child:
            results += walk_folder(child["folder_id"], depth+1, max_depth)
        elif "thread_id" in child:
            tid = child["thread_id"]
            meta = get_thread(tid).get("thread", {})
            ttype = meta.get("type")
            title = meta.get("title")
            link = meta.get("link")

            entry = {"thread_id": tid, "type": ttype, "title": title, "link": link}

            if ttype == "DOCUMENT":
                entry["html"] = get_thread_html(tid)
            elif ttype == "SPREADSHEET":
                safe = "".join(c for c in (title or tid) if c.isalnum() or c in (" ", "_", "-")).strip()
                out = pathlib.Path("exports") / f"{safe or tid}.xlsx"
                out.parent.mkdir(parents=True, exist_ok=True)
                export_spreadsheet_xlsx(tid, out)
                entry["export_path"] = str(out)

            results.append(entry)

    return results

if __name__ == "__main__":
    items = walk_folder(FOLDER_ID)
    print(f"Found {len(items)} items")
    for it in items:
        print(f"- [{it['type']}] {it['title']} ({it['thread_id']}) -> {it.get('export_path','html in memory')}")
```

- `GET /1/folders/{id}` and mixed `children` shape are documented and mirrored by Quip’s own samples (their backup script recurses `folder_id` and `thread_id`). ([Quip](https://quip.com/api/reference "Quip Automation API Reference"), [GitHub](https://github.com/quip/quip-api/blob/master/samples/baqup/main.py?utm_source=chatgpt.com "quip-api/samples/baqup/main.py at master - GitHub"))

- Thread metadata and HTML endpoints are v2 and support **ID or secret path**. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- Spreadsheet export endpoint is v1 `/export/xlsx`. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- Rate-limit headers are from Quip’s docs. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

---

# Minimal VS Code repo scaffold

```
quip-folder-reader/
├─ .env.example
├─ README.md
├─ requirements.txt
└─ reader.py
```

**.env.example**

```
QUIP_TOKEN=your_token_here
QUIP_BASE=https://platform.quip.com
QUIP_FOLDER_ID=your_folder_id
```

**requirements.txt**

```
requests>=2.32.0
python-dotenv>=1.0.1
```

**README.md (snippet)**

```md
# Quip Folder Reader

Reads all Quip documents/spreadsheets from a given folder (recurses subfolders),
prints metadata, pulls HTML for docs, and exports spreadsheets as .xlsx.

## Setup
1. Create a Personal Access Token or API key (Admin Console).  
   See: Automation API → **Authentication** / **Get Access to Quip’s APIs**.  
2. `cp .env.example .env` and fill values.
3. `pip install -r requirements.txt`
4. `python reader.py`

### Notes
- Special folder IDs (desktop/private/etc.) are returned by `GET /1/users/current`.  
- Folder read: `GET /1/folders/{id}`; iterate `children` for `thread_id` and `folder_id`.  
- Document body: `GET /2/threads/{id}/html` (paged by `cursor`).  
- Spreadsheet export: `GET /1/threads/{id}/export/xlsx`.  
- Mind your rate limits & backoff (`X-*RateLimit*` headers).
```

(Those bullets map directly to the official Automation API pages.) ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

---

# How to pick the right folder ID (3 common approaches)

1. **You already know it** (from URL): the 12-char “secret path” or the folder ID; both are accepted in different endpoints. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

2. **From your user record:** `GET /1/users/current` → use `private_folder_id`, `starred_folder_id`, etc. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

3. **From a parent “root” you control:** store that ID in config and recurse with `/1/folders/{id}` (children → subfolders). Quip’s own sample backup code does exactly this recursion. ([GitHub](https://github.com/quip/quip-api/blob/master/samples/baqup/main.py?utm_source=chatgpt.com "quip-api/samples/baqup/main.py at master - GitHub"))

---

## Gotchas & tips

- **Folders aren’t strict trees.** Because they’re “tag-like”, a thread may appear in more than one folder; dedupe by thread ID if you aggregate. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- **Chats in folders:** exclude them by default (`include_chats=false`) unless you explicitly need them. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- **Large docs:** the HTML endpoint is **paginated** with `cursor`. Keep calling until `next_cursor` is empty. ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

- **Spreadsheets inside docs vs. standalone spreadsheets:** the XLSX export is for **standalone** spreadsheets; for sheets embedded in a document, fetch the document’s HTML or export to PDF (with caveats). ([Quip](https://quip.com/api/reference "Quip Automation API Reference"))

---

Perfect 👍 — here’s an **ASCII tree view** of the same mock Quip folder. This gives you a visual of how the recursion walks through folders and threads.

---

# 🌲 Example Quip Folder Tree

```
📂 Example Team Folder (FOLDER123)
├── 📄 DOCUMENT: 🚀 Launch Checklist  (abcdEfGHijkL)
│     └── html pulled via /2/threads/{id}/html
│
├── 📊 SPREADSHEET: Sales Data Q1  (mnoPQrsTUvwx)
│     └── exported to exports/Sales_Data_Q1.xlsx
│
└── 📂 Subfolder: Projects (FOLDER456)
      └── 📄 DOCUMENT: Nested Doc (zyxWVutSRqpo)
            └── html pulled via /2/threads/{id}/html
```

---

## 🔑 Notation Conventions Illustrated

- **Folder IDs**: `FOLDER123`, `FOLDER456`
- **Thread IDs**: `abcdEfGHijkL`, `mnoPQrsTUvwx`, `zyxWVutSRqpo` (12-char mixed-case IDs)
- **Types**: DOCUMENT vs. SPREADSHEET (from `/2/threads/{id}` API)
- **Actions**:

  - DOCUMENT → fetch HTML body
  - SPREADSHEET → export to `.xlsx`

---

👉 With this view, you can quickly see how recursion works:

- Start at `FOLDER123` → iterate children
- If `thread_id`: fetch thread (doc/spreadsheet)
- If `folder_id`: recurse into that folder

---

Would you like me to **extend this tree** with an example of a **chat thread** and a **slide thread**, so you see the full range of Quip types in one folder?
