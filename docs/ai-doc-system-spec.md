# AI-Collaborative Documentation System Spec

> Version: 1.0.0 | Date: 2026-04-07
> Author: Tech Lead
> Status: Proposed

A specification for documentation systems optimized for AI Agent consumption. Designed for projects using multi-agent frameworks (Claude Code, Cursor, etc.) where agents need to discover, read, and trust documentation without human guidance.

---

## 1. Design Principles

| Principle | Rationale |
|-----------|-----------|
| Discovery over memorization | Agents start cold every session. They must find docs, not remember them. |
| Reference over narrative | Agents need lookup tables, not essays. Structured data > prose. |
| Single source of truth | Duplicate info drifts. One canonical location per fact. |
| Token budget awareness | Every doc an agent reads costs tokens. Smaller, focused docs beat monoliths. |
| Machine-parseable structure | Consistent headings, tables, and frontmatter enable reliable extraction. |
| Staleness is worse than absence | Wrong docs cause wrong code. Sync mechanisms are not optional. |

---

## 2. Document Discovery Architecture

### 2.1 The Problem

An AI agent starting a new session has no memory. It sees `CLAUDE.md` (or equivalent entry point) and must navigate from there to the exact document it needs. Without an explicit reference graph, the agent resorts to `Glob` + `Grep` across the entire repo — slow, token-expensive, and unreliable.

### 2.2 Three-Layer Discovery Model

```
Layer 1: Entry Point          CLAUDE.md (root)
              │
              ├── @ref → docs/system-architecture.md
              ├── @ref → docs/api-reference.md
              ├── @ref → .claude/rules/*.md
              │
Layer 2: Domain Entry Points  backend/CLAUDE.md, frontend/CLAUDE.md
              │
              ├── @ref → docs/data-model.md
              ├── @ref → docs/api-reference.md#accounts
              │
Layer 3: Inline References    Source code docstrings, schema comments
              │
              └── @see docs/adr/ADR-004-encryption.md
```

### 2.3 Reference Syntax

Use a simple, grep-able reference format in Markdown files:

```markdown
<!-- @ref docs/api-reference.md "API endpoint details" -->
<!-- @ref docs/data-model.md#account "Account table schema" -->
```

Rules:
- Place `@ref` tags in an HTML comment so they don't render but are searchable
- The path is always relative to project root
- Optional fragment (`#section`) points to a heading within the target
- Optional description in quotes tells the agent what it will find there
- Agent tooling can `Grep` for `@ref` to build a reference graph on demand

For source code, use language-native comments:

```python
# @see docs/adr/ADR-004-encryption.md — why AES-256-GCM
def encrypt_cookie(plaintext: str) -> str: ...
```

```typescript
// @see docs/api-reference.md#accounts — response shape
const useAccounts = () => useQuery({ ... })
```

### 2.4 Entry Point Structure

Every `CLAUDE.md` (root or subdirectory) MUST contain a `## References` section that acts as a table of contents for that scope:

```markdown
## References

| Document | Path | What it answers |
|----------|------|-----------------|
| System Architecture | docs/system-architecture.md | How the system is structured, why |
| API Reference | docs/api-reference.md | Endpoint params, responses, examples |
| Data Model | docs/data-model.md | Table schemas, field types, constraints |
| Dev Guide | docs/dev-guide.md | How to set up and run the project |
| ADRs | docs/adr/ | Why we chose X over Y |
```

For agent definition files (`.claude/agents/*.md`), add a `## Key References` section scoped to that agent's domain:

```markdown
## Key References

- `docs/api-reference.md` — API contracts this agent implements
- `docs/data-model.md` — Database schemas
- `backend/CLAUDE.md` — Backend dev environment setup
- `.claude/rules/python-coding-rules.md` — Coding standards
```

### 2.5 Agent Discovery Protocol

When an agent starts a task, it follows this lookup sequence:

