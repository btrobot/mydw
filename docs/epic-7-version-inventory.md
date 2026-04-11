# Epic 7 Version Inventory

> PR3 checked-in artifact  
> 目的：明确用户可见版本元信息的 canonical source 与同步范围，并说明哪些 package-manager metadata 不属于用户可见 canonical source。

## Canonical version source

- `backend/core/config.py`
- constant: `APP_VERSION`

当前 canonical version：

- `0.2.0`

## User-visible version surfaces that must stay in sync

| Surface | File | Sync rule |
|---|---|---|
| README displayed version | `README.md` | must match `APP_VERSION` |
| FastAPI app version | `backend/main.py` | must read `settings.APP_VERSION` |
| backend root metadata | `backend/main.py` | must return `settings.APP_VERSION` |
| frontend package version | `frontend/package.json` | must match `APP_VERSION` for Electron app version |
| Electron about/version string | `frontend/electron/main.ts` | must display `app.getVersion()` |
| tracked Electron runtime JS mirror | `frontend/electron/main.js` | must stay aligned with TS source in repo |
| CLI package version | `frontend/scripts/cli/package.json` | must match `APP_VERSION` |
| CLI `--version` output | `frontend/scripts/cli/src/index.ts` | must match `APP_VERSION` |
| exported OpenAPI info.version | `frontend/openapi.local.json` | regenerated/exported from backend version |

## Explicit non-canonical metadata

这些不作为“用户可见 canonical source”管理：

- `frontend/package-lock.json`
- `frontend/bun.lock`
- `frontend/scripts/cli/package-lock.json`
- third-party dependency versions inside lockfiles

原因：

- 它们记录的是包管理解析结果
- 不是当前产品/构建面对用户展示的版本答案
- 可以在 grep inventory 中出现不同版本数字，但不构成 PR3 失败

## Grep checklist

推荐检查命令：

```bash
rg -n "0\.1\.0|0\.2\.0|APP_VERSION|version=" README.md backend frontend -g '!frontend/node_modules' -g '!frontend/dist'
```

Pass condition:

- 所有用户可见版本 surfaces 收口到 `APP_VERSION`
- 仍残留的版本号若只存在于 lockfile / third-party metadata，必须被明确归类为非 canonical metadata
