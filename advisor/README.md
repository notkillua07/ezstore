# EZStore Sales Advisor (bonus agent)

A second agent for the EZStore workshop. It answers sales questions from an **OKF knowledge bundle** and hands
quotation work to the first agent (`quotation_agent`) over the **A2A protocol**.

```
User ─▶ sales_advisor (ADK LlmAgent, Gemini)
          ├─ tools: read_concepts · search_knowledge (index in the prompt)─▶ knowledge/ezstore (OKF v0.2 bundle)
          └─ sub-agent: quotation_agent (RemoteA2aAgent) ──A2A──▶ agent:8080/a2a/quotation_agent ─▶ MCP ─▶ backend
```

| Question type | What the advisor does | Example |
|---|---|---|
| Policies, pricing, products | Searches the knowledge bundle, reads the concepts, answers with sources | 「VIP 客戶買 10 箱 SP-001，單價和總價？」 → 520 per box, 5,200 total, 來源：products/SP-001, policies/customer-levels |
| Quotation operations | Transfers to `quotation_agent` over A2A and returns its reply with links | 「幫我把報價單 QT-20260330-001 轉成訂單」 → ORD-… + order link |
| Anything else | Politely declines | 「今天天氣如何？」 |

## Files

| Path | Purpose |
|---|---|
| `sales_advisor/agent.py` | The advisor (`LlmAgent`), its instruction, and the `RemoteA2aAgent` for `quotation_agent` |
| `sales_advisor/knowledge.py` | Reads the OKF bundle: `read_concepts`, `search_knowledge`, `read_concept`, `list_knowledge`, trust tier |
| `knowledge/ezstore/` | OKF v0.2 bundle: 5 policies, 1 agent guide, 20 products (index.md, log.md) |
| `scripts/okf_tool.py` | Regenerates product concepts from the backend API, rebuilds index.md, validates the bundle |
| `a2a/quotation_agent_card.json` | The quotation agent's A2A card for Docker (see "A2A notes") |

## OKF knowledge bundle

Open Knowledge Format v0.2 (https://github.com/GoogleCloudPlatform/open-knowledge-format): one Markdown file per
concept with YAML frontmatter (`type`, `title`, `description`, `sources`, `generated`, …), linked with relative links.

```bash
python advisor/scripts/okf_tool.py products   # regenerate products/*.md from http://localhost:8080/api/v1
python advisor/scripts/okf_tool.py index      # rebuild index.md files
python advisor/scripts/okf_tool.py validate   # conformance check (spec section 11)
```

Every concept is "unverified" until a person reviews it and adds `verified: {by: "human:<name>", at: …}`;
`read_concept` reports the trust tier to the agent.

## A2A notes

- The quotation agent serves A2A at `/a2a/quotation_agent` (scaffolded by agents-cli). Its card advertises `APP_URL`;
  Compose sets `APP_URL=http://agent:8080`.
- ADK only fetches agent cards over https or loopback http. Inside Docker the advisor therefore reads the card from
  `a2a/quotation_agent_card.json` (`QUOTATION_AGENT_CARD`); locally it fetches `http://127.0.0.1:8001/...`.
- The card URL and the URLs inside the card must have the same origin (use `127.0.0.1` on both sides locally).

## Run

Docker (recommended; Vertex AI with your gcloud login):

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml -f docker-compose.vertex.yml up -d --build
# ADK web UI: http://localhost:8090/dev-ui/?app=sales_advisor
```

Local: start the quotation agent with `APP_URL=http://127.0.0.1:8001` on port 8001, then
`cd advisor && cp .env.example .env && uv sync --group dev && agents-cli playground --port 8502`.

Tests: `cd advisor && uv run pytest tests/unit -q` (7 tests, no API key needed).

Known issue on Windows hosts: model calls through the local server sometimes hang when replies are streamed; Docker
(Linux) does not show this. Turn off token streaming in the web UI if it happens locally.

---

## 中文說明

**EZStore 業務顧問 Agent（加分作業）**：第二個 Agent。業務相關問題（客戶等級與報價因子、報價計算、報價單／訂單狀態、產品與價格）
從 **OKF 知識庫**（`knowledge/ezstore/`，Open Knowledge Format v0.2，26 個概念）查詢後回答並附上來源；
報價單操作（查詢、清單、複製、改報價因子、改總價、轉訂單）則透過 **A2A 協定**轉交第一個 Agent（`quotation_agent`）處理，
回覆中保留純文字系統連結；其他需求一律禮貌拒絕。

- 執行：`docker compose -f docker-compose.yml -f docker-compose.build.yml -f docker-compose.vertex.yml up -d --build`，
  開啟 http://localhost:8090/dev-ui/?app=sales_advisor
- 知識庫工具：`python advisor/scripts/okf_tool.py products | index | validate`
- 測試：`cd advisor && uv run pytest tests/unit -q`
- A2A 注意：ADK 只透過 https 或本機 loopback 抓 agent card，所以 Docker 內改讀 `a2a/quotation_agent_card.json`。
