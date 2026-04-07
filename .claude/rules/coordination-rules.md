---
paths:
  - "production/**"
  - ".claude/**"
---

# Coordination Rules

Multi-Agent collaboration rules ensuring efficient coordination and conflict resolution.

> This is a **Process Rule** covering collaboration between agents.

## Agent Hierarchy

```
用户 (Product Owner)
  └── Tech Lead (opus)
        ├── Frontend Lead (sonnet)
        │     └── UI Designer (sonnet)
        ├── Backend Lead (sonnet)
        │     └── Automation Developer (sonnet)
        ├── QA Lead (sonnet)
        ├── Security Expert (sonnet)
        └── DevOps Engineer (sonnet)
```

## Vertical Delegation

### Rules

- User MUST assign tasks to Tech Lead for complex/cross-domain work
- Tech Lead MUST assign tasks to Domain Leads
- Domain Leads MAY delegate to specialists (e.g., Backend Lead → Automation Developer)
- Complex decisions MUST escalate through hierarchy
- Results MUST report back through hierarchy

### Prohibited

- Specialists MUST NOT accept tasks directly from users (except simple tasks)
- Specialists MUST NOT make cross-domain architecture decisions
- Specialists MUST NOT skip Leads and report to Tech Lead directly

## Horizontal Collaboration

### Collaboration Matrix

| Agent | Collaborates With | Topics |
|-------|------------------|--------|
| Frontend Lead | Backend Lead | API contracts, Type definitions |
| Frontend Lead | UI Designer | Page specs, Layout templates, Design review |
| Backend Lead | QA Lead | Test cases, Acceptance criteria |
| Backend Lead | Automation Developer | Playwright/FFmpeg scripts, API endpoints |
| QA Lead | DevOps Engineer | CI/CD, Test automation |
| Frontend Lead | DevOps Engineer | Frontend build configuration |
| Tech Lead | Security Expert | Security architecture |
| Security Expert | Backend Lead | Encryption, credential protection |

### Rules

- agents MAY discuss and propose suggestions
- agents MUST NOT make decisions for other domains
- collaboration results SHOULD be documented

## Conflict Resolution

### Escalation Path

| Conflict Type | Escalate To | Description |
|--------------|-------------|-------------|
| Technical architecture | Tech Lead | API design, DB schema |
| Code quality | Tech Lead | Review failures |
| Feature design | User | Unclear requirements |
| Security issues | Security Expert | Vulnerabilities |
| Test standards | QA Lead | Coverage requirements |
| Resource conflicts | User | Agent conflicts |
| No consensus | Tech Lead | Horizontal negotiation failed |

### Escalation Format

```markdown
## Escalation Report

### Conflict
[Clear description of conflict]

### Views
- **Agent A**: [View and reasoning]
- **Agent B**: [View and reasoning]

### Impact
- [Impact on project]

### Suggestion
[Proposed solution]

### Request
[What leadership should do]
```

## Agent Handoff Protocol

When delegating work from one agent to another, the caller MUST provide a structured handoff to ensure the receiving agent has sufficient context.

### Handoff Format

The main session (or delegating agent) MUST include these fields in the agent prompt:

```markdown
## Handoff

**From**: [caller agent name]
**To**: [target agent name]
**Task**: [one-line summary of what to accomplish]

### Context
[2-5 sentences: why this task exists, what has been decided so far, any relevant design/architecture choices]

### Constraints
- [constraint 1: e.g., must use existing API pattern]
- [constraint 2: e.g., cannot modify shared types without frontend-lead approval]

### Input Artifacts
- [file or decision the receiving agent should read first]

### Expected Output
- [concrete deliverable: e.g., "implemented endpoint at backend/api/xxx.py"]
- [quality bar: e.g., "passes typecheck, follows Pydantic validation"]
```

### Rules

- Handoffs MUST flow through the hierarchy (User → Tech Lead → Domain Lead → Specialist)
- The `Context` section MUST NOT exceed 500 words — link to files instead of duplicating content
- The `Constraints` section MUST include cross-domain boundaries if applicable
- If the receiving agent needs output from a parallel agent, the handoff MUST state what to wait for

### Parallel Handoff Sync Gate

When multiple agents are delegated in parallel:

1. Main session launches agents with individual handoff prompts
2. Each agent completes and returns results
3. Main session (or Tech Lead) performs **integration check** before proceeding:
   - Are the outputs compatible? (e.g., frontend types match backend response)
   - Any conflicts between parallel decisions?
   - Update `active.md` with combined results
4. Only after sync gate passes → proceed to next phase

### Handoff Failure

#### Failure Detection

An agent execution is considered **failed** when any of the following occur:

| Failure Type | Detection | Example |
|-------------|-----------|---------|
| **Timeout** | Agent hits maxTurns without completing the task | Complex implementation exceeds 25 turns |
| **Wrong output** | Deliverable does not match Expected Output in handoff | Asked for API endpoint, got only a design doc |
| **Scope violation** | Agent modifies files outside its Directory Scope | Backend Lead edits frontend components |
| **Quality failure** | Output fails typecheck, lint, or violates coding rules | TypeScript `any` types, Python `print()` |
| **Blocked** | Agent reports it cannot proceed due to missing info or dependency | Needs API contract that hasn't been defined |

