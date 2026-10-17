"""Workflow 節點之間傳遞的資料結構。"""

from typing import Literal

from pydantic import BaseModel, Field

# 六個報價單操作，名稱與 MCP Server 的工具名、Workflow 的操作節點名、route 名稱一致。
Operation = Literal[
    "get_quotation",
    "list_customer_quotations",
    "duplicate_quotation",
    "update_pricing_factor",
    "adjust_total_price",
    "convert_to_order",
]

Intent = Literal[
    "get_quotation",
    "list_customer_quotations",
    "duplicate_quotation",
    "update_pricing_factor",
    "adjust_total_price",
    "convert_to_order",
    "provide_info",
    "off_topic",
]


class IntentResult(BaseModel):
    """意圖分類節點（LLM）的結構化輸出。只描述「使用者說了什麼」，不決定要做什麼。"""

    intent: Intent = Field(
        description=(
            "使用者這一句話的意圖。六個報價單操作之一；"
            "只補充資料（例如只給報價單編號或數值）而沒有說要做什麼時用 provide_info；"
            "其餘與報價單管理無關的一律 off_topic。"
        )
    )
    quotation_number: str | None = Field(
        default=None, description="報價單編號，格式如 QT-20260330-001；沒提到則為 null。"
    )
    customer_name: str | None = Field(
        default=None, description="客戶名稱，例如「史塔克工業」；沒提到則為 null。"
    )
    new_pricing_factor: float | None = Field(
        default=None, description="新的報價因子，例如 1.5；沒提到則為 null。"
    )
    target_total_price: float | None = Field(
        default=None, description="目標總價，例如 8000；沒提到則為 null。"
    )
    system_error: str | None = Field(
        default=None, description="系統保留欄位，一律輸出 null。"
    )


class OperationRequest(BaseModel):
    """route 節點交給操作節點的輸入：已驗證、齊全的工具參數。"""

    operation: Operation
    args: dict[str, str | float]


class ClarifyRequest(BaseModel):
    """route 節點交給 clarify 節點的輸入。operation 為 None 表示還不知道要做哪個操作。"""

    operation: Operation | None
    missing: list[str]
    args: dict[str, str | float]
    english: bool = False


class RefuseRequest(BaseModel):
    english: bool = False
