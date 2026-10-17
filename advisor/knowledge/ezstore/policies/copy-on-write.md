---
type: Business Rule
title: Copy-on-write for quotation changes (修改前先複製)
description: Every change made through the quotation agent is applied to a new copy; the original quotation is never modified.
tags: [quotation, safety]
status: stable
generated:
  by: claude-code/opus-5.5
  at: "2026-10-17T06:00:00Z"
sources:
  - id: mcp-server
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/mcp_server/server.py
    title: update_pricing_factor / adjust_total_price tools
---

# Rule

Changing the pricing factor or the total price of a quotation through the
[quotation agent](../guides/quotation-agent.md) always:

1. duplicates the quotation into a new `draft` copy with a new number, then
2. applies the change to the copy only.

The original keeps its number, factor, total and status, and the agent's reply says so ("原始報價單 …（未修改）").[^mcp-server]

# Why

Quotations may already have been sent to a customer. Keeping the original untouched means every version stays
traceable and nothing a customer has seen changes silently. A `published` quotation cannot be edited at all
(see [quotation lifecycle](quotation-lifecycle.md)).

[^mcp-server]: `update_pricing_factor` and `adjust_total_price` in `mcp_server/server.py` call duplicate first.
