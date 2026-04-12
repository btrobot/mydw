# AI-Collaborative Documentation System Spec

> Version: 2.0.0 | Updated: 2026-04-07
> Author: Tech Lead
> Status: Active

A specification for documentation systems optimized for AI Agent consumption. Designed for projects using multi-agent frameworks where agents need to discover, read, and trust documentation without human guidance.

---

## 1. Design Principles

| Principle | Rationale |
|-----------|-----------|
| Discovery over memorization | Agents start cold every session. Entry points must link to everything an agent might need. |
| Reference over narrative | Agents need lookup tables, not essays. Structured data (tables, code blocks) > prose. |
| Single source of truth | Duplicate info drifts. One canonical location per fact. |
| Token budget awareness | Every doc costs context tokens. Smaller, focused docs beat monoliths. |

---

## 2. Document Discovery

### 2.1 Entry Point References Table

Every `CLAUDE.md` (root or subdirectory) MUST contain a `## References` section — a table of contents for that scope:

```markdown
## References

| Document | Path | What it answers |
|----------|------|-----------------|
| System Architecture | docs/archive/reference/system-architecture.md | How the system is structured |
| API Reference | docs/archive/reference/api-reference.md | Endpoint params, responses, errors |
| Data Model | docs/archive/reference/data-model.md | Table schemas, field types, constraints |
| Dev Guide | docs/dev-guide.md | How to set up and run the project |
| ADRs | docs/adr/ | Why we chose X over Y |
```

This is the primary discovery mechanism. Agents read the References table (cheap) and only load the full doc when needed.

### 2.2 Agent Key References

Agent definition files (`.claude/agents/*.md`) SHOULD include a `## Key References` section scoped to that agent's domain:

```markdown
## Key References

- `docs/archive/reference/api-reference.md` -- API contracts this agent implements
- `docs/archive/reference/data-model.md` -- Database schemas
- `backend/CLAUDE.md` -- Backend dev environment setup
- `.claude/rules/python-coding-rules.md` -- Coding standards
```

### 2.3 How Agents Find Docs

```
1. Read CLAUDE.md (auto-injected at session start)
2. Read own agent definition (.claude/agents/{self}.md)
3. Read Key References listed in agent definition
4. If still missing info -> Glob/Grep source files directly
```

No special tags or reference syntax needed. Agents already have Glob and Grep — they can find anything in the repo. The References tables just make it faster.

---

## 3. Document Catalog

### 3.1 Tier 1 -- Every Project

Answers: "what does this system do and how do I work with it"

| Document | Path Convention | Answers |
|----------|----------------|---------|
| Project Entry | `CLAUDE.md` | Tech stack, structure, agent config, references |
| System Architecture | `docs/archive/reference/system-architecture.md` | Components, data flow, deployment topology |
| API Reference | `docs/archive/reference/api-reference.md` | Endpoint signatures, params, responses, errors |
| Data Model | `docs/archive/reference/data-model.md` | Table/collection schemas, relationships |
| Dev Guide | `docs/dev-guide.md` | Environment setup, run commands |

### 3.2 Tier 2 -- Growing Projects

Answers: "why did we do it this way"

| Document | Path Convention | Answers |
|----------|----------------|---------|
| ADRs | `docs/adr/ADR-NNN-slug.md` | Architecture decisions and rationale |
| Domain CLAUDE.md | `{subdir}/CLAUDE.md` | Subdirectory-specific setup and conventions |
| Coding Rules | `.claude/rules/*.md` | Language/framework-specific standards |
| Changelog | `CHANGELOG.md` | What changed between versions |

### 3.3 Tier 3 -- Team/Complex Projects

Answers: "how do we coordinate"

| Document | Path Convention | Answers |
|----------|----------------|---------|
| Agent Definitions | `.claude/agents/*.md` | Agent roles, scopes, references |
| Coordination Rules | `.claude/rules/coordination-rules.md` | Handoff protocol, conflict resolution |
| Test Strategy | `docs/testing-strategy.md` | Test layers, coverage targets |
| Deployment Guide | `docs/deployment-guide.md` | Build, package, release process |

---

## 4. Document Format Standards

### 4.1 Metadata Header

Every document MUST start with:

```markdown
# [Title]

> Version: X.Y.Z | Updated: YYYY-MM-DD
> Owner: [agent-role or human name]
> Status: Draft | Active | Deprecated
```

### 4.2 Content Rules

