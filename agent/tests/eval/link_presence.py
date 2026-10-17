"""link_present：程式判定回覆是否含純文字系統連結（spec 1.8、2.7）。

規則：
1. 出現 Markdown 連結 [文字](網址) → 0 分。
2. eval_case_id 以 off_topic 開頭的案例 → 1 分（拒答不需要連結）。
3. 其他案例：回覆必須含 http(s)://…/quotations/<id> 或 /orders/<id> → 1 分，否則 0 分。
"""

import re

_LINK = re.compile(r"https?://\S+/(quotations|orders)/\d+")
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")


def _response_text(instance) -> str:
    response = instance.get("response") or {}
    if isinstance(response, str):
        return response
    parts = response.get("parts") or []
    return "".join(p.get("text", "") for p in parts if isinstance(p, dict))


def evaluate(instance):
    text = _response_text(instance)
    case_id = str(instance.get("eval_case_id", ""))

    if _MARKDOWN_LINK.search(text):
        return {"score": 0, "explanation": "回覆使用了 Markdown 連結語法，spec 要求純文字連結"}
    if case_id.startswith("off_topic"):
        return {"score": 1, "explanation": "拒答案例不需要連結"}
    if _LINK.search(text):
        return {"score": 1, "explanation": "回覆包含純文字系統連結"}
    return {"score": 0, "explanation": "回覆缺少 /quotations/<id> 或 /orders/<id> 的純文字連結"}
