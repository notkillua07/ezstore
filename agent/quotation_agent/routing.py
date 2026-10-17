"""路由規則：依意圖分類結果、使用者原文與上一輪待補資料，用程式決定下一個節點。

這裡沒有任何 LLM 呼叫。LLM 只負責把自然語言轉成 IntentResult，
「要不要拒答、要不要追問、呼叫哪個工具、帶什麼參數」都由本模組決定（spec 1.9、1.10、2.1）。
"""

import re
from dataclasses import dataclass, field
from typing import Any

from .schemas import IntentResult

OPERATIONS: dict[str, tuple[str, ...]] = {
    "get_quotation": ("quotation_number",),
    "list_customer_quotations": ("customer_name",),
    "duplicate_quotation": ("quotation_number",),
    "update_pricing_factor": ("quotation_number", "new_pricing_factor"),
    "adjust_total_price": ("quotation_number", "target_total_price"),
    "convert_to_order": ("quotation_number",),
}

OPERATION_LABELS = {
    "get_quotation": "查詢報價單",
    "list_customer_quotations": "查詢客戶的報價單清單",
    "duplicate_quotation": "複製報價單",
    "update_pricing_factor": "修改報價單報價因子",
    "adjust_total_price": "修改報價單總價",
    "convert_to_order": "將報價單轉為訂單",
}

FIELD_LABELS = {
    "quotation_number": "報價單編號（例如 QT-20260330-001）",
    "customer_name": "客戶名稱（例如 史塔克工業）",
    "new_pricing_factor": "新的報價因子（例如 1.5）",
    "target_total_price": "目標總價（例如 8000）",
}

ARG_FIELDS = tuple(FIELD_LABELS)

_QUOTATION_NUMBER = re.compile(r"QT-\d{8}-\d{3}", re.IGNORECASE)
_CJK = re.compile(r"[一-鿿]")

# 程式層的離題防線：對客戶／產品／訂單做新增、修改、刪除，且沒有提到報價單，一律拒答，
# 不管 LLM 分類成什麼。
_CRUD_VERB = r"(新增|建立|增加|刪除|移除|修改|更改|更新|編輯|add|create|delete|remove|update|edit|change)"
_OTHER_ENTITY = r"(客戶|顧客|產品|商品|訂單|customer|product|order)"
_OTHER_ENTITY_CRUD = re.compile(
    rf"{_CRUD_VERB}.{{0,10}}{_OTHER_ENTITY}|{_OTHER_ENTITY}.{{0,10}}{_CRUD_VERB}",
    re.IGNORECASE,
)
_MENTIONS_QUOTATION = re.compile(r"報價|quotation|quote|QT-\d", re.IGNORECASE)


@dataclass
class Decision:
    """route 的決定。route 是下一個節點名；pending 是要存進 session state 的待補請求。"""

    route: str
    payload: dict[str, Any]
    pending: dict[str, Any] | None = None
    english: bool = False
    notes: list[str] = field(default_factory=list)


def is_english(text: str) -> bool:
    return bool(text.strip()) and not _CJK.search(text)


def is_non_quotation_crud(text: str) -> bool:
    """客戶／產品／訂單的新增修改刪除（且沒提到報價單）→ True。"""
    return bool(_OTHER_ENTITY_CRUD.search(text)) and not _MENTIONS_QUOTATION.search(text)


def _clean_args(result: IntentResult, user_text: str, history_text: str = "") -> dict[str, Any]:
    """從分類結果取出參數並用程式驗證。

    報價單編號以使用者原文的 regex 比對為準；這一句沒有時，接受 LLM 從前幾輪對話取出的編號，
    但前提是它真的出現在使用者先前的訊息裡。兩邊都找不到的編號視為幻覺，丟棄。
    """
    args: dict[str, Any] = {}

    numbers = _QUOTATION_NUMBER.findall(user_text)
    if numbers:
        args["quotation_number"] = numbers[0].upper()
    elif result.quotation_number:
        candidate = result.quotation_number.strip().upper()
        if _QUOTATION_NUMBER.fullmatch(candidate) and candidate in history_text.upper():
            args["quotation_number"] = candidate

    if result.customer_name and result.customer_name.strip():
        args["customer_name"] = result.customer_name.strip()
    if result.new_pricing_factor is not None:
        args["new_pricing_factor"] = float(result.new_pricing_factor)
    if result.target_total_price is not None:
        args["target_total_price"] = float(result.target_total_price)
    return args


