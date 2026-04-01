---
name: project-overview
description: "得物掘金工具 Framework Overview"
---

# 得物掘金工具 (DewuGoJin Tool)

**得物平台自动化视频发布系统** - A multi-agent Claude Code framework for the 得物掘金工具 project.

## Technology Stack

- **Frontend**: Electron + React + TypeScript + Vite + Ant Design
- **Backend**: Python FastAPI + SQLAlchemy
- **Automation**: Playwright (browser automation)
- **Media**: FFmpeg (video processing)
- **Database**: SQLite

## Available Agents

| Agent | Description |
|-------|-------------|
| `/frontend-expert` | React/TypeScript/Electron specialist |
| `/backend-expert` | Python/FastAPI specialist |
| `/browser-automation` | Playwright automation specialist |
| `/video-processing` | FFmpeg/AI clip specialist |
| `/database-expert` | SQLAlchemy/data modeling specialist |

## Available Skills

| Skill | Description |
|-------|-------------|
| `/code-review` | Review code quality, security, and best practices |
| `/browser-automation` | Implement Playwright browser automation workflows |
| `/video-processing` | Implement FFmpeg video processing and AI clip detection |

## Project Structure

```
dewugojin/
├── frontend/                      # Electron + React frontend
│   ├── src/
│   │   ├── pages/               # Page components
│   │   ├── components/           # Shared components
│   │   └── services/             # API services
│   └── electron/                  # Electron config
├── backend/                        # Python FastAPI backend
│   ├── api/                       # API routes
│   ├── models/                    # Database models
│   ├── services/                  # Business services
│   └── core/                      # Configuration
└── data/                          # Media storage
    ├── video/
    ├── audio/
    ├── cover/
    ├── text/
    └── topic/
```

## Quick Start

```bash
# Start development (recommended)
.\dev.bat

# Or manually:
# Terminal 1: Backend
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev:electron
```

## Access Points

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development Tips

1. Use `/frontend-expert` for React/TypeScript questions
2. Use `/backend-expert` for FastAPI/Python questions
3. Use `/browser-automation` for Playwright issues
4. Use `/video-processing` for FFmpeg questions
5. Use `/code-review` to review your code before committing

## Related Documents

- [README.md](README.md) - Main project documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details
