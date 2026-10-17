---
type: Business Rule
title: Orders and converting a quotation to an order (訂單與報價單轉訂單)
description: Order statuses and what happens when a quotation is converted to an order.
tags: [order, quotation]
status: stable
generated:
  by: claude-code/opus-5.5
  at: "2026-10-17T06:00:00Z"
sources:
  - id: order-go
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/backend/models/order.go
    title: Order model (status defaults to pending)
  - id: mcp-server
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/mcp_server/server.py
    title: convert_to_order tool in the MCP Server
  - id: seed
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/scripts/seed-test-data.sql
    title: Seed data (order statuses in use)
---

# Statuses

New orders start as `pending`.[^order-go] The test data also uses `confirmed`, `completed` and `cancelled`.[^seed]

| Status | 中文 |
|--------|------|
| `pending` | 待處理 |
| `confirmed` | 已確認 |
| `completed` | 已完成 |
| `cancelled` | 已取消 |

# Converting a quotation

Converting creates a new order with the quotation's customer and items (same unit prices and quantities) and
links it to the quotation through `quotation_id`. The quotation itself is not changed and is not published by
this step.[^mcp-server]

The [quotation agent](../guides/quotation-agent.md) can do the conversion; its reply contains the new order number
(`ORD-YYYYMMDD-NNN`) and a link to the order page. See also [quotation lifecycle](quotation-lifecycle.md).

[^order-go]: `backend/models/order.go`, `Status` default `'pending'`.
[^seed]: `scripts/seed-test-data.sql`.
[^mcp-server]: `convert_to_order` in `mcp_server/server.py`.
