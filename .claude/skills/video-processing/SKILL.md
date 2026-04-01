---
name: video-processing
description: "Implement FFmpeg video processing and AI clip detection"
argument-hint: "[task description or video operation]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

When this skill is invoked:

1. **Parse arguments** — Identify video processing task
2. **Check prerequisites** — Verify FFmpeg is installed
3. **Read context** — Load existing AI clip service
4. **Begin workflow** — Start with Phase 1: Requirements Analysis

---

### Phase 1: Requirements Analysis

**Goal**: Understand the video processing requirements

**Steps**:
1. Identify input/output video formats
2. Review existing patterns in `backend/services/ai_clip_service.py`
3. Check FFmpeg command patterns
4. Document quality requirements

---

### Phase 2: Design Processing Pipeline

**Goal**: Plan the video processing implementation

**Steps**:
1. Break down into FFmpeg operations
2. Plan for progress reporting
3. Design error handling for corrupt files
4. Consider batch processing if needed

---

### Phase 3: Implement

**Goal**: Implement the video processing

**Steps**:
1. Create or update FFmpeg commands
2. Implement video analysis functions
3. Add progress reporting
4. Implement error handling
5. Add cleanup of temporary files

---

### Phase 4: Test

**Goal**: Verify video processing works

**Steps**:
1. Test with sample video files
2. Verify output quality
3. Check progress reporting
4. Validate error handling

---

### Quality Checks

Review against these standards:

- [ ] FFmpeg commands are tested and working
- [ ] Error handling for corrupt files
- [ ] Progress reporting implemented
- [ ] Temporary files are cleaned up
- [ ] Output quality meets requirements
- [ ] Memory usage is reasonable

---

### Output Format

```
## Video Processing Report

### Task: [Task Name]

### Processing Pipeline
1. [Operation]: `ffmpeg [command]`
2. [Operation]: `ffmpeg [command]`

### Input/Output
- Input: [Format, resolution, duration]
- Output: [Format, resolution, quality]

### Performance
- Estimated processing time: [Duration]
- Memory usage: [MB/GB]

### Files Modified
- `backend/services/ai_clip_service.py`
- `backend/api/ai.py`

### Testing Notes
[Any manual testing required]
```

---

### Next Steps

1. Test with various video formats
2. Monitor performance with large files
3. Consider GPU acceleration if available
4. Add batch processing support if needed

---

### Related Skills

- `/video-processing` agent — Video processing specialist
- `/code-review` — Review FFmpeg code quality

### Involves

- `video-processing` — Implement processing
- `backend-expert` — API integration
