# 从当前状态出发，Slice 2~6 分别该“直做”还是“先 ralplan”的判断表

日期：2026-04-24

关联文档：

- `discss/creative-two-level-candidate-pool-execution-rhythm-rules-2026-04-24.md`
- `.omx/plans/prd-creative-two-level-candidate-pool-adoption-2026-04-24.md`
- `.omx/plans/test-spec-creative-two-level-candidate-pool-adoption-2026-04-24.md`

当前基线：

- Phase 0 已冻结
- Slice 1「作品真值显式化」已完成并 fresh verification 通过
- 当前判断目标：**从现在开始，Slice 2~6 哪些可以直接执行，哪些更适合先补一次局部 ralplan**

---

## 1. 总结版结论

| Slice | 主题 | 当前建议 | 结论 |
|---|---|---|---|
| Slice 2 | 作品-商品关联表 | 可直做 | **直做** |
| Slice 3 | 作品候选池 | 可直做 | **直做** |
| Slice 4 | 当前入选媒体集合 | 条件较多 | **建议先补一次局部 ralplan** |
| Slice 5 | Workbench 汇总升级 | 依赖前序稳定 | **默认直做，但以前置验收为门槛** |
| Slice 6 | Version / Package 对齐 | 高风险收口 | **先 ralplan** |

一句话版本：

> **Slice 2、3 适合直接推进；Slice 4 是第一次强碰“selected-media 真正收口”，建议先补局部 ralplan；Slice 5 在 Slice 4 稳定后可直做；Slice 6 是冻结与发布口径总收口，建议执行前必须再过一次 ralplan。**

---

## 2. 为什么这么判断

当前已经具备的条件：

1. 总 PRD / test spec 已存在
2. Phase 0 已冻结了：
   - authority matrix
   - primary-product 规则
   - current cover contract
   - `creative_input_items` 兼容退场表
   - Workbench 摘要字段映射表
   - manifest v1 typed contract
3. Slice 1 已把“作品真值”显式化，给后续 Slice 提供了稳定锚点

因此：

- **越靠前、越贴近已冻结合同、越不跨 Version/Publish 的 Slice，越适合直做**
- **越靠后、越接近 freeze / manifest / publish / version 读口径总对齐的 Slice，越适合先局部 ralplan 再执行**

---

## 3. 分 Slice 判断

## Slice 2：作品-商品关联表

### 当前建议

**直做。**

### 原因

这是“二级候选池模型”里最自然的下一步，而且它主要承接的是已冻结的 Phase 0 合同：

- primary-product 规则已经冻结
- authority matrix 已经定义了 primary product / current product name 的口径
- Slice 1 已经把 current truth 显式化，Slice 2 只是在此基础上引入 `creative_product_links`

也就是说，Slice 2 不是重新发明合同，而是把 Phase 0 里已经讲清楚的规则落地。

### 直做前需要满足

- 不改 primary-product 规则定义
- 不改 `subject_product_id` 与 primary link 的对应语义
- 不顺手扩展到候选池和 selected-media
- 验收保持在“商品关联、顺序、主题商品切换、默认跟随/手工覆盖”范围内

### 一旦出现这些信号就停下回 ralplan

- 发现 primary-product 规则其实不够用
- 发现 current cover / current copywriting 的跟随规则需要重写
- 发现商品关联表必须与候选池一起设计才说得清

### 推荐动作

```bash
$ralph "执行已批准的 Slice 2：作品-商品关联表。严格遵守已冻结 primary-product 规则与 authority matrix；不进入候选池、不进入 selected-media、不改 version/package freeze 语义。"
```

---

## Slice 3：作品候选池

### 当前建议

**直做。**

### 原因

在 Slice 2 完成后，作品已经有“真值 + 商品关系”，这时引入候选池是自然顺推：

- 候选池是作品级“小池子”
- 它本身仍属于 authoring / detail 领域
- 主要是 CRUD / adopt / remove / status 合同
- 还没有正式进入 freeze / publish 总收口

所以 Slice 3 仍然适合在现有计划下直接执行。

### 直做前需要满足

- Slice 2 已通过验证
- candidate contract 不改变 Phase 0 的 authority 分工
- 候选池只定义“候选”，不提前承担最终冻结责任
- 不顺手把 selected-media 和 version/package 一起做掉

### 一旦出现这些信号就停下回 ralplan

- 发现 candidate 状态机需要大改
- 发现候选池与“当前入选集合”边界说不清
- 发现候选池已不可避免影响 Workbench summary / manifest 结构

### 推荐动作

```bash
$ralph "执行已批准的 Slice 3：作品候选池。仅落地 candidate CRUD / adopt / remove / status 合同；保持候选与当前入选分层，不提前进入 Version/Package 冻结逻辑。"
```

---

## Slice 4：当前入选媒体集合

### 当前建议

**建议先补一次局部 ralplan。**

### 原因

这是整条线里第一个真正高风险的拐点。

因为从这一刻开始，不再只是“有真值、有候选”，而是要开始明确：

- 什么叫当前真正入选
- `creative_input_items` 在兼容期里还剩什么责任
- selected-media projection 的唯一读口径是什么
- 后续 Workbench / Version / Publish 是否都必须转向这个投影