#### Common Failure Patterns and Fixes

| Pattern | Root Cause | Fix |
|---------|-----------|-----|
| Agent asks too many clarifying questions | Handoff Context too vague | Refine: add specific requirements to Context |
| Agent produces partial implementation | Task too large for maxTurns budget | Split into sub-tasks, delegate separately |
| Agent modifies wrong files | Directory Scope not stated in handoff | Refine: add Constraints with explicit file scope |
| Agent output conflicts with parallel agent | Missing sync gate | Wait for parallel agent, then re-delegate with its output as Input Artifact |

#### Recovery Flow

1. Main session diagnoses root cause: unclear prompt? wrong agent? environment issue?
2. Options (in order of preference):
   - **Refine**: adjust the handoff prompt and re-delegate to the same agent
   - **Reroute**: delegate to a different agent better suited for the task
   - **Absorb**: main session handles the task directly
3. **Retry limit**: MUST NOT retry the same agent with the same prompt more than 2 times. After 2 failures, escalate (Reroute or Absorb)
4. Record failure in `active.md` Agent Handoffs table with Status=`failed` and Outcome=`[reason]`

## Change Propagation

### Trigger Conditions

Changes affecting multiple domains MUST trigger propagation:

- API contract changes
- Shared data type changes
- Cross-domain dependencies
- Configuration changes

### Propagation Flow

```
1. Change initiated → Notify Tech Lead
2. Tech Lead assesses impact → Identify affected agents
3. Tech Lead coordinates → Confirm change plan
4. Implementation → Complete schedule
5. Tracking → Confirm completion
```

### Change Notification Template

```markdown
## Change Notification

### Change Description
[What changed]

### Impact Scope
- [ ] Frontend Lead
- [ ] UI Designer
- [ ] Backend Lead
- [ ] Automation Developer
- [ ] QA Lead
- [ ] Security Expert
- [ ] DevOps Engineer

### Timeline
- Plan confirmed: [Date]
- Implementation: [Date]
- Testing passed: [Date]

### Status
- [ ] Frontend Lead: Pending
- [ ] Backend Lead: Pending
- [ ] Automation Developer: Pending
- [ ] QA Lead: Pending
- [ ] Security Expert: Pending
- [ ] DevOps Engineer: Pending
```

## Cross-Domain Changes

### Default Prohibitions

Unless explicitly authorized:

| Prohibition | Description |
|------------|-------------|
| Frontend Lead → Backend | Cannot modify API routes or services |
| Backend Lead → Frontend | Cannot modify React components or stores |
| Automation Developer → Cross-domain | Can only modify automation-scoped files |
| QA Lead → Implementation | Can only modify test files |
| DevOps Engineer → Application | Can only modify CI/CD and config files |
| UI Designer → Implementation | Can only modify docs/page-specs/ and docs/ui-templates.md |

### Authorization Process

To make cross-domain changes:

1. Request authorization from domain Lead
2. Explain reason and scope
3. Receive written confirmation
4. Document authorization source

## Decision Rules

### Decision Types

| Type | Decision Maker | Description |
|------|---------------|-------------|
| Product | User | Feature scope, priority |
| Technical architecture | Tech Lead | System design, API contracts |
| Frontend implementation | Frontend Lead | Component structure, state management |
| UI design | UI Designer | Layout templates, page specs, design review |
| Backend implementation | Backend Lead | API implementation, database design |
| Automation | Automation Developer | Browser/video automation |
| Security | Security Expert | Security measures |
| Testing | QA Lead | Coverage requirements |
| Deployment | DevOps Engineer | CI/CD, build configuration |

### Decision Flow

```
1. Question → Understand the problem
2. Options → Propose 2-3 options
3. Analysis → Analyze trade-offs
4. Decision → Decision maker chooses
5. Document → Log to session state
```

## State Management

### Session State File

Location: `production/session-state/active.md`

### Update Triggers

| Trigger | Content |
|---------|---------|
| Sprint start | Sprint goals, task assignments |
| Task start | Current task, owner |
| Task completion | Mark done, record results |
| Decision made | Log to decision log |
| Risk identified | Record risk and mitigation |
| Sprint end | Summary, prepare next Sprint |

### Status Block Format

```markdown
<!-- STATUS -->
Epic: [Current Epic]
Feature: [Current Feature]
Task: [Current Task]
Owner: [Current Owner]
<!-- /STATUS -->
```

## Validation Rules

### Before Committing

- [ ] Changes reviewed by relevant Lead
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Session state updated
- [ ] No blocking issues from other domains

### Violation Handling

| Violation | Action |
|-----------|--------|
| Skip hierarchy | Tech Lead corrects and documents |
| Cross-domain change | Rollback and re-coordinate |
| Not documented | Require documentation |
| Conflict not escalated | Tech Lead intervenes |

## Rationale

These rules ensure:
- Clear responsibility assignment
- Efficient information flow
- Proper escalation of conflicts
- Traceable decision making
- Coordinated changes across domains

## Related Rules

- `commit-rules.md` — Commit standards
- `code-review-rules.md` — Review checklist
- `python-coding-rules.md` — Backend implementation
- `typescript-coding-rules.md` — Frontend implementation
- `security-rules.md` — Security requirements
