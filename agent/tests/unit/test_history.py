"""recent_history：從 session events 取出給意圖分類用的對話紀錄。"""

from google.adk.events.event import Event
from google.genai import types

from quotation_agent.agent import recent_history

QT = "QT-20260330-001"


def _event(author: str, text: str, path: str = "") -> Event:
    role = "user" if author == "user" else "model"
    event = Event(author=author, content=types.Content(role=role, parts=[types.Part.from_text(text=text)]))
    if path:
        event.node_info.path = path
    return event


def test_keeps_user_messages_and_final_replies_only():
    events = [
        _event("user", "我要複製報價單"),
        _event("classify_intent", '{"intent": "duplicate_quotation"}', "quotation_agent@1/classify_intent@1"),
        _event("quotation_agent", "請提供報價單編號", "quotation_agent@1/respond@1"),
        _event("user", QT),
    ]
    assert recent_history(events, QT) == [("使用者", "我要複製報價單"), ("助手", "請提供報價單編號")]


def test_injected_history_without_node_path_is_kept():
    # agents-cli eval 塞進 session 的前幾輪事件沒有 nodeInfo.path。
    events = [_event("user", "我要複製報價單"), _event("agent", "請提供報價單編號")]
    assert recent_history(events, QT) == [("使用者", "我要複製報價單"), ("助手", "請提供報價單編號")]
