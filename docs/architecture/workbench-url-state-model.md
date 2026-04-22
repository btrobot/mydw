# Workbench URL 状态模型
> Updated: 2026-04-22
> Status: Active

## 1. 文档目的

本文档说明 Creative Workbench 当前采用的 **URL 状态模型**：

- 哪些工作台状态被显式编码进 URL
- 页面如何从 URL 恢复状态
- Workbench → Detail → Back 如何保持操作上下文
- 这套模型当前的边界、约束与非目标

这是一份 **架构说明**，重点回答：

> Workbench 为什么这样设计，以及当前系统如何依赖这套设计来保持上下文。

---

## 2. 设计动机

Workbench 是创作主入口。用户在这里会持续进行：

- 搜索
- 筛选
- 排序
- 分页浏览
- 进入详情处理
- 返回工作台继续处理

如果这些状态只存在于组件内存里，就会出现几个问题：

- 刷新页面后状态丢失
- 复制链接无法复现当前现场
- 从详情返回后回不到原来的工作上下文
- E2E 很难稳定验证“上下文保持”能力

因此，Workbench 需要把关键状态从“隐式内存状态”收口成“显式 URL 状态”。

---

## 3. 核心定义

这里的“URL 状态模型”指：

> 把 Workbench 的关键工作状态定义为一组稳定的 URL 参数协议，并让页面能够双向同步：
>
> - **URL → UI**：打开页面时按 URL 恢复状态
> - **UI → URL**：用户调整状态后把结果写回 URL

这意味着 URL 不再只是导航地址，而是当前工作上下文的结构化表达。

---

## 4. 当前参数模型

Workbench 当前正式收口到 URL 的参数如下：

| 参数 | 含义 | 当前取值/格式 | 默认值 |
| --- | --- | --- | --- |
| `keyword` | 作品检索词 | 任意非空字符串 | 无 |
| `status` | 作品状态筛选 | `CreativeStatus` 枚举值 | 无 |
| `poolState` | 发布池准备状态筛选 | `in_pool` / `out_pool` / `version_mismatch` | 无 |
| `sort` | 排序模型 | `updated_at:ascend` / `updated_at:descend` | `updated_at:descend` |
| `page` | 当前页码 | 正整数 | `1` |
| `pageSize` | 每页条数 | 正整数 | `10` |

示例：

```text
#/creative/workbench?keyword=Spring&status=WAITING_REVIEW&poolState=in_pool&sort=updated_at%3Adescend&page=1&pageSize=10
```

该 URL 表示：

- 搜索词为 `Spring`
- 只看 `WAITING_REVIEW`
- 只看 `in_pool`
- 按 `updated_at` 倒序
- 第 1 页
- 每页 10 条

---

## 5. 为什么这些状态进入 URL

当前进入 URL 的都是“工作上下文恢复”必需状态：

- 搜索条件
- 筛选条件
- 排序方式
- 分页位置

这些状态决定用户当前“正在看什么、按什么顺序看、看到第几页”。

相反，一些短期 UI 细节 **不** 进入 URL，例如：

- 纯展示型折叠状态
- 临时 hover / focus 状态
- 非关键交互中间态

因此，这个模型是“最小可恢复工作上下文模型”，不是“把所有 UI 状态都塞进 URL”。

---

## 6. URL → UI 恢复规则

Workbench 打开时，URL 是初始化状态的来源。

当前恢复规则如下：

### 6.1 参数解析

- `keyword`：读取后去掉首尾空白；空值视为未设置
- `status`：只有落在当前状态枚举内才生效，否则回退为未设置
- `poolState`：只有落在当前池状态枚举内才生效，否则回退为未设置
- `sort`：当前只接受 `updated_at:ascend` / `updated_at:descend`，非法值回退为默认倒序
- `page` / `pageSize`：只接受正整数，非法值回退到默认值

### 6.2 表单与表格初始化

解析后的 URL 状态会用于：

- 初始化搜索表单
- 初始化分页
- 初始化默认排序
- 触发表格请求逻辑

换句话说：

> URL 不是“展示给用户看的附加信息”，而是 Workbench 初始化状态的一部分。

