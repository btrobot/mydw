---
name: code-review
description: "Review code quality, security, and best practices"
argument-hint: "[file paths or directories to review]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
---

When this skill is invoked:

1. **Parse arguments** — Identify files/directories to review
2. **Check prerequisites** — Verify files exist
3. **Read context** — Load project rules and patterns
4. **Begin workflow** — Start with Phase 1: Gather Context

---

### Phase 1: Gather Context

**Goal**: Understand the code to review

**Steps**:
1. Identify the file types (Python/TypeScript/JavaScript)
2. Load relevant project rules from `.claude/rules/`
3. Check for existing tests
4. Understand the purpose of the code

---

### Phase 2: Review Code

**Goal**: Perform comprehensive code review

**Steps**:
1. **Correctness**: Does the code do what it claims?
2. **Security**: Are there potential vulnerabilities?
3. **Performance**: Are there obvious performance issues?
4. **Style**: Does it follow project conventions?
5. **Tests**: Is there adequate test coverage?

---

### Phase 3: Generate Report

**Goal**: Provide actionable feedback

**Steps**:
1. Document findings with severity (MUST FIX/SHOULD/NIT)
2. Provide specific examples and suggestions
3. Suggest references to relevant rules

---

### Quality Checks

Review against these standards:

- [ ] Code is correct and does what it claims
- [ ] No security vulnerabilities (injection, XSS, etc.)
- [ ] No obvious performance issues
- [ ] Follows project style conventions
- [ ] Error handling is appropriate
- [ ] Tests are present and adequate

---

### Output Format

```
## Code Review Report

### Files Reviewed
- `path/to/file1.ts`
- `path/to/file2.py`

### Issues Found

#### MUST FIX (Blocking)
1. **[File:Line]** Description
   - Impact: [What could go wrong]
   - Suggestion: [How to fix]

#### SHOULD FIX (Important)
1. **[File:Line]** Description
   - Suggestion: [How to improve]

#### Nitpicks
1. **[File:Line]** Minor issue

### Summary
- Critical Issues: X
- Important Issues: X
- Nitpicks: X

### Recommendations
1. [Overall recommendation]
```

---

### Next Steps

1. Address MUST FIX issues first
2. Review SHOULD FIX issues when convenient
3. Consider nitpicks for future improvements
4. Re-review after fixes if needed

---

### Related Skills

- `/frontend-expert` — Frontend-specific reviews
- `/backend-expert` — Backend-specific reviews
- `/browser-automation` — Browser automation code reviews

### Involves

- User review and approval of recommendations
