# DewuGoJin Tool

> Version: 2.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Active

Dewu platform automated video publishing system -- multi-agent collaborative framework.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Electron 28 + React 18 + TypeScript 5 + Vite 5 + Ant Design 5 + Zustand |
| Backend | Python FastAPI + SQLAlchemy + aiosqlite |
| Automation | Patchright (Playwright fork, 反检测) |
| Media | FFmpeg (video processing) |
| Security | AES-256-GCM (cookie encryption), PBKDF2HMAC (key derivation) |

## Project Structure

```
dewugojin/
├── frontend/              # Electron + React (see frontend/CLAUDE.md)
│   └── src/
│       ├── pages/         # Page components
│       ├── components/    # Shared components
│       ├── services/      # API service layer
│       └── stores/        # Zustand state
├── backend/               # Python FastAPI (see backend/CLAUDE.md)
│   ├── api/               # Route handlers
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── utils/             # Utilities (crypto.py)
├── docs/                  # Project documentation
├── production/            # Session state & logs
└── .claude/               # Agent framework
    ├── agents/            # Agent definitions
    ├── skills/            # Skill workflows
    ├── hooks/             # Lifecycle hooks
    └── rules/             # Coding standards
```

## Agent Roster

```
User (Product Owner)
  └── Tech Lead (opus)
        ├── Frontend Lead (sonnet)
        ├── Backend Lead (sonnet)
        │     └── Automation Developer (sonnet)
        ├── QA Lead (sonnet)
        ├── Security Expert (sonnet)
        └── DevOps Engineer (sonnet)
```

## Platform Rules (Windows)

| Rule | Detail |
|------|--------|
| Shell | bash (Git Bash) -- use Unix syntax |
| Hooks | bash -> bun (TypeScript) |
| Encoding | Use Grep/Read tools for Chinese content; no inline Chinese in Bash |
| Tools | Use built-in Read/Edit/Grep/Glob instead of shell equivalents |

## Coding Standards (Summary)

| Domain | Key Rules |
|--------|-----------|
| Python | Type annotations, loguru (not print), Pydantic v2, async/await |
| TypeScript | Strict mode, no `any`, functional components + Hooks, Zustand |
| Security | AES-256-GCM for credentials, no secrets in code, Pydantic validation |

## Collaboration Protocol

**Task flow**: Question -> Options -> Decision -> Draft -> Approval

| Rule | Description |
|------|-------------|
| Vertical delegation | Complex decisions flow through hierarchy |
| Horizontal collaboration | Same-level agents negotiate, don't bind |
| Conflict escalation | Tech issues -> Tech Lead; Security -> Security Expert |
| Cross-domain prohibition | No modifying other domain's code without authorization |
| Retry limit | Max 2 retries per prompt, then reroute or absorb |

## Session State

**File**: `production/session-state/active.md` -- the live checkpoint.

Update after: design approval, architecture decisions, milestones, test results, task start/complete/block.

Compress at ~60-70% context usage. Read `active.md` to recover after compression.

## References

| Document | Path | What it answers |
|----------|------|-----------------|
| System Architecture | docs/system-architecture.md | Component diagram, data flow |
| API Reference | docs/api-reference.md | All endpoints, params, responses |
| Data Model | docs/data-model.md | Table schemas, relationships |
| Dev Guide | docs/dev-guide.md | Environment setup, run commands |
| Frontend Entry | frontend/CLAUDE.md | Frontend tech stack, structure |
| Backend Entry | backend/CLAUDE.md | Backend setup, venv, commands |
| Coordination Rules | .claude/rules/coordination-rules.md | Handoff protocol, conflict resolution |
| Python Rules | .claude/rules/python-coding-rules.md | Python coding standards |
| TypeScript Rules | .claude/rules/typescript-coding-rules.md | TypeScript coding standards |
| Security Rules | .claude/rules/security-rules.md | Encryption, input validation |
| API Design Rules | .claude/rules/api-design-rules.md | REST conventions, response models |
| Code Review Rules | .claude/rules/code-review-rules.md | Review checklist, severity levels |
| Commit Rules | .claude/rules/commit-rules.md | Commit message format |
| Doc System Spec | docs/ai-doc-system-spec.md | Documentation standards |
| Doc Checklist | docs/doc-checklist.md | Documentation quality verification |
| Usage Guide | .claude/docs/usage-guide.md | Multi-agent usage examples |

## Available Skills

| Skill | Command | Primary User |
|-------|---------|-------------|
| Code Review | `/code-review` | tech-lead, frontend-lead, backend-lead |
| Security Scan | `/security-scan` | security-expert |
| Architecture Review | `/architecture-review` | tech-lead |
| Sprint Plan | `/sprint-plan` | -- |
| Task Breakdown | `/task-breakdown` | -- |
| Bug Report | `/bug-report` | qa-lead |
| Release Checklist | `/release-checklist` | qa-lead |
