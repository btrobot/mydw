# 文档质量 Checklist

> 用于验证文档的正确性、一致性和完整性。
> 可由 QA Lead 或 Tech Lead 在 Sprint 结束时执行，也可集成到 pre-commit hook。

---

## 1. 完整性检查

### 1.1 必要文档是否存在

> 缺失的文档应创建对应任务，不阻塞其他检查项。

```
[ ] CLAUDE.md 存在且有 ## References 表
[ ] backend/CLAUDE.md 存在
[ ] docs/system-architecture.md 存在
[ ] docs/dev-guide.md 存在
[ ] docs/data-model.md 存在
[ ] docs/api-reference.md 存在
```

### 1.2 References 表覆盖度

```
[ ] CLAUDE.md References 表中的每个路径指向的文件都存在
[ ] 每个 .claude/agents/*.md 有 ## Key References 节
[ ] Agent Key References 中的路径都存在
```

### 1.3 ADR 覆盖度

```
[ ] 每个重大技术选型有对应 ADR（检查方法：Grep "为什么" 类问题是否有 ADR 回答）
[ ] ADR 编号连续，无跳跃
[ ] 废弃的 ADR 标记为 Deprecated/Superseded
```

---

## 2. 正确性检查

### 2.1 数据模型 vs 代码

```
[ ] docs/data-model.md 中的表名与 models/__init__.py 中的 __tablename__ 一致
[ ] 字段列表与模型定义一致（无遗漏、无多余）
[ ] 关系描述与 relationship() 定义一致
[ ] 加密标记与实际 encrypt_data() 调用一致
```

验证命令：
```bash
# 提取模型中的表名
grep "__tablename__" backend/models/__init__.py
# 对比文档中的表名
grep "^## " docs/data-model.md
```

### 2.2 API 端点 vs 代码

```
[ ] 文档中的端点路径与 @router 装饰器一致
[ ] 请求参数与 Pydantic Schema 字段一致
[ ] 响应状态码与代码中的 status_code 一致
[ ] deprecated 标记与代码一致
```

验证命令：
```bash
# 提取所有路由
grep "@router\." backend/api/*.py
# 对比文档端点数量
grep "^### " docs/api-reference.md | wc -l
```

### 2.3 架构文档 vs 代码

```
[ ] 技术栈版本与 package.json / requirements.txt 一致
[ ] 项目结构树与实际目录一致
[ ] 路由注册列表与 main.py 一致
```

---

## 3. 一致性检查

### 3.1 Freshness（新鲜度）

```
[ ] 每个文档头部有 Updated: YYYY-MM-DD
[ ] 无文档的 Updated 日期超过 30 天（活跃项目）
[ ] 自动生成的文档有 <!-- AUTO-GENERATED --> 标记
```

### 3.2 文档体积

```
[ ] 根 CLAUDE.md 不超过 200 行
[ ] 每个文档不超过 500 行（超过则拆分）
```

### 3.3 单一事实来源

```
[ ] 同一信息不在两个文档中重复描述
[ ] 无两个文档描述同一主题（如旧 architecture.md 和新 system-architecture.md 并存）
[ ] 引用关系是单向的（A 引用 B，B 不反向引用 A 的细节）
```

### 3.3 术语一致

```
[ ] 同一概念在所有文档中用同一名称（如 "Task" 不混用 "任务"/"发布任务"/"PublishTask"）
[ ] 模型名称与代码类名一致
[ ] API 路径前缀与 main.py 注册一致
```

---

## 4. 自动化检查脚本

以下检查可集成到 pre-commit hook 或 CI：

### 4.1 引用完整性（References 表中的文件都存在）

```python
# scripts/check-doc-refs.py
import re
from pathlib import Path

root = Path(".")
errors = []

for md_file in root.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    # 匹配 References 表中的路径
    for match in re.finditer(r'\|\s*\S+\s*\|\s*([\w/./-]+\.md\S*)\s*\|', content):
        ref_path = match.group(1).split("#")[0].strip()
        if not (root / ref_path).exists():
            errors.append(f"{md_file}: broken ref → {ref_path}")

for e in errors:
    print(f"[DOC-REF] {e}")
```

### 4.2 模型-文档漂移检测

```python
# scripts/check-model-drift.py
import re
from pathlib import Path

models_file = Path("backend/models/__init__.py")
doc_file = Path("docs/data-model.md")

# 提取代码中的表名
code_tables = set(re.findall(r'__tablename__\s*=\s*"(\w+)"', models_file.read_text()))

# 提取文档中的表名
doc_tables = set(re.findall(r'^## (\w+)', doc_file.read_text(), re.MULTILINE))

missing_in_doc = code_tables - doc_tables
extra_in_doc = doc_tables - code_tables

if missing_in_doc:
    print(f"[DRIFT] 代码有但文档缺: {missing_in_doc}")
if extra_in_doc:
    print(f"[DRIFT] 文档有但代码无: {extra_in_doc}")
```

### 4.3 API 端点数量对比

```python
# scripts/check-api-drift.py
import re
from pathlib import Path

api_dir = Path("backend/api")
doc_file = Path("docs/api-reference.md")

# 代码中的端点数
code_count = 0
for f in api_dir.glob("*.py"):
    code_count += len(re.findall(r'@router\.(get|post|put|delete)\(', f.read_text()))

# 文档中的端点数
doc_count = len(re.findall(r'^### (GET|POST|PUT|DELETE) ', doc_file.read_text(), re.MULTILINE))

if abs(code_count - doc_count) > 2:
    print(f"[DRIFT] API 端点数不一致: 代码 {code_count}, 文档 {doc_count}")
```

---

## 5. 执行时机

| 时机 | 检查范围 | 执行者 |
|------|----------|--------|
| 每次 commit | 引用完整性 (4.1) | pre-commit hook 自动 |
| Sprint 结束 | 全部 checklist | QA Lead 或 Tech Lead |
| 模型变更后 | 模型漂移 (4.2) | pre-commit hook 警告 |
| API 变更后 | API 漂移 (4.3) | pre-commit hook 警告 |
| 架构重构后 | 正确性全量 (2.x) | Tech Lead 手动 |

---

## 6. 与 Agent 框架集成

在 `.claude/agents/qa-lead.md` 的职责中增加：

```markdown
## 文档质量检查
- Sprint 结束时执行 docs/doc-checklist.md 全量检查
- 发现漂移时创建修复任务
```

在 `/release-checklist` skill 中增加文档检查步骤。
