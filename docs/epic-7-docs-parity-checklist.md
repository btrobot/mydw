# Epic 7 Docs Parity Checklist

> PR1 checked-in artifact  
> 目的：确保新 baseline 文档不是“又一份脱离代码的总结”。

## 当前需要对齐的高价值真相

- [ ] `schedule-config` canonical source = `ScheduleConfig`
- [ ] `publish status` = scheduler runtime truth
- [ ] `task semantics` = collection-based authoritative model
- [ ] `settings` truth 已按 startup-env / runtime-config / read-only 收口
- [ ] `topic relation` truth 已按 relation-first / JSON-fallback 收口
- [ ] Phase 6 剩余 JSON 字段结论已可被引用

## 文档职责检查

- [ ] `current-architecture-baseline.md` 只做总入口，不复制 runtime facts 全量细节
- [ ] `current-runtime-truth.md` 继续作为 canonical fact inventory
- [ ] `runtime-truth.md` 仅作为入口页，不形成第二份 truth
- [ ] `system-architecture.md` 已被明确降级为非默认 authoritative source

## 阅读路径检查

- [ ] README 能引导到当前文档入口
- [ ] 新人可以按 “README -> current-architecture-baseline -> current-runtime-truth” 理解系统
