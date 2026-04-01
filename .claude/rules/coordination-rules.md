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
  └── Project Manager (PM)
        └── Tech Lead
              ├── Frontend Lead
              │     └── UI Developer
              ├── Backend Lead
              │     ├── API Developer
              │     └── Automation Developer
              ├── QA Lead
              │     └── Test Engineer
              └── DevOps Engineer
```

## Vertical Delegation

### Rules

- PM MUST assign tasks to Tech Lead
- Tech Lead MUST assign tasks to Domain Leads
- Domain Leads SHOULD assign tasks to Developers
- complex decisions MUST escalate through hierarchy
- results MUST report back through hierarchy

### Prohibited

- Developers MUST NOT accept tasks directly from users (except simple tasks)
- Developers MUST NOT make cross-domain architecture decisions
- Developers MUST NOT skip Leads and report to Tech Lead directly

## Horizontal Collaboration

### Collaboration Matrix

| Agent | Collaborates With | Topics |
|-------|------------------|--------|
| Frontend Lead | Backend Lead | API contracts, Type definitions |
| Backend Lead | QA Lead | Test cases, Acceptance criteria |
| Automation Dev | Backend Lead | API endpoints, Webhooks |
| QA Lead | DevOps | CI/CD, Test automation |
| Tech Lead | Security Expert | Security architecture |

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
| Feature design | PM | Unclear requirements |
| Security issues | Security Expert | Vulnerabilities |
| Test standards | QA Lead | Coverage requirements |
| Resource conflicts | PM | Developer conflicts |
| No consensus | PM | Horizontal negotiation failed |

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

## Change Propagation

### Trigger Conditions

Changes affecting multiple domains MUST trigger propagation:

- API contract changes
- Shared data type changes
- Cross-domain dependencies
- Configuration changes

### Propagation Flow

```
1. Change initiated → Notify PM
2. PM assesses impact → Identify affected parties
3. PM coordinates → Confirm change plan
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
- [ ] Backend Lead
- [ ] QA Lead
- [ ] DevOps

### Timeline
- Plan confirmed: [Date]
- Implementation: [Date]
- Testing passed: [Date]

### Status
- [ ] Frontend: Pending
- [ ] Backend: Pending
- [ ] QA: Pending
```

## Cross-Domain Changes

### Default Prohibitions

Unless explicitly authorized:

| Prohibition | Description |
|------------|-------------|
| Frontend → Backend | Cannot modify API routes or services |
| Backend → Frontend | Cannot modify React components or stores |
| Developer → Cross-domain | Can only modify own domain files |
| QA → Implementation | Can only modify test files |

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
| Implementation | Lead/Developer | Specific implementation |
| Security | Security Expert | Security measures |
| Testing | QA Lead | Coverage requirements |

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
| Skip hierarchy | PM corrects and documents |
| Cross-domain change | Rollback and re-coordinate |
| Not documented | Require documentation |
| Conflict not escalated | PM介入介入 |

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
