
Below you’ll find:

1. Quick facts you’ll need (auth endpoints, VPC notes, cursors, OAS)

2. VS Code–first workflow (extensions + Claude usage)

3. A complete repo scaffold (files + contents)

4. Step-by-step run guide

5. Debugging playbook (practical tactics)

6. MCP/AI integration tips

I’ve included citations to Quip’s docs for anything non-obvious.

---

# 1) Quick facts (you’ll use these repeatedly)

- **Base host (cloud):** `https://platform.quip.com`  
    **VPC hosts:** `https://platform.<customername>.onquip.com` or `https://platform.quip-<customername>.com` (swap in all endpoints). ([Quip](https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"))

- **OAuth endpoints (cloud):**

  - Auth: `https://platform.quip.com/1/oauth/login`

  - Token: `https://platform.quip.com/1/oauth/access_token` ([Quip](https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"))

- **Personal Access Token (fastest to start):** `https://quip.com/dev/token` (use as `Authorization: Bearer ...`). ([UiPath Documentation](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/uipath-salesforce-quip-authentication?utm_source=chatgpt.com "Integration Service - Quip authentication"), [Quip](https://quip.com/blog/api?utm_source=chatgpt.com "Introducing the Quip API"))

- **OpenAPI (OAS) downloads** for the **Automation API – Current** (import anywhere, generate types/clients): Quip publishes OAS files. ([Quip](https://quip.com/dev/automation/documentation/current/openapi-info?utm_source=chatgpt.com "Quip Current Automation OpenAPI Info"), [Salesforce](https://help.salesforce.com/s/articleView?id=release-notes.oas_and_rate_limits.htm&language=en_US&release=236&type=5&utm_source=chatgpt.com "Get More Flexibility and Increased Stability with Quip's APIs"))

- **Pagination cursors** on some list endpoints **expire ~30 minutes**; fetch next page before expiry or request a new cursor. ([Quip](https://quip.com/dev/automation/documentation/all?utm_source=chatgpt.com "Automation API (All)"))

---

# 2) VS Code–first workflow (no Postman)

**Extensions to install in VS Code**

- **REST Client** (Huachao Mao) – run HTTP requests from `.http` files inside VS Code.

- **Python** (Microsoft) – debugging, linting, test discovery.

- **Claude for VS Code** – use Claude to write tests, add retries, generate types from OAS, etc.

- Optional: **Error Lens**, **EditorConfig**, **dotenv** syntax.

**How you’ll work**

- Use the `.http` file to send requests directly (handy for smoke tests).

- Use the Python client for real flows, retries, pagination.

- Ask **Claude** to:

  - “Generate Pydantic models from this OAS schema” (paste the relevant path schema from Quip OAS).

  - “Suggest unit tests for `QuipClient.list_threads()` with a fake 429 and backoff.”

  - “Add structured logs around auth refresh, and include request IDs from headers.”

---

# 3) Easy-to-run repo scaffold

> Copy/paste the tree, then the file contents below.

```
quip-vscode-starter/
├─ .env.example
├─ .gitignore
├─ README.md
├─ pyproject.toml
├─ uv.lock                # created on first sync if you use uv
├─ src/
│  ├─ quip_client.py
│  ├─ main.py
│  └─ utils/
│     └─ backoff.py
├─ tests/
│  └─ test_quip_client.py
├─ .vscode/
│  ├─ settings.json
│  ├─ launch.json
│  └─ tasks.json
└─ requests/
   └─ smoke.http
```

### `.env.example`

```ini
# Copy to .env and fill in
QUIP_BASE=https://platform.quip.com
# For personal token, set QUIP_TOKEN and leave OAuth empty
QUIP_TOKEN=

# OAuth (if you use client credentials or auth code flow)
QUIP_CLIENT_ID=
QUIP_CLIENT_SECRET=
QUIP_REDIRECT_URI=https://platform.quip.com
# If you already have a refresh token:
QUIP_REFRESH_TOKEN=
```

### `pyproject.toml` (works with `uv` or plain `pip`)

```toml
[project]
name = "quip-vscode-starter"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "httpx>=0.27.0",
  "python-dotenv>=1.0.1",
  "pydantic>=2.8.2",
  "tenacity>=8.5.0",
  "rich>=13.7.1",
]

[project.optional-dependencies]
dev = ["pytest>=8.2.0", "pytest-httpx>=0.30.0", "ruff>=0.5.6", "mypy>=1.10.0"]

[tool.ruff]
line-length = 100
```

### `src/utils/backoff.py`

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
import httpx

def retry_on_429_5xx():
    return retry(
        reraise=True,
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        wait=wait_exponential_jitter(initial=0.5, max=10.0),
        stop=stop_after_attempt(5),
    )
```

### `src/quip_client.py`

```python
import os, typing as t
import httpx
from dotenv import load_dotenv
from rich.console import Console
from utils.backoff import retry_on_429_5xx

load_dotenv()
console = Console()

def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name, default)
    return v if v and v.strip() else None

class QuipError(RuntimeError): ...

class QuipClient:
    def __init__(self,
                 base_url: str | None = None,
                 token: str | None = None,
                 timeout: float = 30.0):
        self.base = (base_url or _env("QUIP_BASE") or "https://platform.quip.com").rstrip("/")
        self.token = token or _env("QUIP_TOKEN")
        self.client = httpx.Client(timeout=timeout, headers=self._auth_headers())

    def _auth_headers(self) -> dict[str, str]:
        if not self.token:
            # (Optional) add OAuth refresh here using QUIP_CLIENT_ID/SECRET/REFRESH_TOKEN if desired.
            raise QuipError("No token found. Set QUIP_TOKEN or implement OAuth refresh.")
        return {"Authorization": f"Bearer {self.token}"}

    def _check(self, r: httpx.Response) -> None:
        # Surface Quip rate-limit and request ids if present
        rid = r.headers.get("x-request-id", "")
        if r.is_error:
            body = r.text[:2000]
            raise httpx.HTTPStatusError(
                f"{r.status_code} {r.request.method} {r.request.url} req={rid} body={body}",
                request=r.request, response=r
            )

    @retry_on_429_5xx()
    def _get(self, path: str, params: dict[str, t.Any] | None = None) -> dict:
        url = f"{self.base}{path}"
        r = self.client.get(url, params=params)
        self._check(r)
        return r.json()

    # ---- Example endpoints (confirm in your CURRENT Automation API OAS) ----
    def current_user(self) -> dict:
        return self._get("/1/users/current")

    def get_thread(self, thread_id: str) -> dict:
        return self._get("/1/threads/get", {"id": thread_id})

    def list_my_threads(self, count: int = 50, cursor: str | None = None) -> dict:
        params = {"count": count}
        if cursor:
            params["cursor"] = cursor
        return self._get("/1/threads/list", params)
```

> The example paths reflect common **current** Automation API patterns; validate exact names against the **Automation API (Current) OAS** before committing. ([Quip](https://quip.com/dev/automation/documentation/current/openapi-info?utm_source=chatgpt.com "Quip Current Automation OpenAPI Info"))

### `src/main.py`

```python
from quip_client import QuipClient, QuipError
from rich import print

def run():
    qc = QuipClient()
    me = qc.current_user()
    print({"current_user": me})

    # Example: iterate threads with ephemeral cursor
    page = qc.list_my_threads(count=25)
    print({"first_page_keys": list(page.keys())})
    next_cursor = page.get("next_cursor")
    if next_cursor:
        more = qc.list_my_threads(count=25, cursor=next_cursor)
        print({"second_page_keys": list(more.keys())})

if __name__ == "__main__":
    try:
        run()
    except QuipError as e:
        print({"error": str(e)})
```

### `tests/test_quip_client.py`

```python
import os
import pytest
from httpx import Response
from pytest_httpx import HTTPXMock
from src.quip_client import QuipClient

def test_current_user_success(httpx_mock: HTTPXMock):
    base = "https://platform.quip.com"
    os.environ["QUIP_TOKEN"] = "testtoken"
    httpx_mock.add_response(
        method="GET",
        url=f"{base}/1/users/current",
        json={"id":"abcd","name":"Test User"}
    )
    qc = QuipClient(base_url=base)
    assert qc.current_user()["name"] == "Test User"

def test_429_retries(httpx_mock: HTTPXMock):
    base = "https://platform.quip.com"
    os.environ["QUIP_TOKEN"] = "testtoken"
    httpx_mock.add_response(method="GET", url=f"{base}/1/users/current", status_code=429, text="slow down")
    httpx_mock.add_response(method="GET", url=f"{base}/1/users/current", json={"id":"x","name":"OK"})
    qc = QuipClient(base_url=base)
    assert qc.current_user()["name"] == "OK"
```

### `requests/smoke.http` (VS Code REST Client)

```http
### Who am I?
GET {{base}}/1/users/current
Authorization: Bearer {{token}}

### List my threads (first page)
GET {{base}}/1/threads/list?count=25
Authorization: Bearer {{token}}

### Get a thread by id
GET {{base}}/1/threads/get?id={{thread_id}}
Authorization: Bearer {{token}}

@base={{QUIP_BASE}}
@token={{QUIP_TOKEN}}
@thread_id=REPLACE_ME
```

> **Tip:** Create a `.vscode/settings.json` entry mapping `QUIP_BASE` and `QUIP_TOKEN` to your environment so REST Client picks them up.

### `.vscode/settings.json`

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  "terminal.integrated.env.osx": {
    "PYTHONUNBUFFERED": "1"
  },
  "rest-client.environmentVariables": {
    "$shared": {
      "QUIP_BASE": "${env:QUIP_BASE}",
      "QUIP_TOKEN": "${env:QUIP_TOKEN}"
    }
  }
}
```

### `.vscode/launch.json`

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run main.py",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

### `.vscode/tasks.json`

```json
{
  "version": "2.0.0",
  "tasks": [
    {"label":"Tests","type":"shell","command":"pytest -q","problemMatcher":[]},
    {"label":"Lint","type":"shell","command":"ruff check ."}
  ]
}
```

### `README.md` (excerpt you can keep)

```md
## Quickstart

1. `cp .env.example .env` and fill in `QUIP_TOKEN` (or your OAuth vars).
2. (Optional) Use `uv`:
   - `uv sync` (or `pip install -r <generated>`)
3. In VS Code:
   - Open the `.http` file and click **Send Request**.
   - Or press F5 to run `src/main.py`.
4. Run tests: `pytest -q`

### VPC
Set `QUIP_BASE` to your tenant (e.g., `https://platform.<customer>.onquip.com`). All endpoints use the same paths. :contentReference[oaicite:6]{index=6}

### Notes
- Some list cursors expire in ~30 minutes; request the next page promptly. :contentReference[oaicite:7]{index=7}
- Use the Automation API **Current** OAS to confirm endpoint names. :contentReference[oaicite:8]{index=8}
```

---

# 4) Step-by-step run guide (VS Code + Claude)

1. **Clone the scaffold** into VS Code.

2. `cp .env.example .env` → set:

    - `QUIP_BASE` (use your VPC host if applicable). ([Quip](https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"))

    - `QUIP_TOKEN` (personal token from **quip.com/dev/token**) or wire OAuth later. ([UiPath Documentation](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/uipath-salesforce-quip-authentication?utm_source=chatgpt.com "Integration Service - Quip authentication"))

3. Install deps

    - **With `uv`**: `uv sync` (or `uv pip install -e .[dev]`)

    - **Plain pip**: `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`

4. **Smoke test**: open `requests/smoke.http` → **Send Request** → you should get `200` and your user JSON.

5. **Run Python flow**: Press **F5** (VS Code) to run `src/main.py`.

6. **Ask Claude** (inside VS Code) to:

    - “Generate Pydantic models for `/1/threads/get` response from this OAS snippet.” (Paste schema from the **Current** Automation OAS.) ([Quip](https://quip.com/dev/automation/documentation/current/openapi-info?utm_source=chatgpt.com "Quip Current Automation OpenAPI Info"))

    - “Write unit tests that simulate a 429 then success for `current_user()`.”

---

# 5) Debugging playbook (practical)

**Auth & tenancy**

- **401**: expired/invalid token; regenerate personal token or refresh OAuth; ensure **Bearer** header present. ([Quip](https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"))

- **403**: scope/permission; confirm your token’s scopes and that your user can access the target thread/folder. ([Quip](https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"))

- **404 on VPC**: Using cloud host accidentally—switch every URL to your **VPC host**. ([Salesforce](https://help.salesforce.com/s/articleView?id=sf.quip_salesforce_vpc_setup.htm&language=en_US&type=5&utm_source=chatgpt.com "Connect Quip VPC to Salesforce"))

**Cursors & pagination**

- If a second-page call fails or returns nothing after a delay, your `next_cursor` may have **expired (~30 min)**. Start from the first page to obtain a new cursor. ([Quip](https://quip.com/dev/automation/documentation/all?utm_source=chatgpt.com "Automation API (All)"))

**Rate limits**

- On **429**, retry with exponential backoff (baked into `tenacity` here). Log Quip’s rate headers if present. ([Salesforce](https://help.salesforce.com/s/articleView?id=release-notes.oas_and_rate_limits.htm&language=en_US&release=236&type=5&utm_source=chatgpt.com "Get More Flexibility and Increased Stability with Quip's APIs"))

**VS Code visibility**

- Use the **REST Client**’s response view to inspect headers/body.

- Enable **Python logging** or add `rich` prints in `QuipClient._check()` to dump `x-request-id`.

**cURL parity (quick sanity)**

```bash
curl -i "$QUIP_BASE/1/users/current" -H "Authorization: Bearer $QUIP_TOKEN"
```

- Confirms environment + token quickly.

**Export/PDF quirks**

- Some export download URLs are **time-limited (e.g., ~72h)**—plan to download promptly in jobs. ([Salesforce](https://help.salesforce.com/s/articleView?id=004693512&language=en_US&type=1&utm_source=chatgpt.com "Bulk Export of Quip Content to PDF"))

**OAS-driven typing**

- Import the **Automation API (Current) OAS** and have Claude generate response models + client stubs—reduces 4xx due to shape/param mistakes. ([Quip](https://quip.com/dev/automation/documentation/current/openapi-info?utm_source=chatgpt.com "Quip Current Automation OpenAPI Info"))

---

# 6) MCP / AI integration tips

- **Deterministic envs**: Commit lockfiles (e.g., `uv.lock`) and pin `httpx`, `pydantic`.

- **Secret handling**: Store `QUIP_TOKEN` (or OAuth client creds/refresh token) in your MCP tool’s secret store; support both cloud and **VPC** bases. ([Quip](https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"))

- **Tool schemas from OAS**: Use the **OAS** as the contract feeding your MCP tool definition (endpoints, params, auth). ([Quip](https://quip.com/dev/automation/documentation/current/openapi-info?utm_source=chatgpt.com "Quip Current Automation OpenAPI Info"))

- **Robust pagination**: MCP actions that “list threads” should immediately consume `next_cursor` until exhausted (within the ~30-minute window). ([Quip](https://quip.com/dev/automation/documentation/all?utm_source=chatgpt.com "Automation API (All)"))

---

## References

- Quip API reference (auth URLs, VPC variants) and token details. ([Quip](https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"))

- Automation API **Current** OAS (download). ([Quip](https://quip.com/dev/automation/documentation/current/openapi-info?utm_source=chatgpt.com "Quip Current Automation OpenAPI Info"))

- Personal access token entry point. ([UiPath Documentation](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/uipath-salesforce-quip-authentication?utm_source=chatgpt.com "Integration Service - Quip authentication"), [Quip](https://quip.com/blog/api?utm_source=chatgpt.com "Introducing the Quip API"))

- Cursor expiry behavior. ([Quip](https://quip.com/dev/automation/documentation/all?utm_source=chatgpt.com "Automation API (All)"))

- Export/PDF link lifetime. ([Salesforce](https://help.salesforce.com/s/articleView?id=004693512&language=en_US&type=1&utm_source=chatgpt.com "Bulk Export of Quip Content to PDF"))

---

If you want, I can tailor the scaffold for **your VPC host**, add an **OAuth refresh helper** (client-credentials or auth-code), and insert **Claude-ready prompts** alongside each module (so you can one-click generate tests and types).