- Use tables for structured data (agents parse tables more reliably than prose)
- Use code blocks for commands, schemas, examples
- Use ASCII diagrams over image references (agents can't see images)
- Keep each document under 500 lines. Split if larger.
- Use heading hierarchy consistently: `##` for sections, `###` for subsections
- No orphan documents -- every doc must be reachable from a References table

### 4.3 API Reference Format

Optimized for lookup:

```markdown
## [Module Name] -- /api/[prefix]

### [METHOD] /api/[prefix]/[path]

[One-line description]

**Request:**

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| id | path | integer | yes | Resource ID |

**Response:** `200 OK`

\```json
{ "id": 1, "name": "example" }
\```

**Errors:**

| Status | Condition |
|--------|-----------|
| 404 | Resource not found |
```

For FastAPI projects: the `/openapi.json` endpoint is the source of truth. Agents can read it directly when they need the latest contract.

### 4.4 Data Model Format

```markdown
## [TableName]

[One-line business description]

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| name | String(100) | not null, unique | Display name |

**Relationships:**
- TableName 1:N OtherTable (via `other_table.table_id`)

**Notes:**
- `secret` field encrypted at rest, see ADR-004
```

### 4.5 ADR Format

```markdown
# ADR-NNN: [Title]

> Date: YYYY-MM-DD | Status: Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## Context
[What problem are we solving?]

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
```

ADR numbering: sequential, zero-padded to 3 digits. Slug in filename: `ADR-004-aes-encryption.md`.

---

## 5. Document-Code Consistency

Three rules to keep docs from drifting:

### Rule 1: Freshness Headers

Every document includes `Version` and `Updated` date in its metadata header. This enables:
- Automated staleness detection — default threshold: 30 days for active projects (see `docs/doc-checklist.md` Section 3.1)
- Agent skepticism (if `Updated: 2025-01-15` on a fast-moving project, verify against source code)

### Rule 2: Pre-Commit Drift Detection

Extend pre-commit hooks to detect doc-code drift via path matching:

```
Trigger: file in backend/models/ modified
Check: docs/archive/reference/data-model.md updated in same commit?
Action: Warning (not block) -- "Model changed but data-model.md not updated"

Trigger: file in backend/api/ modified
Check: docs/archive/reference/api-reference.md updated in same commit?
Action: Warning -- "API route changed, consider updating api-reference.md"
```

Implementation: pattern-match on staged file paths. Lightweight -- no AST parsing.

### Rule 3: Co-locate When Possible

Place docs close to the code they describe:

| Instead of | Do this |
|------------|---------|
| Separate "backend setup" doc far from backend | `backend/CLAUDE.md` in the backend directory |
| Separate "frontend conventions" doc | `frontend/CLAUDE.md` in the frontend directory |

Proximity reduces drift because the developer sees the doc when editing the code.

### Consistency Matrix

| Document | Sync Strategy | Staleness Risk |
|----------|---------------|----------------|
| API Reference | Freshness header + pre-commit warning | Medium |
| Data Model | Freshness header + pre-commit warning | Medium |
| Dev Guide | Freshness header | Medium |
| ADRs | Write-once (rarely changes) | Low |
| System Architecture | Freshness header, review on major refactors | High |
| Coding Rules | Manual (changes infrequently) | Low |

---

## 6. Token Budget Optimization

### 6.1 Layered Loading

Not all docs need to be read at session start:

| Layer | When Loaded | Examples |
|-------|-------------|---------|
| Always | Session start (auto-injected) | CLAUDE.md, active rules, agent definition |
| On-demand | Agent reads when task requires | API reference, data model, ADRs |
| Rare | Only when specifically relevant | Sprint plans, changelog, old requirements |

### 6.2 Section Anchors

Large documents should use clear `##` headings so agents can read specific sections:

```markdown
## Accounts -- /api/accounts
## Tasks -- /api/tasks
## Materials -- /api/materials
```

Agent does `Grep "## Accounts"` then `Read file offset=N limit=50` instead of loading the entire document.

### 6.3 Summary + Detail Split

For large documents, provide a summary table at the top:

```markdown
## API Endpoints Summary

| Module | Prefix | Endpoints | Key Operations |
|--------|--------|-----------|----------------|
| Accounts | /api/accounts | 12 | CRUD, connect, health-check |
| Tasks | /api/tasks | 8 | CRUD, publish, batch |

---

## Accounts -- /api/accounts (detailed)
...
```

Agent reads the summary (~20 lines) to orient, then dives into the specific section.

### 6.4 Keep CLAUDE.md Lean

Root `CLAUDE.md` is loaded every session. It should contain:
- Tech stack (table)
- Project structure (abbreviated tree)
- References table
- Agent roster (table)
- Critical rules (brief)

Target: root CLAUDE.md under 200 lines / ~2k tokens.

---

## 7. Anti-Patterns

| Anti-Pattern | Why It Fails | Alternative |
|-------------|-------------|-------------|
| Monolithic architecture doc (1000+ lines) | Wastes tokens, hard to find specific info | Split by concern, use section anchors |
| Docs in a wiki (Notion, Confluence) | Agents can't access external URLs | Keep docs in-repo as Markdown |
| README.md as the only doc | Too much crammed in, or too little | README for humans, CLAUDE.md for agents |
| Duplicating info across docs | Guaranteed drift | Single source + References table links |
| Over-documenting stable code | Wastes maintenance effort | Document boundaries and contracts, not internals |
| Images/diagrams without text equivalent | Agents can't interpret images | ASCII diagrams or structured text |

---

## 8. Applying to Other Projects

Minimum viable documentation system for any project:

1. Create `CLAUDE.md` with tech stack table, project structure, and References table
2. Identify Tier-1 docs by asking: "What questions do agents ask repeatedly that require reading source code?"
3. Wire References so every doc is reachable from `CLAUDE.md` within 2 hops
4. Choose sync strategy per doc: freshness headers for manual docs, pre-commit warnings for high-drift-risk docs, co-location for setup guides