```
1. Read CLAUDE.md (automatic — Claude Code injects this)
2. Read own agent definition (.claude/agents/{self}.md)
3. Read Key References listed in agent definition
4. If still missing info → Grep for @ref tags in relevant scope
5. If still missing → Grep source code for @see tags
6. Last resort → Glob + read source files directly
```

This is a convention, not enforced code. Agents follow it because the instructions in their definition files tell them to.

---

## 3. Document Catalog

### 3.1 What Documents a Project Needs

Not every project needs every document. The catalog below is organized by the question each doc answers.

#### Tier 1 — Every Project (answers "what does this system do and how do I work with it")

| Document | Path Convention | Format | Answers |
|----------|----------------|--------|---------|
| Project Entry | `CLAUDE.md` | Markdown + tables | Tech stack, structure, agent config, references |
| System Architecture | `docs/system-architecture.md` | Markdown + ASCII diagrams | Components, data flow, deployment topology |
| API Reference | `docs/api-reference.md` | Markdown tables | Endpoint signatures, params, responses, errors |
| Data Model | `docs/data-model.md` | Markdown tables | Table/collection schemas, field types, constraints, relationships |
| Dev Guide | `docs/dev-guide.md` | Markdown + code blocks | Environment setup, run commands, common workflows |

#### Tier 2 — Growing Projects (answers "why did we do it this way")

| Document | Path Convention | Format | Answers |
|----------|----------------|--------|---------|
| ADRs | `docs/adr/ADR-NNN-slug.md` | ADR template | Architecture decisions and their rationale |
| Domain CLAUDE.md | `{subdir}/CLAUDE.md` | Same as root | Subdirectory-specific setup, structure, conventions |
| Coding Rules | `.claude/rules/*.md` | Rule DSL | Language/framework-specific coding standards |
| Changelog | `CHANGELOG.md` | Keep a Changelog | What changed between versions |

#### Tier 3 — Team/Complex Projects (answers "how do we coordinate")

| Document | Path Convention | Format | Answers |
|----------|----------------|--------|---------|
| Agent Definitions | `.claude/agents/*.md` | Agent DSL | Agent roles, scopes, references |
| Coordination Rules | `.claude/rules/coordination-rules.md` | Rule DSL | Handoff protocol, conflict resolution |
| Test Strategy | `docs/testing-strategy.md` | Markdown | Test layers, coverage targets, how to run |
| Deployment Guide | `docs/deployment-guide.md` | Markdown + code blocks | Build, package, release process |

### 3.2 Document Format Standards

Every document MUST start with a metadata header:

```markdown
# [Title]

> Version: X.Y.Z | Updated: YYYY-MM-DD
> Owner: [agent-role or human name]
> Status: Draft | Active | Deprecated
```

