---
type: Business Rule
title: How a quotation's price is computed (報價計算方式)
description: Unit price, subtotal, total, profit and profit rate formulas the backend applies to every quotation.
tags: [pricing, quotation]
status: stable
generated:
  by: claude-code/opus-5.5
  at: "2026-10-17T06:00:00Z"
sources:
  - id: readme-pricing
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/README.md#pricing-computation-rules
    title: README — Pricing Computation Rules
---

# Formula

When a quotation is created or updated, the backend:[^readme-pricing]

1. Copies the customer's level onto the quotation (see [customer levels](customer-levels.md)).
2. For each item, copies the product's name, cost and list price (a snapshot; later product changes do not affect the quotation).
3. `unit_price = list_price × pricing_factor`
4. `subtotal = unit_price × quantity`
5. `total_price = Σ subtotal`
6. `profit_amount = Σ (unit_price − cost) × quantity`
7. `profit_rate = profit_amount ÷ total_price` (0 when the total is 0)

# Examples

Ten boxes of [A4 copy paper](../products/SP-001.md) (list price 650) for a `new` customer with factor 0.95:
unit price 617.5, subtotal and total 6175.

The same ten boxes for a `vip` customer at the default factor 0.80: unit price 520, total 5200.

# Changing the total

To reach a target total, the pricing factor is adjusted, not the item prices. The
[quotation agent](../guides/quotation-agent.md) searches for the factor by bisection (at most 20 tries) on a copy
of the quotation, so the result can differ from the target by a few cents.

[^readme-pricing]: README, "Pricing Computation Rules".
