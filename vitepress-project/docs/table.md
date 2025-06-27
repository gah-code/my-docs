
---

### ✅ Place this in: `docs/internal-docs/audit-system.md`

---

title: Internal Documentation Audit & Tagging System
description: A McKinsey-style content workflow for onboarding optimization.
sidebarDepth: 2
tags:

- documentation
- audit
- trainee-first
- onboarding

---

# 🧠 Internal Documentation Audit & Tagging System

This page helps you **audit and re-structure** internal documentation for a **trainee-first experience**.  
Use it to:

✅ Identify and prioritize essential content  
✅ Tag and categorize documentation for role-based filtering  
✅ Streamline onboarding from 3 months → 2 months

---

## 📋 1️⃣ Audit Table

| # | Doc Title | URL or Location | Purpose / Summary | Role Relevance | Learning Phase | Last Updated | SME / Owner | Action Needed | Tags |
|---|-----------|-----------------|--------------------|----------------|----------------|--------------|-------------|----------------|------|
| 1 | AEM Content Fragment Guide | /aem/cf-overview | Explains CF types, structure | Content Manager | Week 1–2 | 2024-12-10 | Priya K. | Break into 2 modules | aem, cf, content-manager |
| 2 | Metadata Best Practices | /seo/metadata | Details on adding SEO fields | Content Manager, SEO | Week 2–3 | 2023-11-02 | Sara L. | Extract steps + add checklist | seo, metadata |
| 3 | Localization Workflow | /aem/translation | Explains translation process | All Roles | Week 3–4 | 2024-10-01 | Localization Team | Add visual flowchart | translation, workflow |
| 4 | Tagging Policy | /guidelines/tags | List of tag naming conventions | Content Manager | Optional | 2021-06-22 | Unknown | Needs SME review | tags, policy |
| 5 | AEM Troubleshooting FAQ | /faq/aem-issues | Covers common authoring issues | All Roles | Month 2+ | 2024-01-15 | John H. | Link in advanced section | aem, troubleshooting |
| 6 | Content Publishing SOP | /process/publishing | SOP for content releases | Content Manager, QA | Week 4+ | 2023-09-12 | Ops Team | Condense into “first publish” guide | publishing, sop |

---

## 🏷️ 2️⃣ Tagging Matrix

> **Tip:** Use 3–5 tags per document to enable filtering and structured dashboards.

### 👥 Role Tags

| Tag | Description |
|-----|-------------|
| `content-manager` | For Content Managers |
| `qa` | For QA and reviewers |
| `developer` | For technical integration |
| `all-roles` | Relevant to everyone |

### 🛠️ Task Type Tags

| Tag | Description |
|-----|-------------|
| `how-to` | Step-by-step instructions |
| `checklist` | Task-oriented lists |
| `reference` | Deep reference guides |
| `walkthrough` | Guided examples |
| `faq` | Common questions |
| `workflow` | Multi-step processes |

### 🧩 System / Tool Tags

| Tag | Description |
|-----|-------------|
| `aem` | AEM-specific content |
| `contentful` | Contentful guides |
| `confluence` | Confluence usage |
| `metadata` | SEO and tagging |
| `localization` | Multilingual workflows |

### 📅 Learning Stage Tags

| Tag | Description |
|-----|-------------|
| `day-1` | Required on first day |
| `week-1` | First week essentials |
| `week-2` | Deeper onboarding |
| `month-1` | Advanced skills |
| `advanced` | Post-onboarding |

### 📘 Status Tags

| Tag | Description |
|-----|-------------|
| `needs-review` | Requires SME check |
| `verified` | Up-to-date and approved |
| `draft` | In progress |
| `archived` | Legacy reference only |

---

## 🧠 3️⃣ Example Tagged Document

**Doc Title:** _How to Create a New AEM Content Fragment_  
**Tags:** `content-manager`, `how-to`, `aem`, `week-1`, `verified`  
**Learning Objective:** Enable new hires to confidently create and publish a CF  
**Action:** Break reference guide into a 5-step walkthrough with screenshots

---

## 🛠️ 4️⃣ Using This System in Obsidian (or offline)

1. **Track** progress in the audit table  
2. **Filter** docs by tag in your note tool  
3. **Link** individual notes using consistent naming  
4. **Update** status tags as SME reviews occur

---

```md


## 🔍 5️⃣ Example Dataview-Style Query (Obsidian)

While VitePress doesn't run queries, here’s a reference for use in Obsidian:

```dataview
table Doc Title, Role Relevance, Learning Phase, Last Updated, Action Needed, Tags
from ""
where contains(Tags, "aem")
sort Last Updated desc
````

---

## 📦 What to Do Next

- 📁 Create a folder like `/internal-docs/modules/` for each document
- 📄 Use consistent frontmatter on each page to store metadata (tags, owner, review-date)
- 🔁 Set up a recurring review loop every 3–6 months to verify and refresh content

---

Would you like me to generate a **per-document template** (with YAML frontmatter) for each module now?