虽然这些大方向在 Phase 0 里冻结过，但真正到 Slice 4 落地时，往往会暴露出更多细节问题：

- video/audio 的顺序与 enabled 语义
- 候选转入选的动作边界
- “移除/禁用/重排”是 authoring 语义还是 publish-ready 语义
- 与现有 `creative_input_items` 的桥接是否足够机械

这类问题如果在执行中边做边定，很容易把 Slice 4 做成半个 Slice 5 / Slice 6。

### 为什么不建议直接硬推

因为它最容易出现：

- authority 漂移
- 兼容桥接失控
- Workbench / Version / Publish 偷读旧 carrier
- selected-media 成为“事实标准”但没有正式被计划确认

### 推荐做法

先做一个**局部 ralplan**，只规划 Slice 4：

- 明确 selected-media projection contract
- 明确 `creative_input_items` 在这一阶段的剩余职责
- 明确与 Workbench / Version / Publish 的边界
- 明确这一 Slice 严格不做什么

### 推荐动作

```bash
$ralplan --interactive "只规划 Slice 4：当前入选媒体集合。补齐 selected-media projection contract、creative_input_items 兼容边界、文件触点、验收标准；不要扩到 Workbench 汇总与 Version/Package 对齐。"
```

规划批准后再执行：

```bash
$ralph "执行已批准的 Slice 4：当前入选媒体集合。严格按 selected-media projection contract 落地，不提前扩边界到 Workbench/Version/Package 总收口。"
```

---

## Slice 5：Workbench 汇总升级

### 当前建议

**默认直做，但以前置验收为门槛。**

### 原因

Slice 5 的理论复杂度不如 Slice 4 和 Slice 6。

如果以下条件成立，它更像一个“聚合口径接线”工作：

- Slice 2 的商品关系已稳定
- Slice 3 的候选池已稳定
- Slice 4 的 selected-media projection 已稳定
- Phase 0 的 Workbench summary mapping 没有被推翻

那它就适合直接做，因为它主要是在既定映射表基础上把 summary 接出来。

### 为什么不是无条件直做

因为它对前置 Slice 的依赖最强。

如果 Slice 4 实际落地后，selected-media projection 跟原来想的不一样，那 Slice 5 就不应该直接做，而应该先局部重看规划。

### 直做前必须确认

- summary mapping 表无需改写
- Workbench 只读后端聚合结果，不自己拼口径
- preset/filter/sort 不因 summary 字段升级而回归
- diagnostics 语义不被误扩展

### 一旦出现这些信号就停下回 ralplan

- summary mapping 需要重写
- Workbench 需要临时拼接未冻结字段
- Slice 5 被迫带出 diagnostics / detail / version 的新语义

### 推荐动作

```bash
$ralph "执行已批准的 Slice 5：Workbench 汇总升级。以已冻结 workbench summary mapping 为唯一口径；Workbench 只消费后端聚合结果，不扩展到 Version/Package 语义。"
```

---

## Slice 6：Version / Package 对齐

### 当前建议

**先 ralplan。**

### 原因

这是整条线的真正总收口点，也是最容易“做进去就出不来”的地方。

它会同时碰到：

- version freeze source
- package freeze source
- manifest v1
- publish consumption path
- generation / workflow / publish service 的最终读取口径

即使总 PRD 已有，到了真正执行 Slice 6 前，也强烈建议基于 Slice 2~5 的实际落地结果再做一次局部共识规划。

因为这时候最重要的问题已经不再是“原计划怎么写”，而是：

- 前面几步真实落地后，freeze 语义有没有偏差
- manifest v1 是否还需要微调
- 哪些字段已经可以完全从 legacy carrier 脱离
- 哪些服务消费路径可以真正统一

这些都属于典型的 **“执行前再收一次边界”** 场景。

### 推荐做法

在进入 Slice 6 前，先局部 ralplan：

- 回顾 Slice 2~5 实际实现
- 锁定最终 freeze source
- 锁定 manifest v1 字段与顺序语义
- 锁定 version / package / publish 的唯一读取口径
- 明确是否还存在 compat projection 残留

### 推荐动作

```bash
$ralplan --interactive --deliberate "只规划 Slice 6：Version / Package 对齐。基于 Slice 2~5 实际落地结果，重新确认 freeze source、manifest v1、publish/version/package 统一读取口径、compat projection 退场边界与验收标准。"
```

批准后再执行：

```bash
$ralph "执行已批准的 Slice 6：Version / Package 对齐。严格按最新 freeze/manifest 合同收口，不混入新的 authoring/workbench 扩边界。"
```

---

## 4. 推荐执行顺序

从当前状态出发，建议顺序如下：

1. **Slice 2：直做**
2. **Slice 3：直做**
3. **Slice 4：先局部 ralplan，再执行**
4. **Slice 5：若 Slice 4 稳定，则直做**
5. **Slice 6：先局部 ralplan，再执行**

---

## 5. 最终建议

如果只保留一句话，建议记住下面这条：

> **当前 creative 二级候选池后续推进节奏，推荐采用“2、3 直做；4 先局部 ralplan；5 条件直做；6 必须先 ralplan”的策略。**

这套节奏的核心不是保守，而是把规划成本用在最容易失控的节点上：

- 前段快推
- 中段收边界
- 后段再总收口

这样既保留速度，也保留合同稳定性。
