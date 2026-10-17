---
type: Agent Capability
title: Quotation agent (報價單管理 Agent)
description: What the quotation agent can do, the phrasing it understands, and how the sales advisor reaches it over A2A.
resource: http://agent:8080/a2a/quotation_agent/.well-known/agent-card.json
tags: [agent, a2a, quotation]
status: stable
generated:
  by: claude-code/opus-5.5
  at: "2026-10-17T06:00:00Z"
sources:
  - id: spec
    resource: https://github.com/cshliu77/ezstore/blob/workshop-start/agent-spec-prompt.md
    title: agent-spec-prompt.md, section 1
---

# Operations

The quotation agent performs these six operations on live EZStore data:[^spec]

| Operation | Example request |
|-----------|-----------------|
| Look up a quotation | 我要查詢報價單，報價單編號：QT-20260330-001 |
| List a customer's quotations | 我要查詢客戶的報價單清單，客戶名稱：史塔克工業 |
| Duplicate a quotation | 我要複製報價單，報價單編號：QT-20260330-001 |
| Change the pricing factor | 我要修改報價單報價因子，報價單編號：QT-20260330-001，報價因子改為 1.5 |
| Change the total price | 我要修改報價單總價，報價單編號：QT-20260330-001，總價改為 8000 |
| Convert to an order | 我要將報價單轉訂單，報價單編號：QT-20260330-001 |

Every reply contains a plain-text link to the quotation or order page. Changes follow
[copy-on-write](../policies/copy-on-write.md). If the quotation number is missing it asks for it; anything else
(weather, editing customers or products, ...) is refused.

# How the sales advisor uses it

The sales advisor answers policy and product questions itself from this knowledge bundle. When a user wants one of
the six operations, it hands the request to the quotation agent through the A2A protocol (agent card at the
`resource` above, inside Docker Compose) and passes the reply back unchanged, links included.

[^spec]: `agent-spec-prompt.md`, section 1.1–1.10.
