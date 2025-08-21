
* Lists your **special folders** (private/desktop/starred) from `GET /1/users/current`
* Lets you **pick a folder** and previews its **child folders/threads**
* Lets you **paste any Quip URL** and extracts the **12-char slug** (thread/folder ID)
* Can **emit a ready-to-paste .env block** (and optionally write `.env`)

---

# Drop-in files

## `scripts/discover.py`

```python
#!/usr/bin/env python3
import os, re, json, sys, argparse
import requests
from dotenv import load_dotenv

URL_RE = re.compile(r"https?://(?:\w+\.)?quip\.com/([A-Za-z0-9]{10,14})")

def slug_from_url(url: str) -> str | None:
    m = URL_RE.search(url or "")
    return m.group(1) if m else None

def api(base, token, method, path, **kwargs):
    url = f"{base}{path}"
    h = kwargs.pop("headers", {})
    h["Authorization"] = f"Bearer {token}"
    for _ in range(6):
        r = requests.request(method, url, headers=h, timeout=30, **kwargs)
        if r.status_code in (200, 201):
            return r
        if r.status_code in (429, 500, 502, 503, 504):
            # polite backoff: short linear; robust enough for discovery
            import time
            time.sleep(2)
            continue
        r.raise_for_status()
    r.raise_for_status()

def get_current_user(base, token):
    return api(base, token, "GET", "/1/users/current").json()

def get_folder(base, token, folder_id, include_chats=False):
    return api(base, token, "GET", f"/1/folders/{folder_id}",
               params={"include_chats": str(include_chats).lower()}).json()

def get_thread(base, token, thread_id):
    return api(base, token, "GET", f"/2/threads/{thread_id}").json()

def print_special_folders(u):
    print("\n== Special folders from /1/users/current ==")
    for k in ("private_folder_id", "desktop_folder_id", "starred_folder_id", "trash_folder_id"):
        v = u.get(k)
        if v:
            print(f"- {k}: {v}")

def preview_folder(base, token, fid, limit=10):
    print(f"\n== Preview for folder {fid} ==")
    f = get_folder(base, token, fid)
    children = f.get("folder", f).get("children", [])  # tolerate two shapes
    shown = 0
    for ch in children:
        if shown >= limit:
            print(f"... (+{len(children)-limit} more)")
            break
        if "folder_id" in ch:
            print(f"📂 folder_id: {ch['folder_id']}")
            shown += 1
        elif "thread_id" in ch:
            tid = ch["thread_id"]
            tmeta = get_thread(base, token, tid).get("thread", {})
            print(f"📄 thread_id: {tid}  [{tmeta.get('type','?')}]  {tmeta.get('title','(no title)')}")
            shown += 1
    return children

def emit_env_block(base, token, folder_id=None, doc_thread_id=None, sheet_thread_id=None):
    lines = [
        f"QUIP_BASE={base}",
        f"QUIP_TOKEN={token}",
        f"QUIP_FOLDER_ID={folder_id or ''}",
        f"QUIP_DOC_THREAD_ID={doc_thread_id or ''}",
        f"QUIP_SHEET_THREAD_ID={sheet_thread_id or ''}",
    ]
    return "\n".join(lines) + "\n"

def write_env_file(content, path=".env", force=False):
    if os.path.exists(path) and not force:
        print(f"Refusing to overwrite existing {path}. Use --force to replace.")
        return
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote {path}")

def main():
    parser = argparse.ArgumentParser(description="Discover Quip env values.")
    parser.add_argument("--base", default=os.getenv("QUIP_BASE", "https://platform.quip.com"),
                        help="Quip API base (default: https://platform.quip.com)")
    parser.add_argument("--token", default=os.getenv("QUIP_TOKEN"), help="Quip Personal Access Token")
    parser.add_argument("--folder", help="Folder ID/slug to preview (optional)")
    parser.add_argument("--from-url", help="Extract ID from a Quip URL (thread or folder)")
    parser.add_argument("--emit-env", action="store_true", help="Print a .env block with discovered values")
    parser.add_argument("--write-env", action="store_true", help="Write .env based on discovered values")
    parser.add_argument("--force", action="store_true", help="Overwrite .env if present")
    parser.add_argument("--limit", type=int, default=10, help="Max children to preview")
    args = parser.parse_args()

    load_dotenv()
    base = args.base.rstrip("/")
    token = args.token
    if not token:
        print("ERROR: Provide QUIP_TOKEN in env or --token.", file=sys.stderr)
        sys.exit(1)

    # URL → ID helper
    extracted = None
    if args.from-url:
        extracted = slug_from_url(args.from-url)
        if extracted:
            print(f"Extracted ID from URL: {extracted}")
        else:
            print("No 12-char slug found in URL.")

    # Show special folders
    cur = get_current_user(base, token)
    print_special_folders(cur)

    # If user passed a folder or we extracted one, preview it
    chosen_folder = args.folder or extracted or cur.get("desktop_folder_id") or cur.get("private_folder_id")
    if chosen_folder:
        preview_folder(base, token, chosen_folder, limit=args.limit)
    else:
        print("\nNo folder to preview. Pass --folder <id> or --from-url <url>.")

    # Quick examples: pick first doc & sheet if present (for convenience)
    doc_id = None
    sheet_id = None
    if chosen_folder:
        children = get_folder(base, token, chosen_folder).get("folder", {}).get("children", [])
        for ch in children:
            if "thread_id" in ch:
                meta = get_thread(base, token, ch["thread_id"]).get("thread", {})
                ttype = meta.get("type")
                if ttype == "DOCUMENT" and not doc_id:
                    doc_id = meta.get("id")
                if ttype == "SPREADSHEET" and not sheet_id:
                    sheet_id = meta.get("id")
                if doc_id and sheet_id:
                    break

    if args.emit-env or args.write-env:
        env_block = emit_env_block(base, "REDACTED_TOKEN", chosen_folder, doc_id, sheet_id)
        print("\n# --- .env block (token redacted) ---")
        print(env_block)
        if args.write-env:
            # Write real token to file
            real_block = emit_env_block(base, token, chosen_folder, doc_id, sheet_id)
            write_env_file(real_block, path=".env", force=args.force)

if __name__ == "__main__":
    main()
```

## `Makefile` additions

```make
discover:
\tpython scripts/discover.py --emit-env

discover-url:
\tpython scripts/discover.py --from-url "$(URL)" --emit-env

discover-write:
\tpython scripts/discover.py --emit-env --write-env
```

## `README.md` (snippet)

```md
## 🔎 Bootstrap discovery

1) Ensure you already created your **Personal Access Token** and exported it:
```

export QUIP\_TOKEN=xxxxxxxxxxxxxxxx

```

2) Run discovery (prints special folders and previews a folder):
```

make discover

```

3) If you have a Quip URL, extract its ID:
```

make discover-url URL="[https://quip.com/3fs7B2leat8/TrackingDocument](https://quip.com/3fs7B2leat8/TrackingDocument)"

```

4) Emit a ready-to-use `.env` (and optionally write it):
```

make discover-write          # writes .env (uses detected folder/doc/sheet)

```
```

---

## How this helps you, fast

* **`QUIP_FOLDER_ID`**: discovered from your special folders or any URL you paste
* **`QUIP_DOC_THREAD_ID` / `QUIP_SHEET_THREAD_ID`**: auto-picked from the first doc/sheet in that folder (you can edit later)
* **`.env`**: generated for you (token redacted in console; real token written only if you pass `--write-env`)
