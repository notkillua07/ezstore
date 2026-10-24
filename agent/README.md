# EZStore Quotation Agent

This folder holds the EZStore quotation assistant, built with Google ADK 2.x as a graph Workflow and scaffolded with
agents-cli 1.10. It reaches the EZStore MCP Server through `McpToolset`.

Two names are fixed because the Chat UI and the grading scripts depend on them:
the ADK app is called `quotation_agent`, and the node that produces the final reply is called `respond`.

## Files

| File | Purpose |
|------|---------|
| `quotation_agent/agent.py` | The graph: nodes, edges, `App(name="quotation_agent")` |
| `quotation_agent/schemas.py` | Pydantic models passed between nodes (`IntentResult`, `OperationRequest`, ...) |
| `quotation_agent/routing.py` | Routing rules and fixed replies, plain Python, no LLM |
| `quotation_agent/mcp_tools.py` | `McpToolset` with `StreamableHTTPConnectionParams`, URL from `MCP_URL` |
| `quotation_agent/fast_api_app.py` | FastAPI server (ADK web routes and A2A), used by Docker and by `agents-cli eval` |
| `tests/` | Unit tests, integration tests and the eval suite |

## Graph design

The flow for every user message:

0. `load_context` (code) collects this turn's context into `state["turn_context"]`: the user's text, the pending
   request from an earlier clarification, and the last few messages.
1. `classify_intent` is the only LLM node. It returns an `IntentResult` (intent plus extracted fields).
   Its instruction includes the context from `load_context`, so a short follow-up can continue a task.
2. `route` is plain code. It decides between refusing, asking for missing data, and calling one of the six tools,
   and it builds the tool arguments.
3. One of the branch nodes runs:
   - six operation nodes, one per MCP tool: `get_quotation`, `list_customer_quotations`, `duplicate_quotation`,
     `update_pricing_factor`, `adjust_total_price`, `convert_to_order`
   - `clarify` asks for missing fields and keeps the request in `state.pending_request`
   - `off_topic` returns the fixed refusal
   - `report_error` explains missing credentials, quota limits or model errors
4. `respond` receives the branch text, turns any Markdown link into a plain link, and emits the reply.

Rules enforced in code (not by the prompt):

- Off-topic requests are refused: any intent outside the six operations, plus a regex guard for creating,
  editing or deleting customers, products or orders.
- The quotation number must come from the user's own words (this message or an earlier one).
  A number the LLM made up is dropped and the agent asks for it instead.
- Edit operations always work on a copy (done by the MCP tools); the reply says the original was not modified.

Writing edges in ADK 2.11: a tuple is a chain, a dict is a routing table, and a tuple inside a tuple fans in.

    ("START", classify_intent, route)
    (route, {"get_quotation": get_quotation_node, "clarify": clarify, ...})
    ((get_quotation_node, clarify, off_topic, ...), respond)

The three-item form `(source, target, "route")` shown in some older docs is rejected by ADK 2.11.

## How to add an operation

Example: a new MCP tool `publish_quotation(quotation_number)`.

1. `schemas.py`: add `"publish_quotation"` to both `Operation` and `Intent`.
2. `routing.py`: add it to `OPERATIONS` with its required fields, for example
   `"publish_quotation": ("quotation_number",)`, and give it a label in `OPERATION_LABELS`.
   New field types also need an entry in `FIELD_LABELS` and in `IntentResult`.
3. `agent.py`: describe the new intent in `CLASSIFY_INSTRUCTION`. The operation node and its route are created
   automatically from `routing.OPERATIONS` (`operation_nodes` and the routing table), so no edge needs editing.
   `mcp_tools.py` also reads its tool filter from `OPERATIONS`.
4. Tests: add a case to `tests/unit/test_routing.py`, and an eval case to
   `tests/eval/datasets/quotation-actions.json` with `eval_case_id` equal to the tool name.

## Run and test

Setup (db, backend and mcp-server running in Docker; mcp-server published on host port 8010):

    cp .env.example .env        # fill GEMINI_API_KEY, keep MCP_URL=http://localhost:8010/mcp
    uv sync --group dev --extra eval
    agents-cli playground --port 8501
    uv run pytest tests/unit tests/integration -q
    agents-cli eval run --dataset tests/eval/datasets/quotation-guardrails.json --config tests/eval/eval_config.yaml

Notes:

- The playground's default port 8080 is already used by the backend container, hence `--port 8501`.
- The tests need no API key. The integration tests replace the classifier with a fake and talk to the real MCP Server.
- Grading the `refusal_or_action` metric needs a GCP project (Vertex AI eval service).

---

## 中文說明

EZStore 報價單管理助手，以 Google ADK 2.x 的 Graph Workflow 開發，用 agents-cli 1.10 產生骨架，透過 `McpToolset` 連接 MCP Server。
ADK app 名稱必須是 `quotation_agent`，最終回覆節點必須叫 `respond`（Chat UI 與評分腳本都依賴這兩個名稱）。

### 圖的設計

每一則使用者訊息都從 START 重新跑一次：

0. `load_context`（程式）：把這一輪的上下文存進 `state["turn_context"]`：使用者原文、先前追問留下的待補請求、最近幾則對話。
1. `classify_intent`：唯一呼叫 LLM 的節點，輸出 `IntentResult`（意圖與抽取的欄位）。指令中帶入 `load_context` 整理的上下文，讓簡短的補充訊息能接續原本的操作。
2. `route`：純程式，決定拒答、追問，或呼叫六個工具之一，並組好工具參數。
3. 分支節點：六個操作節點（各呼叫一個 MCP 工具）、`clarify`（追問並把請求存進 `state.pending_request`）、`off_topic`（固定拒答）、`report_error`（憑證、額度或模型錯誤的說明）。
4. `respond`：把 Markdown 連結轉成純文字連結後輸出回覆。

由程式（而非提示詞）保證的規則：六個操作以外一律拒答，另有 regex 防線攔下客戶／產品／訂單的新增修改刪除；報價單編號必須出現在使用者自己的訊息裡，LLM 編造的編號會被丟棄並改為追問；修改類操作一律作用在複本上，回覆會說明原始報價單未被修改。

ADK 2.11 的 edge 寫法：tuple 是依序相連的鏈，dict 是 route 對應節點的路由表，tuple 裡放 tuple 表示多個節點接到同一個節點。舊文件中的三元素寫法 `(來源, 目標, "route")` 在 ADK 2.11 會被拒絕。

### 如何新增一個操作

以新的 MCP 工具 `publish_quotation(quotation_number)` 為例：

1. `schemas.py`：在 `Operation` 與 `Intent` 加入 `"publish_quotation"`。
2. `routing.py`：在 `OPERATIONS` 加入它與必要欄位（例如 `("quotation_number",)`），並在 `OPERATION_LABELS` 加上中文名稱。新的欄位類型還要加進 `FIELD_LABELS` 與 `IntentResult`。
3. `agent.py`：在 `CLASSIFY_INSTRUCTION` 說明新的意圖。操作節點與路由會依 `routing.OPERATIONS` 自動產生，不需要改 edge；`mcp_tools.py` 的工具清單也取自 `OPERATIONS`。
4. 測試：在 `tests/unit/test_routing.py` 加案例，並在 `tests/eval/datasets/quotation-actions.json` 加一個 `eval_case_id` 等於工具名的評估案例。

### 執行與測試

指令同上方英文段落。注意：playground 預設的 8080 已被 backend 容器占用，請加 `--port 8501`；單元與整合測試不需要 API key；`refusal_or_action` 指標評分需要 GCP 專案（Vertex AI eval service）。
