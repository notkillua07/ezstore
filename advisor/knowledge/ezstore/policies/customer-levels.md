---
type: Business Rule
title: Customer levels and default pricing factors (客戶等級與預設報價因子)
description: The three customer levels (vip, standard, new) and the pricing factor each one gets by default.
tags: [pricing, customer]
status: stable
generated:
  by: claude-code/opus-5.5
  at: "2026-10-17T06:00:00Z"
sources:
  - id: customer-go
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/backend/models/customer.go
    title: DefaultPricingFactor() in backend/models/customer.go
  - id: readme-pricing
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/README.md#pricing-computation-rules
    title: README — Pricing Computation Rules
---

# Levels

Every customer has exactly one level: `vip`, `standard` or `new` (any other value is rejected).[^readme-pricing]

| Level | 中文 | Default pricing factor | Effect on list price |
|-------|------|------------------------|----------------------|
| `vip` | VIP 客戶 | 0.80 | 20% below list price |
| `standard` | 一般客戶 | 0.90 | 10% below list price |
| `new` | 新客戶 | 1.00 | list price |

An unknown level falls back to 0.90.[^customer-go]

# How it is used

When a quotation is created, the customer's level is copied onto the quotation (`customer_level`) and the
default pricing factor for that level is used unless someone sets a different factor. See
[pricing computation](pricing-computation.md) for the full price formula.

A sales person can still change the factor of a quotation later; the
[quotation agent](../guides/quotation-agent.md) does this on a copy, never on the original
(see [copy-on-write](copy-on-write.md)).

[^customer-go]: `DefaultPricingFactor()` in `backend/models/customer.go`.
[^readme-pricing]: README, "Pricing Computation Rules" and "Business Rules and Constraints".
