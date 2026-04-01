# Commit Rules - Git 提交规范

## 提交格式

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Type 类型

| Type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档更新 |
| style | 代码格式 |
| refactor | 重构 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### 示例

```
# 功能
feat(frontend): 添加账号管理页面
feat(backend): 新增定时任务 API
feat(clip): 添加高光检测功能

# 修复
fix(frontend): 修复账号列表加载状态
fix(backend): 修复 Cookie 加密异常

# 文档
docs: 更新 README.md
```

## 提交时机

### 应该提交
- ✅ 完成一个功能
- ✅ 修复一个 bug
- ✅ 更新文档

### 不应该提交
- ❌ 未完成的代码
- ❌ 调试代码
- ❌ 构建产物
