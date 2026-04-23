# Phase 0 Contract Freeze — Primary Product Rules

## Goal

冻结多商品场景下 primary product 的唯一规则，避免 Slice 2 落地时出现双主语义。

## Rules

1. 一件作品可关联多个商品，但 **primary product 只能有一个**。
2. primary product 的唯一权威面是：
   - `creative_product_links.is_primary = true`
3. 迁移期：
   - `creative_items.subject_product_id` 作为兼容镜像存在
   - 但 primary truth 来自 `creative_product_links`
4. `subject_product_id` 的写回规则：
   - 仅由 primary product 变更流程统一回填
   - 其他路径禁止各自写回
5. 切换 primary product 时：
   - `product_name_mode = follow_primary_product` 时，允许同步更新当前商品名称
   - `product_name_mode = manual` 时，禁止覆盖
   - `cover_mode = default_from_primary_product` 时，允许同步更新当前封面
   - `cover_mode = manual` 或 `adopted_candidate` 时，禁止覆盖
   - `copywriting_mode = manual` 时，禁止覆盖
6. Workbench 展示的主题商品摘要与 Detail 顶部主题商品摘要都以 primary product 规则为准。

## Single Write Entry

primary product 相关 snapshot 的唯一写入口为：

- `backend/services/creative_service.py`

禁止：

- 前端直接写 `subject_product_id`
- version/publish/generation service 各自修正 primary product

## Retirement

- Slice 2 完成后，所有新逻辑都必须经由 `creative_product_links`
- `subject_product_id` 仅保留兼容与历史回读语义
