"""route 節點的程式邏輯（不需要 LLM、不需要 MCP Server）。"""

import pytest

from quotation_agent.routing import (
    clarify_message,
    decide,
    is_non_quotation_crud,
    refuse_message,
    strip_markdown_links,
)
from quotation_agent.schemas import IntentResult

QT = "QT-20260330-001"


def intent(name: str, **kw) -> IntentResult:
    return IntentResult(intent=name, **kw)


@pytest.mark.parametrize(
    ("result", "text", "route", "args"),
    [
        (intent("get_quotation", quotation_number=QT), f"我要查詢報價單，報價單編號：{QT}", "get_quotation", {"quotation_number": QT}),
        (intent("list_customer_quotations", customer_name="史塔克工業"), "我要查詢客戶的報價單清單，客戶名稱：史塔克工業", "list_customer_quotations", {"customer_name": "史塔克工業"}),
        (intent("duplicate_quotation", quotation_number=QT), f"我要複製報價單，報價單編號：{QT}", "duplicate_quotation", {"quotation_number": QT}),
        (intent("update_pricing_factor", quotation_number=QT, new_pricing_factor=1.5), f"報價單編號：{QT}，報價因子改為 1.5", "update_pricing_factor", {"quotation_number": QT, "new_pricing_factor": 1.5}),
        (intent("adjust_total_price", quotation_number=QT, target_total_price=8000), f"報價單編號：{QT}，總價改為 8000", "adjust_total_price", {"quotation_number": QT, "target_total_price": 8000.0}),
        (intent("convert_to_order", quotation_number=QT), f"我要將報價單轉訂單，報價單編號：{QT}", "convert_to_order", {"quotation_number": QT}),
    ],
)
def test_each_operation_routes_to_its_tool(result, text, route, args):
    d = decide(result, text, None)
    assert d.route == route
    assert d.payload == {"operation": route, "args": args}
    assert d.pending is None


def test_quotation_number_comes_from_user_text_not_llm():
    # LLM 編造了編號，但使用者原文沒有 → 視為缺少，改為追問。
    d = decide(intent("get_quotation", quotation_number=QT), "我要查詢報價單", None)
    assert d.route == "clarify"
    assert d.payload["missing"] == ["quotation_number"]


def test_lowercase_quotation_number_is_normalised():
    d = decide(intent("get_quotation"), "查詢 qt-20260330-001", None)
    assert d.payload["args"] == {"quotation_number": QT}


def test_off_topic_is_refused_and_clears_pending():
    pending = {"operation": "duplicate_quotation", "args": {}, "missing": ["quotation_number"]}
    d = decide(intent("off_topic"), "今天天氣如何？", pending)
    assert d.route == "refuse"
    assert d.pending is None


@pytest.mark.parametrize(
    "text",
    ["幫我新增一個客戶，名稱叫做韋恩企業", "請刪除產品 A4影印紙", "修改客戶史塔克工業的電話", "add a new customer called Wayne"],
)
def test_customer_or_product_crud_is_refused_even_if_llm_disagrees(text):
    assert is_non_quotation_crud(text)
    d = decide(intent("get_quotation", quotation_number=None), text, None)
    assert d.route == "refuse"


@pytest.mark.parametrize(
    "text",
    ["我要查詢客戶的報價單清單，客戶名稱：史塔克工業", f"我要將報價單轉訂單，報價單編號：{QT}", f"修改報價單 {QT} 的報價因子"],
)
def test_quotation_requests_are_not_caught_by_crud_guard(text):
    assert not is_non_quotation_crud(text)


def test_clarify_then_complete():
    first = decide(intent("duplicate_quotation"), "我要複製報價單", None)
    assert first.route == "clarify"
    assert first.pending == {"operation": "duplicate_quotation", "args": {}, "missing": ["quotation_number"]}
    assert clarify_message(**{k: first.payload[k] for k in ("operation", "missing", "args", "english")}).startswith("請提供")

    second = decide(intent("provide_info", quotation_number=QT), QT, first.pending)
    assert second.route == "duplicate_quotation"
    assert second.payload["args"] == {"quotation_number": QT}
    assert second.pending is None


def test_clarify_keeps_known_args_until_complete():
    first = decide(intent("update_pricing_factor", quotation_number=QT), f"修改報價單 {QT} 的報價因子", None)
    assert first.route == "clarify"
    assert first.payload["missing"] == ["new_pricing_factor"]

    second = decide(intent("provide_info", new_pricing_factor=1.5), "1.5", first.pending)
    assert second.route == "update_pricing_factor"
    assert second.payload["args"] == {"quotation_number": QT, "new_pricing_factor": 1.5}


def test_same_operation_restated_merges_pending_args():
    first = decide(intent("adjust_total_price", target_total_price=8000), "總價改為 8000", None)
    second = decide(intent("adjust_total_price", quotation_number=QT), f"修改報價單總價，報價單編號 {QT}", first.pending)
    assert second.route == "adjust_total_price"
    assert second.payload["args"] == {"quotation_number": QT, "target_total_price": 8000.0}


def test_only_a_quotation_number_asks_which_operation():
    d = decide(intent("provide_info"), QT, None)
    assert d.route == "clarify"
    assert d.payload["operation"] is None
    text = clarify_message(None, ["operation"], d.payload["args"], False)
    assert "請告訴我您要對報價單" in text

    follow_up = decide(intent("convert_to_order"), "轉成訂單", d.pending)
    assert follow_up.route == "convert_to_order"
    assert follow_up.payload["args"] == {"quotation_number": QT}


def test_model_error_routes_to_error_node():
    d = decide(intent("off_topic", system_error="no key"), "hi", None)
    assert d.route == "error"
    assert d.payload == {"message": "no key"}


def test_refusal_wording_matches_grader():
    assert "只能協助" in refuse_message(False)
    assert "Sorry" in refuse_message(True)


def test_english_message_gets_english_hint():
    d = decide(intent("duplicate_quotation"), "please duplicate a quotation", None)
    assert d.payload["english"] is True
    text = clarify_message("duplicate_quotation", ["quotation_number"], {}, True)
    assert text.startswith("請提供") and "Please provide" in text


def test_number_from_earlier_user_message_is_accepted():
    # 多輪案例：這一句沒有編號，但使用者前一句說過 → 接受 LLM 從歷史取出的編號。
    d = decide(intent("duplicate_quotation", quotation_number=QT), "就複製那張", None, f"查詢 {QT}")
    assert d.route == "duplicate_quotation"
    assert d.payload["args"] == {"quotation_number": QT}


def test_number_not_in_any_user_message_is_rejected():
    d = decide(intent("duplicate_quotation", quotation_number=QT), "幫我複製", None, "我要複製報價單")
    assert d.route == "clarify"


def test_strip_markdown_links():
    text = "請看 [報價單](http://localhost:3000/quotations/12) 與 [http://x/orders/3](http://x/orders/3)"
    assert strip_markdown_links(text) == "請看 報價單 http://localhost:3000/quotations/12 與 http://x/orders/3"
