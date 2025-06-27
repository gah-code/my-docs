# Unified Audit

---

### 📘 `docs/audit-workflow.md`

---

### title: Unified Audit + Extraction Workflow

description: A McKinsey-inspired workflow for streamlining onboarding documentation.
sidebarDepth: 2
---

# 🛠️ Unified Audit + Extraction Workflow

> **Objective:** Cut onboarding from **3 → 2 months** by auditing current docs and extracting “just-what-matters” training modules.

---

## 🔍 McKinsey’s Top-Down Approach

This enhanced workflow lets you:

✔️ **Audit** existing docs  
✔️ **Extract & repurpose** critical learning modules  

It layers **McKinsey-style prioritization** over a practical content pipeline:
_Discover → Select → Transform → Deploy._

---

## 1️⃣ Content Inventory & Audit (Discover → Prioritize)

| # | Doc Title | Source / Link | Purpose | Role Relevance | Learning Phase | Last Updated | SME / Owner | Audit Status | Tags |
|---|-----------|---------------|---------|----------------|----------------|--------------|-------------|--------------|------|
| 1 | AEM Content Fragment Guide | `/aem/cf-overview` | Explains CF types | Content Manager | Week 1–2 | 2024-12-10 | Priya K. | Keep & Extract | aem, cf, how-to |
| 2 | Metadata Best Practices | `/seo/metadata` | Add SEO fields | CM, SEO | Week 2–3 | 2023-11-02 | Sara L. | Condense | seo, metadata, checklist |

**Audit Status values:**

- **Keep & Extract** – high-value, transform into trainee module  
- **Condense** – cut fluff, keep essentials  
- **Archive** – use only as reference  
- **Merge** – combine with similar content  

---

## 2️⃣ Extraction Planning (Top-Down Selection)

| Source Doc | Target Module(s) | Extract Goal | Chunk Owner | Due | Status |
|------------|------------------|--------------|--------------|------|--------|
| AEM CF Guide | • Create a CF<br>• Tag & Metadata | Pull 5-step how-to + screenshots | @Gilbert | 07-05 | 🚧 |
| Metadata Best Practices | • CF Metadata Checklist | Turn bullets into checklist | @Sara | 07-07 | ⏳ |

> 🧩 **Chunk Owner** = person rewriting the module.  
> 🔖 Aim for ≤ 2 pages, ≤ 10 min read time per module.

---

## 3️⃣ Extraction Template (Transform)

```md
---
tags: content-manager, how-to, aem, week-1, draft
source: /aem/cf-overview
extracted-from-line: 35-72
owner: @Gilbert
review-date: 2025-07-10
---

# 🔧 {{MODULE TITLE}}

## 🎯 Learning Goal

By the end of this task, you can **create and save a basic CF** in AEM.

## ✅ Prerequisites

- Logged in to AEM Author

## 📝 Step-by-Step

1. **Navigate** to _Assets → Files → Content Fragments_  
2. Click **Create → Content Fragment**  
3. Select **`CF-Basic` model**  
4. Fill required fields → **Save**  
5. Press **Publish** to make live

## 💡 Common Pitfalls

- Forgetting to select correct model  
- Missing mandatory metadata

## 🔗 Related

- [Tag & Metadata a CF](./cf-tagging.md)  
- AEM Reference Doc › line 120–180

## 🕒 Last Reviewed: {{review-date}} | 👤 Owner: {{owner}}
````

---

## 4️⃣ Tagging Matrix (Classify Modules)

| Category  | Tag Examples                         |
| --------- | ------------------------------------ |
| Role      | `content-manager`, `qa`, `developer` |
| Task Type | `how-to`, `checklist`, `faq`         |
| System    | `aem`, `metadata`                    |
| Learning  | `week-1`, `week-2`, `month-1`        |
| Status    | `draft`, `needs-review`, `verified`  |

---

## 5️⃣ Automated Views (Trainee Dashboards)

While VitePress doesn’t support dynamic queries like Obsidian’s Dataview, you can simulate dashboards by manually creating filtered lists:

### 📑 Week 1 – Content Manager Modules

- [Create a Content Fragment](./modules/create-cf.md)
- [Tag & Metadata a CF](./modules/cf-tagging.md)

### ❗ Docs Still in Draft

- [Metadata Best Practices](./modules/cf-metadata.md) — _Needs Review (due 07-07)_
- [Rich Text Limitations](./modules/rte-guidelines.md) — _Draft (due 07-10)_

---

## 6️⃣ Continuous Improvement Loop (Maintain)

| Trigger                   | Automation                                      |
| ------------------------- | ----------------------------------------------- |
| Review date reached       | Templater script → ping SME via Slack           |
| Doc tagged `needs-review` | Kanban “Doc Refresh” in Jira                    |
| New AEM release           | Checklist → grep impacted `aem` + `how-to` tags |

---

## 7️⃣ Roll-Up Metrics (Measure Impact)

- ✅ % of modules **verified** vs. total
- 📉 Reduction in **duplicate Slack questions**
- 📆 Avg. onboarding days (from HR LMS)
- ⭐ Trainee feedback ≥ 4★ on “clarity” rating

---

## ✅ End-to-End Flow Summary

1. **Inventory** docs → mark audit status
2. **Plan** extraction slices
3. **Transform** using template
4. **Tag** with consistent taxonomy
5. **Surface** modules via filtered lists
6. **Review** + maintain
7. **Measure** impact

---

## 📌 Next Steps

- ➕ Copy this note to `/docs/audit-workflow.md`
- ➕ Create a `/docs/modules/` folder for templates
- ➕ Link content from `/docs/index.md` or sidebar

![Flowchart](/images/audit.png)

---