---

## 7. UI → URL 回写规则

当用户在 Workbench 中进行以下动作时，页面会把结果写回 URL：

- 应用搜索/筛选
- 切换排序
- 切换页码
- 修改每页条数

这样可以保证：

- 刷新后仍能恢复
- 复制链接后别人也能看到同样上下文
- 后续页面跳转可以携带当前上下文

---

## 8. `returnTo` 与返回链路

Workbench URL 模型只解决“当前工作台状态是什么”。

为了继续解决“从详情返回时要回到哪个状态”，当前实现又引入了 `returnTo`。

### 8.1 Workbench 自身 URL

例如：

```text
#/creative/workbench?keyword=Spring&status=WAITING_REVIEW&page=1&pageSize=10
```

它表达的是：

> 当前 Workbench 状态是什么。

### 8.2 Detail 页 `returnTo`

从 Workbench 进入作品详情时，会把当前 Workbench 完整路径编码成 `returnTo`：

```text
#/creative/101?returnTo=%2Fcreative%2Fworkbench%3Fkeyword%3DSpring%26status%3DWAITING_REVIEW%26page%3D1%26pageSize%3D10
```

它表达的是：

> 返回时应该回到哪个 Workbench 状态。

### 8.3 当前返回规则

- Workbench → Detail：附带 `returnTo`
- Detail 页返回按钮：优先跳回 `returnTo`
- Detail → Task Detail：继续把 `returnTo` 透传下去

因此当前链路形成：

```text
Workbench(带状态)
  -> Creative Detail(携带 returnTo)
    -> Task Detail(继续携带 returnTo)
      -> Back
        -> 回到原 Workbench 状态
```

---

## 9. 当前实现触点

当前实现主要落在以下文件：

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

其中：

- `CreativeWorkbench.tsx`
  - 负责解析 URL
  - 初始化表格状态
  - 在筛选/排序/分页后回写 URL
  - 打开详情时构造 `returnTo`
- `CreativeDetail.tsx`
  - 负责读取 `returnTo`
  - 统一返回到来源 Workbench
- `creative-workbench.spec.ts`
  - 锁定刷新恢复
  - 锁定进入详情后返回恢复

---

## 10. 非目标与当前边界

这套模型当前 **不** 负责：

- 服务端搜索/排序协议设计
- 跨域/跨模块的全局上下文系统
- PR-2 中业务视图与诊断视图的进一步拆分
- PR-3 中文案与四态治理收口
- 把所有 Workbench 临时 UI 细节持久化

当前边界是：

> 只为 “Creative Workbench 可管理性收口 / Slice A” 提供最小但稳定的上下文保持能力。

---

## 11. 架构含义

这套 URL 模型的真正作用，不只是“前端体验更好”，而是把：

- 原本隐式存在于页面内存里的状态
- 原本只存在于操作者脑中的上下文

变成了系统可以：

- 表达
- 传递
- 恢复
- 测试

的结构化对象。

这使得 Workbench 从“一个临时列表页”更接近“一个可管理、可回溯、可协作的工作台入口”。

---

## 12. 演进约束

虽然这是一份架构说明，不是治理规则，但当前模型已经具备轻量 contract 属性。

后续如果要变更以下内容，应视为模型变更，而不只是普通实现重构：

- 参数名
- 参数值枚举
- 默认排序
- 分页默认值
- `returnTo` 传递方式

因为这些变化会同时影响：

- 页面恢复逻辑
- 返回链路
- 复制链接复现能力
- E2E 用例
- 相关 current truth 文档

---

## 13. 当前验证基线

当前这套模型已由以下验证覆盖：

- `frontend` `npm run typecheck`
- `frontend` `npm run build`
- Playwright：
  - `e2e/creative-workbench/creative-workbench.spec.ts`
  - 覆盖刷新保持状态
  - 覆盖 detail → back 保持状态

---

## 14. 一句话总结

Workbench URL 状态模型就是：

> 把 Workbench 的关键工作状态定义成一套稳定、可恢复、可传递、可测试的 URL 参数协议，并通过 `returnTo` 保持跨页面返回链路中的操作上下文。
