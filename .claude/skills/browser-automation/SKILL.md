---
name: browser-automation
description: "Implement Playwright browser automation workflows"
argument-hint: "[task description or workflow name]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

When this skill is invoked:

1. **Parse arguments** — Identify automation task
2. **Check prerequisites** — Verify Playwright is installed
3. **Read context** — Load existing browser services
4. **Begin workflow** — Start with Phase 1: Requirements Analysis

---

### Phase 1: Requirements Analysis

**Goal**: Understand the automation requirements

**Steps**:
1. Identify the target website and actions
2. Review existing patterns in `backend/services/browser_service.py`
3. Check current cookie/account management
4. Document required selectors and actions

---

### Phase 2: Design Automation Flow

**Goal**: Plan the automation implementation

**Steps**:
1. Map out step-by-step automation flow
2. Identify required Playwright operations
3. Design error handling and retry logic
4. Plan anti-detection measures

---

### Phase 3: Implement

**Goal**: Implement the automation

**Steps**:
1. Create browser service functions
2. Implement proper selectors with fallbacks
3. Add wait conditions and timeouts
4. Implement error handling and recovery
5. Add logging for debugging

---

### Phase 4: Test

**Goal**: Verify the automation works

**Steps**:
1. Test with sample data
2. Verify error handling
3. Check resource cleanup
4. Validate cookie management

---

### Quality Checks

Review against these standards:

- [ ] Selectors are reliable and specific
- [ ] Timeouts are appropriate
- [ ] Resources are properly cleaned up
- [ ] Error handling is comprehensive
- [ ] No sensitive data in logs
- [ ] Cookies are properly encrypted

---

### Output Format

```
## Browser Automation Report

### Task: [Task Name]

### Automation Flow
1. [Step description]
2. [Step description]

### Key Selectors
- [Selector name]: `[selector]`
- [Selector name]: `[selector]`

### Error Handling
- [Error type]: [Recovery strategy]

### Files Modified
- `backend/services/browser_service.py`

### Testing Notes
[Any manual testing required]
```

---

### Next Steps

1. Test automation manually
2. Monitor for anti-bot detection
3. Adjust selectors if website changes
4. Consider adding retry logic for flaky steps

---

### Related Skills

- `/browser-automation` agent — Browser automation specialist
- `/code-review` — Review automation code quality

### Involves

- `browser-automation` — Implement automation
- `backend-expert` — API integration
