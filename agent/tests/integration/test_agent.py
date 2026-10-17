"""Workflow 整合測試：用假的意圖分類取代 LLM（不需要 API key），其餘節點與 MCP Server 都是真的。

需要 MCP Server 在 MCP_URL（預設 http://localhost:8010/mcp）可連線，否則整組 skip。
"""

import asyncio
import socket
from urllib.parse import urlparse

import pytest
from google.adk.models import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from quotation_agent import agent as agent_module
from quotation_agent.mcp_tools import MCP_URL
from quotation_agent.schemas import IntentResult

QT = "QT-20260330-001"


def _mcp_reachable() -> bool:
    url = urlparse(MCP_URL)
    try:
        with socket.create_connection((url.hostname, url.port or 80), timeout=2):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not _mcp_reachable(), reason=f"MCP Server not reachable at {MCP_URL}")


def _run(monkeypatch, classifications: list[IntentResult], messages: list[str]) -> list[str]:
    """依序送出 messages；每一輪的意圖分類由 classifications 提供。回傳每輪 respond 節點的文字。"""
    queue = list(classifications)

    def fake_classifier(callback_context, llm_request):
        result = queue.pop(0)
        return LlmResponse(
            content=types.Content(role="model", parts=[types.Part.from_text(text=result.model_dump_json())])
        )

    # Workflow 建圖時會複製 LlmAgent，所以要替換圖裡那個節點的 callback。
    node = next(n for n in agent_module.root_agent.graph.nodes if n.name == "classify_intent")
    monkeypatch.setattr(node, "before_model_callback", fake_classifier)

    async def go() -> list[str]:
        runner = InMemoryRunner(app=agent_module.app)
        session = await runner.session_service.create_session(app_name=agent_module.APP_NAME, user_id="test")
        replies = []
        for msg in messages:
            reply = ""
            async for event in runner.run_async(
                user_id="test",
                session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=msg)]),
            ):
                path = event.node_info.path if event.node_info else ""
                text = "".join(p.text or "" for p in (event.content.parts if event.content else []))
                if text and "/respond@" in path:
                    reply = text
            replies.append(reply)
        return replies

    return asyncio.run(go())


def test_get_quotation_reply_has_items_and_plain_link(monkeypatch):
    [reply] = _run(monkeypatch, [IntentResult(intent="get_quotation", quotation_number=QT)], [f"查詢報價單 {QT}"])
    assert QT in reply
    assert "品項" in reply
    assert "http://localhost:3000/quotations/" in reply
    assert "](" not in reply


def test_off_topic_is_refused_without_calling_tools(monkeypatch):
    [reply] = _run(monkeypatch, [IntentResult(intent="off_topic")], ["今天天氣如何？"])
    assert "只能協助" in reply
    assert "/quotations/" not in reply


def test_clarify_then_complete(monkeypatch):
    replies = _run(
        monkeypatch,
        [IntentResult(intent="get_quotation"), IntentResult(intent="provide_info", quotation_number=QT)],
        ["我要查詢報價單", QT],
    )
    assert replies[0].startswith("請提供")
    assert QT in replies[1] and "/quotations/" in replies[1]


def test_not_found_is_reported_honestly(monkeypatch):
    missing = "QT-20990101-001"
    [reply] = _run(monkeypatch, [IntentResult(intent="get_quotation", quotation_number=missing)], [f"查詢 {missing}"])
    assert reply.startswith("操作失敗")
    assert "找不到" in reply


def test_missing_credentials_gives_clear_error(monkeypatch):
    monkeypatch.setattr(agent_module, "_has_credentials", lambda: False)
    # 不替換分類器：讓真正的 check_credentials callback 攔下來。
    async def go() -> str:
        runner = InMemoryRunner(app=agent_module.app)
        session = await runner.session_service.create_session(app_name=agent_module.APP_NAME, user_id="test")
        reply = ""
        async for event in runner.run_async(
            user_id="test",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text="hi")]),
        ):
            text = "".join(p.text or "" for p in (event.content.parts if event.content else []))
            if text and "/respond@" in (event.node_info.path if event.node_info else ""):
                reply = text
        return reply

    reply = asyncio.run(go())
    assert "尚未設定" in reply and "GEMINI_API_KEY" in reply