Content rules:
- Use tables for structured data (agents parse tables more reliably than prose)
- Use code blocks for commands, schemas, examples
- Use ASCII diagrams over image references (agents can't see images)
- Keep each document under 500 lines. Split if larger.
- Use heading hierarchy consistently: `##` for sections, `###` for subsections
- No orphan documents — every doc must be reachable from a `CLAUDE.md` References table

### 3.3 API Reference Format

The API reference is the most frequently consulted document. Optimize for lookup:

```markdown
## [Module Name] — /api/[prefix]

### [METHOD] /api/[prefix]/[path]

[One-line description]

**Request:**

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| id | path | integer | yes | Resource ID |
| name | body | string | yes | Display name |

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "example",
  "status": "active"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| 404 | Resource not found |
| 409 | Duplicate resource |
```

For FastAPI projects: generate from OpenAPI schema. The `/openapi.json` endpoint is the source of truth; the Markdown file is a derived artifact.

### 3.4 Data Model Format

```markdown
## [TableName]

[One-line business description]

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| name | String(100) | not null, unique | Display name |
| secret | Text | nullable | Encrypted (AES-256-GCM) |

**Relationships:**
- TableName 1:N OtherTable (via `other_table.table_id`)

**Indexes:**
- `ix_table_name` on `name`

**Notes:**
- `secret` field encrypted at rest, see ADR-004
```

For SQLAlchemy projects: semi-automate extraction from model definitions. Hand-annotate business descriptions and encryption markers.

### 3.5 ADR Format

```markdown
# ADR-NNN: [Title]

> Date: YYYY-MM-DD | Status: Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## Context

[What problem are we solving? What constraints exist?]

## Options Considered

### Option A: [Name]
- Pro: ...
- Con: ...

### Option B: [Name]
- Pro: ...
- Con: ...

## Decision

[Which option and why]

## Consequences

- [Positive consequence]
- [Negative consequence / trade-off]
- [Follow-up action needed]
```

ADR numbering: sequential, zero-padded to 3 digits. Slug in filename for discoverability: `ADR-004-aes-encryption.md`.

---

## 4. Document-Code Consistency

### 4.1 The Staleness Problem

Documentation drifts from code because:
1. Developers change code but forget to update docs
2. No mechanism detects the drift
3. Stale docs are worse than no docs — agents trust what they read

### 4.2 Consistency Strategies

#### Strategy A: Generate, Don't Write (preferred where possible)

| Document | Source of Truth | Generation Method |
|----------|----------------|-------------------|
| API Reference | FastAPI route decorators + Pydantic schemas | Script reads `/openapi.json`, outputs Markdown |
| Data Model (structure) | SQLAlchemy model classes | Script introspects models, outputs Markdown tables |
| Frontend API types | OpenAPI schema | hey-api / openapi-ts (already configured) |

Generated docs carry a header:

```markdown
<!-- AUTO-GENERATED from /openapi.json — do not edit manually -->
<!-- Regenerate: python scripts/gen-api-docs.py -->
<!-- Last generated: 2026-04-07T10:00:00Z -->
```

#### Strategy B: Co-locate with Code

For docs that can't be generated, place them as close to the code as possible:

| Instead of | Do this |
|------------|---------|
| Separate "backend setup" doc far from backend | `backend/CLAUDE.md` in the backend directory |
| Separate "frontend conventions" doc | `frontend/CLAUDE.md` in the frontend directory |
| Separate "encryption design" doc | `@see` comment in `crypto.py` pointing to ADR |

Proximity reduces drift because the developer sees the doc when editing the code.

#### Strategy C: Freshness Markers

Every non-generated document includes a `Version` and `Updated` date in its header. This enables:

1. Automated staleness detection: a script or hook can flag docs not updated in N days
2. Agent skepticism: if an agent sees `Updated: 2025-01-15` on a doc in a fast-moving project, it knows to verify against source code

#### Strategy D: Pre-Commit Hook Checks

Extend the existing `pre-commit.ts` hook to detect doc-code drift:

```
Trigger: file in backend/models/ modified
Check: docs/data-model.md updated in same commit?
Action: Warning (not block) — "Model changed but data-model.md not updated"

Trigger: file in backend/api/ modified
Check: docs/api-reference.md updated OR marked auto-generated?
Action: Warning — "API route changed, consider regenerating api-reference.md"
```

Implementation: pattern-match on staged file paths. This is lightweight — no AST parsing, just path checks.

#### Strategy E: Regeneration Commands

Provide simple commands that agents (or humans) can run:

```bash
# Regenerate API reference from running backend
python scripts/gen-api-docs.py > docs/api-reference.md

# Regenerate data model reference from SQLAlchemy models
python scripts/gen-data-model.py > docs/data-model.md
```

Agents can run these commands when they detect staleness or before starting a task that depends on these docs.

### 4.3 Consistency Matrix

| Document | Sync Strategy | Staleness Risk | Mitigation |
|----------|---------------|----------------|------------|
| API Reference | Generate from OpenAPI | Low | Regen script + pre-commit warning |
| Data Model | Semi-generate from models | Medium | Regen script + manual business notes |
| Dev Guide | Manual | Medium | Freshness marker + review on env changes |
| ADRs | Manual (write-once) | Low | ADRs rarely change after acceptance |
| System Architecture | Manual | High | Review quarterly or on major refactors |
| Coding Rules | Manual | Low | Rules change infrequently |
| Agent Definitions | Manual | Low | Change only when roles change |
| Changelog | Manual per release | Medium | Part of release checklist |

---

## 5. Token Budget Optimization

### 5.1 The Cost Model

Every document an agent reads consumes context window tokens. For a 200k context window:

| Document | Typical Size | Token Cost | Read Frequency |
|----------|-------------|------------|----------------|
| CLAUDE.md | 300 lines | ~3k tokens | Every session (auto) |
| Agent definition | 80 lines | ~800 tokens | Every agent invocation (auto) |
| Coding rules | 100 lines | ~1k tokens | Every session (auto via rules) |
| API Reference | 200-400 lines | ~3-5k tokens | On demand |
| Data Model | 150-300 lines | ~2-4k tokens | On demand |
| System Architecture | 300 lines | ~4k tokens | On demand |

### 5.2 Optimization Techniques

#### Technique 1: Layered Loading

Not all docs need to be read at session start. Structure docs in layers:

| Layer | When Loaded | Examples |
|-------|-------------|---------|
| Always | Session start (auto-injected) | CLAUDE.md, active rules, agent definition |
| On-demand | Agent reads when task requires | API reference, data model, ADRs |
| Rare | Only when specifically relevant | Sprint plans, old requirements, changelog |

The References table in CLAUDE.md acts as a menu — agents read the menu (cheap) and only load the full doc when needed.

#### Technique 2: Section Anchors

Large documents should use clear `##` headings so agents can read specific sections:

```markdown
## Accounts — /api/accounts        ← Agent can Grep for this heading
## Tasks — /api/tasks              ← and Read with offset/limit
## Materials — /api/materials
```

This lets an agent do `Grep "## Accounts"` then `Read file offset=N limit=50` instead of loading the entire document.

#### Technique 3: Summary + Detail Split

For large documents, provide a summary table at the top:

```markdown
## API Endpoints Summary

| Module | Prefix | Endpoints | Key Operations |
|--------|--------|-----------|----------------|
| Accounts | /api/accounts | 12 | CRUD, connect, health-check |
| Tasks | /api/tasks | 8 | CRUD, publish, batch |
| Materials | /api/materials | 6 | CRUD, upload, scan |

---

## Accounts — /api/accounts (detailed)
...
```

The agent reads the summary table (~20 lines) to orient, then dives into the specific section it needs.

#### Technique 4: Keep CLAUDE.md Lean

The root `CLAUDE.md` is loaded every session. It should contain:
- Tech stack (table)
- Project structure (tree, abbreviated)
- References table (links to detailed docs)
- Agent roster (table)
- Critical rules (brief)

It should NOT contain:
- Full architecture descriptions (link to `system-architecture.md`)
- Detailed coding standards (link to `.claude/rules/`)
- Sprint plans or task breakdowns (link to `docs/`)
- Lengthy process descriptions

Target: root CLAUDE.md under 200 lines / 2k tokens.

---

## 6. Implementation for DewuGoJin

### 6.1 Current State

| Aspect | Status | Gap |
|--------|--------|-----|
| Root CLAUDE.md | Exists, 298 lines | Too large (~3k tokens). Contains process details that belong in rules/docs. |
| Backend CLAUDE.md | Exists, 103 lines | Good size. Missing References section. |
| Frontend CLAUDE.md | Missing | No frontend entry point. |
| API Reference | Missing | Agents read source code every time. |
| Data Model | Missing | Only ER overview in system-architecture.md. |
| Dev Guide | Missing | Backend setup in backend/CLAUDE.md, frontend setup nowhere. |
| ADRs | 3 exist (007, 008, 015) | Gaps in early decisions (encryption, tech choices). |
| Agent References | No @ref sections | Agents have no doc pointers in their definitions. |
| Doc-code sync | None | No hooks, no generation scripts. |

### 6.2 Action Plan

#### Phase 1: Reference Wiring (effort: low, impact: high)

1. Add `## References` table to root `CLAUDE.md`
2. Add `## Key References` to each agent definition in `.claude/agents/*.md`
3. Add `## References` to `backend/CLAUDE.md`
4. Create `frontend/CLAUDE.md` with setup instructions + References

#### Phase 2: Missing Tier-1 Docs (effort: medium, impact: high)

5. Create `scripts/gen-api-docs.py` — generate `docs/api-reference.md` from OpenAPI
6. Create `scripts/gen-data-model.py` — generate `docs/data-model.md` from SQLAlchemy models
7. Create `docs/dev-guide.md` — unified setup guide (merge backend/CLAUDE.md content + add frontend)

#### Phase 3: Consistency Mechanisms (effort: medium, impact: medium)

8. Extend `.claude/hooks/pre-commit.ts` with doc-staleness warnings
9. Add `<!-- AUTO-GENERATED -->` headers to generated docs
10. Add `@see` comments to key source files (crypto.py, browser.py, main.py)

#### Phase 4: Backfill (effort: low, impact: low)

11. Backfill ADR-001 through ADR-006
12. Slim down root CLAUDE.md (move process details to coordination-rules.md)
13. Create CHANGELOG.md

### 6.3 Concrete File Changes

#### Root CLAUDE.md — Add References Section

```markdown
## References

| Document | Path | What it answers |
|----------|------|-----------------|
| System Architecture | docs/system-architecture.md | Component diagram, data flow, security |
| API Reference | docs/api-reference.md | All endpoints: params, responses, errors |
| Data Model | docs/data-model.md | Table schemas, fields, constraints |
| Dev Guide | docs/dev-guide.md | Environment setup, run commands |
| Requirements | docs/requirements-spec.md | Feature requirements, priorities |
| ADRs | docs/adr/ | Architecture decision records |
| Coordination Rules | .claude/rules/coordination-rules.md | Agent handoff protocol |
| Coding Rules | .claude/rules/ | Language-specific standards |
```

#### Agent Definition — Add Key References (example: backend-lead.md)

```markdown
## Key References

- `docs/api-reference.md` — API contracts (params, responses, errors)
- `docs/data-model.md` — Database table schemas and relationships
- `backend/CLAUDE.md` — Backend environment setup and project structure
- `.claude/rules/python-coding-rules.md` — Python coding standards
- `.claude/rules/security-rules.md` — Encryption and credential rules
- `docs/system-architecture.md#4-backend-architecture` — Backend architecture overview
```

#### frontend/CLAUDE.md — New File

```markdown
# Frontend Development

## Quick Start

```bash
cd frontend
npm install
npm run dev          # Vite dev server (browser only)
npm run electron:dev # Full Electron app
```

## Project Structure

```
frontend/src/
├── api/           # Auto-generated SDK (hey-api) — DO NOT edit .gen.ts files
├── components/    # Shared components (Layout, ConnectionModal, StatusBadge)
├── hooks/         # Data hooks (useAccount, useTask, useMaterial, ...)
├── pages/         # Route pages (Account, Task, Material, AIClip, ...)
├── providers/     # React Query provider
├── services/      # Axios instance
├── types/         # Shared TypeScript types
└── utils/         # Formatting helpers
```

## Key Conventions

- API client: auto-generated from OpenAPI. Regenerate: `npx openapi-ts`
- State: React Query for server state, local useState for UI state
- Components: functional + hooks, Ant Design 5
- Types: strict mode, no `any`

## References

| Document | Path | What it answers |
|----------|------|-----------------|
| TypeScript Rules | .claude/rules/typescript-coding-rules.md | Coding standards |
| Electron Rules | .claude/rules/electron-rules.md | Electron security patterns |
| System Architecture | docs/system-architecture.md#3-frontend-architecture | Frontend architecture |
| API Reference | docs/api-reference.md | Backend API contracts |
```

---

## 7. Applying to Other Projects

This spec is designed to be reusable. Here is the minimum viable documentation system for any project:

### Step 1: Create Entry Point

Create `CLAUDE.md` (or equivalent) with:
- Tech stack table
- Project structure tree
- References table pointing to all other docs

### Step 2: Identify Tier-1 Docs

Ask: "What questions do agents ask repeatedly that require reading source code?"

Common answers:
- "What API endpoints exist?" → API Reference
- "What does the database look like?" → Data Model
- "How do I run this?" → Dev Guide

### Step 3: Wire References

Add `@ref` tags and References tables so every doc is discoverable from the entry point within 2 hops.

### Step 4: Choose Sync Strategy Per Doc

For each document, pick one:
- Generate from code (best for API docs, type definitions)
- Co-locate with code (best for setup guides, conventions)
- Manual with freshness markers (best for architecture, ADRs)

### Step 5: Add Staleness Detection

Minimum viable: a pre-commit hook that warns when code in certain directories changes without corresponding doc updates.

---

## 8. Anti-Patterns

| Anti-Pattern | Why It Fails | Alternative |
|-------------|-------------|-------------|
| Monolithic architecture doc (1000+ lines) | Agents load entire doc, waste tokens, can't find specific info | Split by concern, use section anchors |
| Docs in a wiki (Notion, Confluence) | Agents can't access external URLs during coding | Keep docs in-repo as Markdown |
| README.md as the only doc | Too much crammed in, or too little to be useful | README for humans, CLAUDE.md for agents |
| Duplicating info across docs | Guaranteed drift | Single source + @ref links |
| Generating docs but never regenerating | Generated docs become stale just like manual ones | Regen scripts + pre-commit reminders |
| Over-documenting stable code | Wastes maintenance effort, adds token cost | Document boundaries and contracts, not internals |
| Images/diagrams without text equivalent | Agents can't interpret images | ASCII diagrams or structured text descriptions |

---

## Appendix A: Reference Tag Specification

### Markdown Files

```markdown
<!-- @ref path/to/doc.md "optional description" -->
<!-- @ref path/to/doc.md#section-anchor "optional description" -->
```

### Python Files

```python
# @see path/to/doc.md — brief reason
# @see docs/adr/ADR-004-encryption.md — encryption design rationale
```

### TypeScript Files

```typescript
// @see path/to/doc.md — brief reason
// @see docs/api-reference.md#accounts — response shape contract
```

### Rules

1. Path is always relative to project root
2. Use forward slashes (even on Windows)
3. Fragment anchors use lowercase-kebab-case matching the heading
4. Description is optional but recommended for non-obvious references
5. One `@ref` or `@see` per line
6. `@ref` for document-to-document links; `@see` for code-to-document links

### Discovery

Agents find references by:

```bash
# Find all document references
rg "@ref " --type md

# Find all code-to-doc references
rg "@see " --type py --type ts

# Find what references a specific doc
rg "api-reference" --type md --type py --type ts
```

## Appendix B: Freshness Check Script (Conceptual)

```python
"""
Check document freshness against related source files.
Run as: python scripts/check-doc-freshness.py
"""

WATCH_PAIRS = [
    # (source_glob, doc_path, max_drift_days)
    ("backend/api/**/*.py", "docs/api-reference.md", 7),
    ("backend/models/**/*.py", "docs/data-model.md", 7),
    ("backend/core/**/*.py", "docs/system-architecture.md", 30),
]

# For each pair:
# 1. Find most recent source file modification time
# 2. Compare against doc file modification time
# 3. If source is newer by more than max_drift_days, emit warning
```

This can be integrated into the pre-commit hook or run as a standalone CI check.
