
# Where to Get Your **Quip Personal Access Token**

1. Sign in to your Quip account in your browser.
2. Navigate to: **`https://quip.com/dev/token`**
3. Click **“Get Personal Access Token”**, then copy the token displayed.
   ([Quip][1], [UiPath Docs][2])

This token is what you’ll stash in your `.env` as `QUIP_TOKEN`.

---

### How to Find **Folder and Thread IDs**

#### From Quip URLs

* \*\*Thread (document/spreadsheet)\*\*: In a Quip URL like
  `https://quip.com/3fs7B2leat8/TrackingDocument`
  the "12‑character slug" (`3fs7B2leat8`) is the **secret path**—equivalent to the `thread_id` or `id`.
  ([Quip][1])

* **Folder**: If you're inside a folder URL like
  `https://quip.com/N5aaOTih0VYy/TeamFolder`,
  that same slug (`N5aaOTih0VYy`) is the **folder secret path**.
  ([Quip][1])

* Some APIs (e.g., `Get Folder`, `Get Thread`) accept either the **id** from their JSON responses or the `secret_path` from the URL.
  ([Quip][1])

---

#### Via the API (programmatic discovery)

* Call `GET /1/users/current` to see special folder IDs like `private_folder_id`, `desktop_folder_id`.

* Call `GET /1/folders/{id}` to list child `thread_id`s and `folder_id`s.
  ([Quip][1])

* The **first** `folder_id` returned via certain API endpoints (e.g., `get_folder`) is often your “company root” folder.
  ([Stack Overflow][3])

---

### Quick Lookup Table

| **Env Key**                   | **How to Find It**                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------- |
| `QUIP_TOKEN`                  | Visit `https://quip.com/dev/token`, click **Get Personal Access Token**. ([UiPath Docs][2]) |
| `QUIP_FOLDER_ID`              | Find it in your browser’s URL when viewing a folder (12-char slug). ([Quip][1])             |
| `QUIP_DOC_THREAD_ID`          | From document URL: same slug in the URL or via `Get Thread` API. ([Quip][1])                |
| `QUIP_SHEET_THREAD_ID`        | Same as above, but for spreadsheet thread URL.                                              |
| Special folder IDs (optional) | Use `GET /1/users/current`, which returns `private_folder_id`, etc. ([Quip][1])             |

---

### Summary & Next Steps

* **Personal Access Token** → grab it via `https://quip.com/dev/token`
* **Folder ID** → copy the 12-char slug from your folder’s URL (or call the API if you prefer dynamic discovery)
* **Document/Spreadsheet Thread ID** → same process via thread URL or via API

Once populated into your `.env`, your scaffold (with the walk, ingest, analyze modules) can start doing its magic—walking folders, appending content, validating ingestion, and analyzing structure.

Let me know if you’d like help automating this discovery (e.g., Bootstrap code to list available threads/folders from your user account)!

[1]: https://quip.com/api/reference?utm_source=chatgpt.com "Quip Automation API Reference"
[2]: https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/uipath-salesforce-quip-authentication?utm_source=chatgpt.com "Integration Service - Quip authentication"
[3]: https://stackoverflow.com/questions/54661096/using-the-quip-api-how-can-you-get-a-list-of-all-threads?utm_source=chatgpt.com "Using the Quip API, how can you get a list of all threads?"