def pending_hint(pending: dict[str, Any] | None) -> str:
    """給意圖分類節點的提示字串（透過 state 注入 instruction）。"""
    if not pending:
        return "（無）"
    operation = pending.get("operation")
    known = ", ".join(f"{k}={v}" for k, v in (pending.get("args") or {}).items()) or "無"
    if operation is None:
        return f"上一輪已知參數：{known}；等待使用者說明要對報價單做哪一項操作"
    missing = "、".join(FIELD_LABELS[m] for m in pending.get("missing", []))
    return (
        f"上一輪正在進行「{OPERATION_LABELS[operation]}」，已知參數：{known}；"
        f"等待使用者補充：{missing}"
    )


def decide(
    result: IntentResult,
    user_text: str,
    pending: dict[str, Any] | None,
    history_text: str = "",
) -> Decision:
    """history_text：使用者先前幾輪的訊息原文，只用來驗證 LLM 從歷史取出的報價單編號。"""
    english = is_english(user_text)

    if result.system_error:
        # 模型呼叫失敗（例如沒有設定憑證）。保留待補請求，讓使用者修好後可以重試。
        return Decision("error", {"message": result.system_error}, pending, english)

    intent = result.intent
    if is_non_quotation_crud(user_text):
        intent = "off_topic"

    if intent == "off_topic":
        return Decision("off_topic", {"english": english}, None, english)

    args = _clean_args(result, user_text, history_text)
    operation: str | None

    if intent == "provide_info":
        # 只補資料：接續上一輪的操作。
        operation = pending.get("operation") if pending else None
        if pending:
            args = {**pending.get("args", {}), **args}
    else:
        operation = intent
        if pending and pending.get("operation") in (None, operation):
            args = {**pending.get("args", {}), **args}

    if operation is None:
        if not args:
            return Decision("off_topic", {"english": english}, None, english)
        missing = ["operation"]
        new_pending = {"operation": None, "args": args, "missing": []}
        return Decision(
            "clarify",
            {"operation": None, "missing": missing, "args": args, "english": english},
            new_pending,
            english,
        )

    required = OPERATIONS[operation]
    args = {k: v for k, v in args.items() if k in required}
    missing = [f for f in required if args.get(f) is None]
    if missing:
        new_pending = {"operation": operation, "args": args, "missing": missing}
        return Decision(
            "clarify",
            {"operation": operation, "missing": missing, "args": args, "english": english},
            new_pending,
            english,
        )

    return Decision(operation, {"operation": operation, "args": args}, None, english)


def clarify_message(operation: str | None, missing: list[str], args: dict, english: bool) -> str:
    if operation is None:
        number = args.get("quotation_number", "")
        text = (
            f"請告訴我您要對報價單 {number} 進行哪一項操作："
            "查詢、複製、修改報價因子、修改總價，或轉為訂單。"
        ).replace("報價單  ", "報價單 ")
        if english:
            text += (
                "\n(What would you like to do with this quotation: view, duplicate, "
                "change the pricing factor, change the total price, or convert it to an order?)"
            )
        return text

    fields = "、".join(FIELD_LABELS[m] for m in missing)
    text = f"請提供{fields}，以便為您{OPERATION_LABELS[operation]}。"
    if english:
        names = {
            "quotation_number": "the quotation number (e.g. QT-20260330-001)",
            "customer_name": "the customer name",
            "new_pricing_factor": "the new pricing factor (e.g. 1.5)",
            "target_total_price": "the target total price (e.g. 8000)",
        }
        text += "\n(Please provide " + " and ".join(names[m] for m in missing) + ".)"
    return text


def refuse_message(english: bool) -> str:
    text = (
        "抱歉，我只能協助報價單相關的操作：查詢報價單、查詢客戶的報價單清單、複製報價單、"
        "修改報價因子、修改總價，以及將報價單轉為訂單。其他需求（例如天氣、閒聊、"
        "客戶或產品的新增修改）無法為您處理。"
    )
    if english:
        text += (
            "\n(Sorry, I can only help with quotation tasks: looking up a quotation, listing a "
            "customer's quotations, duplicating, changing the pricing factor or total price, "
            "and converting a quotation to an order.)"
        )
    return text


_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def strip_markdown_links(text: str) -> str:
    """把 [文字](網址) 換成「文字 網址」（spec 1.8：只用純文字連結）。"""

    def _plain(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        return url if label.strip() == url else f"{label} {url}"

    return _MARKDOWN_LINK.sub(_plain, text)
