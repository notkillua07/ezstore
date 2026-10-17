"""透過 ADK McpToolset 連接 EZStore MCP Server（Streamable HTTP）。"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from google.adk.agents.context import Context
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from .routing import OPERATIONS

logger = logging.getLogger(__name__)

MCP_URL = os.environ.get("MCP_URL", "http://localhost:8010/mcp")

toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_URL,
        timeout=30.0,
        # adjust_total_price 最多迭代 20 次 PUT，要留足讀取時間。
        sse_read_timeout=180.0,
    ),
    tool_filter=list(OPERATIONS),
)

_tools: dict[str, BaseTool] = {}
_TOOL_ERROR_PREFIX = re.compile(r"^Error executing tool \w+:\s*")


@dataclass
class ToolOutcome:
    text: str
    is_error: bool


async def _get_tool(name: str) -> BaseTool:
    if name not in _tools:
        for tool in await toolset.get_tools():
            _tools[tool.name] = tool
    return _tools[name]


def _result_text(result: Any) -> ToolOutcome:
    """把 McpTool 的回傳（CallToolResult dump 或 {"error": ...}）轉成文字。"""
    if isinstance(result, dict):
        if "error" in result and "content" not in result:
            return ToolOutcome(str(result["error"]), True)
        texts = [
            c.get("text", "")
            for c in result.get("content") or []
            if isinstance(c, dict) and c.get("type", "text") == "text"
        ]
        is_error = bool(result.get("isError") or result.get("is_error"))
        text = "\n".join(t for t in texts if t).strip()
        if is_error:
            # MCP SDK 會在 ToolError 前加上「Error executing tool <name>: 」，使用者不需要看到。
            text = _TOOL_ERROR_PREFIX.sub("", text)
        return ToolOutcome(text, is_error)
    return ToolOutcome(str(result), False)


async def call_tool(ctx: Context, name: str, args: dict[str, Any]) -> ToolOutcome:
    """呼叫一個 MCP 工具；連線或工具錯誤都轉成 ToolOutcome(is_error=True)，不丟例外。"""
    try:
        tool = await _get_tool(name)
    except Exception as e:  # noqa: BLE001 — MCP Server 沒開時要回清楚的訊息
        logger.exception("Cannot reach MCP server at %s", MCP_URL)
        _tools.clear()
        return ToolOutcome(f"無法連線 MCP Server（{MCP_URL}）：{e}", True)

    try:
        result = await tool.run_async(args=args, tool_context=ctx)
    except Exception as e:  # noqa: BLE001
        logger.exception("MCP tool %s failed", name)
        _tools.clear()
        return ToolOutcome(f"MCP 工具 {name} 執行失敗：{e}", True)
    return _result_text(result)
