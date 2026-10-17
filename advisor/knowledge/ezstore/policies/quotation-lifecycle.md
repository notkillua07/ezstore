---
type: Business Rule
title: Quotation lifecycle and numbering (報價單狀態與編號)
description: Quotation statuses (draft, published), what can change in each, and the QT-YYYYMMDD-NNN numbering.
tags: [quotation]
status: stable
generated:
  by: claude-code/opus-5.5
  at: "2026-10-17T06:00:00Z"
sources:
  - id: readme-rules
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/README.md#business-rules-and-constraints
    title: README — Business Rules and Constraints
  - id: quotation-go
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/backend/models/quotation.go
    title: Quotation model (status defaults to draft)
---

# Statuses

| Status | 中文 | What is allowed |
|--------|------|-----------------|
| `draft` | 草稿 | Default for new quotations and copies. Items, customer and pricing factor can be edited; it can be deleted or published. |
| `published` | 已發布 | Final. Cannot be edited, deleted or published again.[^readme-rules] |

New quotations start as `draft`.[^quotation-go]

# Numbering

Quotation numbers are generated automatically as `QT-YYYYMMDD-NNN`, for example `QT-20260330-001`
(date of creation plus a three-digit sequence). Orders use `ORD-YYYYMMDD-NNN`.[^readme-rules]

# Copies and orders

- Changing a quotation through the [quotation agent](../guides/quotation-agent.md) always creates a new draft copy
  first; see [copy-on-write](copy-on-write.md).
- A quotation can be turned into an order; see [order lifecycle](order-lifecycle.md).
- Quotations are soft-deleted (`deleted_at`), so deleted ones disappear from lists but stay in the database.

[^readme-rules]: README, "Business Rules and Constraints".
[^quotation-go]: `backend/models/quotation.go`, `Status` default `'draft'`.
