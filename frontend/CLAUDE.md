# Frontend Development

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Frontend Lead
> Status: Active

Frontend entry point for DewuGoJin Electron + React application.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop | Electron 28 |
| UI Framework | React 18 |
| Language | TypeScript 5 (strict mode) |
| Build | Vite 5 |
| Components | Ant Design 5 |
| State | Zustand |
| API Client | @hey-api/client-fetch (auto-generated from OpenAPI) |
| Data Fetching | @tanstack/react-query |
| E2E Testing | Playwright |

---

## Quick Start

```bash
cd frontend
npm install
npm run dev              # Vite dev server at :5173
npm run dev:electron     # Full Electron app
npm run typecheck        # Type check
npm run api:generate     # Regenerate API client from backend OpenAPI
```

---

## Project Structure

```
frontend/
├── electron/
│   ├── main.js          # Electron main process
│   └── preload.js       # Context bridge (minimal API)
├── src/
│   ├── pages/           # Route-level page components
│   │   ├── Dashboard.tsx    # System overview
│   │   ├── Account.tsx      # Account management
│   │   ├── Task.tsx         # Task management
│   │   ├── Material.tsx     # Material management (video/copy/cover/audio)
│   │   ├── AIClip.tsx       # AI video clipping
│   │   └── Settings.tsx     # System settings
│   ├── components/      # Shared/reusable components
│   ├── services/
│   │   └── api.ts       # API service layer
│   ├── stores/          # Zustand state stores
│   ├── types/           # TypeScript type definitions
│   └── utils/           # Utility functions
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## Coding Standards

| Rule | Standard |
|------|----------|
| Types | No `any` -- use `unknown` + type guards |
| Components | Functional components + Hooks only |
| State | Zustand for global, useState for local |
| Error handling | `catch (error: unknown)` with AxiosError check |
| Styling | Ant Design tokens, no inline styles |

See `.claude/rules/typescript-coding-rules.md` for full rules.

### Error Handling Pattern

```typescript
catch (error: unknown) {
  if (axios.isAxiosError(error)) {
    message.error(error.response?.data?.detail || error.message)
  } else if (error instanceof Error) {
    message.error(error.message)
  } else {
    message.error('Operation failed')
  }
}
```

---

## References

| Document | Path | What it answers |
|----------|------|-----------------|
| API Reference | `docs/api-reference.md` | Backend endpoint contracts |
| Data Model | `docs/data-model.md` | Database schemas (for understanding API responses) |
| TypeScript Rules | `.claude/rules/typescript-coding-rules.md` | Coding standards |
| E2E Testing Rules | `.claude/rules/e2e-testing-rules.md` | Playwright test patterns |
| Dev Guide | `docs/dev-guide.md` | Full setup instructions |
