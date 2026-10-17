---
okf_version: "0.2"
---

# EZStore knowledge bundle

Business rules, product catalog and agent capabilities of the EZStore quotation system,
used by the EZStore Sales Advisor agent. Format: Open Knowledge Format (OKF) v0.2.

## Guides

- [Quotation agent (報價單管理 Agent)](guides/quotation-agent.md) — What the quotation agent can do, the phrasing it understands, and how the sales advisor reaches it over A2A.

## Policies and business rules

- [Copy-on-write for quotation changes (修改前先複製)](policies/copy-on-write.md) — Every change made through the quotation agent is applied to a new copy; the original quotation is never modified.
- [Customer levels and default pricing factors (客戶等級與預設報價因子)](policies/customer-levels.md) — The three customer levels (vip, standard, new) and the pricing factor each one gets by default.
- [Orders and converting a quotation to an order (訂單與報價單轉訂單)](policies/order-lifecycle.md) — Order statuses and what happens when a quotation is converted to an order.
- [How a quotation's price is computed (報價計算方式)](policies/pricing-computation.md) — Unit price, subtotal, total, profit and profit rate formulas the backend applies to every quotation.
- [Quotation lifecycle and numbering (報價單狀態與編號)](policies/quotation-lifecycle.md) — Quotation statuses (draft, published), what can change in each, and the QT-YYYYMMDD-NNN numbering.

## Products

- [商用雷射印表機 LJ-5200 (EQ-001)](products/EQ-001.md) — Office equipment; list price 22000 TWD; supplier 京瓷辦公設備.
- [27吋商用液晶螢幕 M27-Pro (EQ-002)](products/EQ-002.md) — Office equipment; list price 9800 TWD; supplier 明基電通.
- [桌上型碎紙機 SH-200C (EQ-003)](products/EQ-003.md) — Office equipment; list price 3500 TWD; supplier 理想牌事務機.
- [商用投影機 PJ-4500 (EQ-004)](products/EQ-004.md) — Office equipment; list price 28000 TWD; supplier 愛普生台灣.
- [多功能事務機 MF-3800 (EQ-005)](products/EQ-005.md) — Office equipment; list price 45000 TWD; supplier 京瓷辦公設備.
- [企業級無線AP WA-6200 (NT-001)](products/NT-001.md) — Networking; list price 15800 TWD; supplier 合勤科技.
- [24埠 PoE 交換器 SW-2400P (NT-002)](products/NT-002.md) — Networking; list price 22500 TWD; supplier 合勤科技.
- [企業防火牆 FW-500 (NT-003)](products/NT-003.md) — Networking; list price 65000 TWD; supplier 飛塔資安.
- [Cat.6A 網路線 3米 (10條/包) (NT-004)](products/NT-004.md) — Networking; list price 680 TWD; supplier 大同電線電纜.
- [伺服器機櫃 42U (NT-005)](products/NT-005.md) — Networking; list price 32000 TWD; supplier 台達電子.
- [A4影印紙 80磅 (5包/箱) (SP-001)](products/SP-001.md) — Office supplies; list price 650 TWD; supplier 永豐餘造紙.
- [黑色碳粉匣 TK-5200K (SP-002)](products/SP-002.md) — Office supplies; list price 2400 TWD; supplier 京瓷辦公設備.
- [彩色碳粉匣組 TK-5200CMY (SP-003)](products/SP-003.md) — Office supplies; list price 6800 TWD; supplier 京瓷辦公設備.
- [A3繪圖紙 100磅 (100張/包) (SP-004)](products/SP-004.md) — Office supplies; list price 850 TWD; supplier 永豐餘造紙.
- [裝訂膠圈 10mm (100入) (SP-005)](products/SP-005.md) — Office supplies; list price 250 TWD; supplier 利百代文具.
- [Office 365 商務版 (年約/人) (SW-001)](products/SW-001.md) — Software and services; list price 5400 TWD; supplier 台灣微軟.
- [防毒軟體企業版 (年約/台) (SW-002)](products/SW-002.md) — Software and services; list price 1500 TWD; supplier 趨勢科技.
- [ERP系統授權 (年約/5人) (SW-003)](products/SW-003.md) — Software and services; list price 85000 TWD; supplier 鼎新電腦.
- [雲端備份服務 1TB (年約) (SW-004)](products/SW-004.md) — Software and services; list price 12000 TWD; supplier 中華電信.
- [視訊會議系統授權 (年約/間) (SW-005)](products/SW-005.md) — Software and services; list price 28000 TWD; supplier 訊連科技.
