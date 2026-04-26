# creative 二级候选池执行节奏规则（什么时候直做 / 什么时候回 ralplan）

日期：2026-04-24

---

## 1. 结论

本项目后续推荐采用 **“Phase 用 ralplan，Slice 用条件直做”** 的混合节奏，而不是机械地二选一：

- **治理层**：继续保留你原来的做法，用 `$ralplan` 负责 Phase 级别拆解、PR 计划、边界冻结、验收定义。
- **执行层**：在已有批准计划的前提下，如果某个 Slice 已经足够清晰，就直接用 `$ralph` / `$team` 执行，不必为每一个 Slice 重复跑一次 `$ralplan`。

换句话说：

> **先用 ralplan 管边界，再在既有批准计划内高效推进；一旦边界漂移，再回到 ralplan。**

---

## 2. 为什么不能只选一种

### 2.1 只按以前的“每次都先 ralplan”

优点：

- 边界清楚
- PR 更整齐
- 风险更可控
- 更适合多人协作和中长期演进

缺点：

- 规划成本高
- 对已经清晰的小 Slice 来说重复劳动较多
- 节奏偏慢，容易把执行问题重新包装成规划问题

### 2.2 只按“清楚了就直接做”

优点：

- 速度快
- 上下文连续
- 对已收敛 Slice 更高效

缺点：

- 容易在执行中悄悄扩边界
- 容易把 authority / freeze / contract 改动混入当前 Slice
- 到后面可能出现“做着做着改计划”的失控状态

因此最佳实践不是二选一，而是分层使用。

---

## 3. 推荐执行规则

## 3.1 什么时候必须先回 `$ralplan`

以下任一成立，就先走 `$ralplan`：

1. **进入新 Phase / 新主题**
   - 例如从“作品真值显式化”进入“作品-商品关系模型重构”
2. **边界发生变化**
   - 当前 Slice 已不再是原计划里的机械推进
3. **authority matrix / freeze source / summary source 要调整**
   - 包括：
   - primary product 规则
   - current cover contract
   - current copywriting contract
   - version/package freeze source
   - workbench summary source
4. **验收标准不再清楚**
   - 做之前说不清“完成是什么意思”
5. **触点明显扩散**
   - 需要同时改多个 slice 的责任边界
6. **需要重新拆 PR**
   - 例如原来的 Slice 太大、太散，必须重切成新的执行包

一句话：

> **凡是涉及“重新定边界、重新定责任、重新定验收”的，都先回 ralplan。**

---

## 3.2 什么时候可以直接执行

如果满足下面条件，就可以**不重新跑 `$ralplan`**，直接执行：

1. 已有批准的 **PRD**
2. 已有批准的 **test spec**
3. 当前 Slice 的名称、目标、In/Out Scope 已明确
4. 当前 Slice 的主要文件触点基本明确
5. 验收标准清晰，可直接验证
6. 上一个 Slice 已完成并有 fresh verification evidence

这时可直接使用：

- `$ralph "执行已批准的 Slice X"`
- 或 `$team "执行已批准的 Slice X"`

一句话：

> **凡是“边界已定、目标已清、验收已清”的 Slice，直接执行。**

---

## 3.3 执行中什么时候要立刻停下并回到 `$ralplan`

即使已经开始执行，只要出现以下信号，也应该停止当前直推，回到 `$ralplan`：

1. 发现当前 Slice 其实会改到后续 Slice 的 authority
2. 发现要提前改 version / package / manifest / workbench summary 的合同
3. 为了做当前 Slice，不得不先做后面两三个 Slice
4. E2E / integration 验收口径开始模糊
5. 当前实现明显超出原 PRD / test spec 约束

一句话：

> **执行中一旦出现“计划外扩边界”，不要硬做，马上回 ralplan。**

---

## 4. 套到当前 creative 二级候选池项目

当前这条线推荐按下面理解：

### 4.1 什么属于 Phase 级治理

这些应该交给 `$ralplan`：

- 总体目标是否变化
- Slice 1-6 是否还成立
- authority matrix 是否变化
- primary-product 规则是否变化
- current cover / copywriting / selected-media 合同是否变化
- Workbench summary / Version / Package 冻结口径是否变化

### 4.2 什么属于 Slice 级执行

这些在计划已批准时可以直接做：

- Slice 1：作品真值显式化
- Slice 2：作品-商品关联表
- Slice 3：作品候选池
- Slice 4：当前入选媒体集合
- Slice 5：Workbench 汇总升级
- Slice 6：Version / Package 对齐

前提是：

- 当前 Slice 的边界没有变化
- 该 Slice 的测试入口明确
- 不去偷改其他 Slice 的合同

---

## 5. 对这次 Slice 1 的判定

这次 Slice 1 直接执行是合理的，不属于“跳过规划”，原因是：

1. 总 PRD 已存在
2. test spec 已存在
3. Phase 0 合同已冻结
4. Slice 1 边界明确：**作品真值显式化**
5. 验证路径明确：backend contract + frontend build/typecheck + Playwright

所以这次本质上是：

> **在既有批准计划内继续推进，而不是绕过规划。**

---

## 6. 建议采用的默认工作流

## 6.1 Phase 层默认动作

先执行：

```bash
$ralplan "把当前 Phase 拆成可执行 PR / Slice 计划，输出 ralph-ready 文档"
```

目标：

- 固定范围
- 固定合同
- 固定测试
- 固定推荐执行顺序

## 6.2 Slice 层默认动作

### 如果 Slice 已经清楚

直接执行：

```bash
$ralph "执行已批准的 Slice X"
```

### 如果 Slice 还不够清楚

先补一个局部规划：

```bash
$ralplan "只规划 Slice X，补齐风险、文件触点、验收标准、推荐执行模式"
```

---

## 7. 一页式判断表

## 7.1 继续直做

满足以下条件时，直接做：

- 有 PRD
- 有 test spec
- Slice 名称明确
- In/Out Scope 明确
- 验收明确
- 上一 Slice 已验证完成

## 7.2 回到 ralplan

出现以下任一情况时，回到 ralplan：

- 改边界
- 改 authority
- 改 freeze contract
- 改 summary contract
- 触点扩散
- 验收不清
- PR 需要重切

---

## 8. 最终建议

对这个仓库，推荐长期采用下面这条规则：

> **保留“先 ralplan 定 Phase / 定 PR”的治理方式；但对已经批准且边界清晰的 Slice，不要重复规划，直接执行。只有当边界、合同、责任或验收发生漂移时，才回到 ralplan。**

这会同时保留两件事：

- 你的老方法的 **稳**
- 当前直推节奏的 **快**

也最符合当前 creative 二级候选池这种“多 Slice、强合同、但可逐段落地”的项目形态。
