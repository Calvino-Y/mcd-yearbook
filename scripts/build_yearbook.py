#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把麦当劳 MCP 的历史订单整理成一份「麦门年报」数据集。

数据来源（全部真实，零编造）：
  * 订单      tool: order-list          -> data/orders_raw.json
  * 营养成分  tool: list-nutrition-foods -> data/nutrition_raw.txt

诚实原则：
  订单里只有部分单品能和营养表对上号。对不上的（比如「培根芝士双牛堡」
  官方营养表里没有这一项）就如实标记为未匹配，并统计覆盖率。
  我们宁可让年报少一个数字，也不放一个编出来的数字。
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORDERS = ROOT / "data" / "orders_raw.json"
NUTRITION = ROOT / "data" / "nutrition_raw.txt"
OUT = ROOT / "data" / "yearbook.json"

TIME_BUCKETS = [
    ("早餐", 5, 10), ("午餐", 10, 14), ("下午茶", 14, 17),
    ("晚餐", 17, 21), ("夜宵", 21, 25),
]


def parse_nutrition() -> dict[str, dict]:
    table: dict[str, dict] = {}
    for line in NUTRITION.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("[", "{")):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 9:
            continue
        try:
            num = [float(x) for x in parts[2:]]
        except ValueError:
            continue
        table[parts[0]] = {
            "energyKcal": num[1], "protein": num[2], "fat": num[3],
            "carbs": num[4], "sodium": num[5], "calcium": num[6],
        }
    return table


def load_orders() -> list[dict]:
    raw = json.loads(ORDERS.read_text(encoding="utf-8"))
    return raw["orders"], raw["source"]


def bucket_of(hour: int) -> str:
    for name, lo, hi in TIME_BUCKETS:
        if lo <= hour < hi:
            return name
    return "深夜"


def main() -> int:
    orders, source = load_orders()
    nutrition = parse_nutrition()

    total_spend = sum(float(o["realTotalAmount"]) for o in orders)
    dates = [datetime.strptime(o["createTime"], "%Y-%m-%d %H:%M:%S") for o in orders]
    first, last = min(dates), max(dates)
    span_days = (last - first).days or 1

    # ---------- 餐品维度 ----------
    item_qty: Counter[str] = Counter()
    item_orders: Counter[str] = Counter()      # 出现在几笔订单里
    unmatched_qty = 0
    matched_qty = 0
    kcal = protein = fat = sodium = 0.0
    unmatched_names: Counter[str] = Counter()

    for o in orders:
        seen: set[str] = set()
        for prod in o["orderProductList"]:
            # 有套餐组成就走子项；纯单品（如「柠檬脆脆麦旋风」）自身就是一条明细
            subs = prod.get("comboItemList") or [
                {"name": prod["productName"], "quantity": prod["quantity"]}
            ]
            for sub in subs:
                name, qty = sub["name"], int(sub["quantity"])
                item_qty[name] += qty
                if name not in seen:
                    item_orders[name] += 1
                    seen.add(name)
                row = nutrition.get(name)
                if row:
                    matched_qty += qty
                    kcal += row["energyKcal"] * qty
                    protein += row["protein"] * qty
                    fat += row["fat"] * qty
                    sodium += row["sodium"] * qty
                else:
                    unmatched_qty += qty
                    unmatched_names[name] += qty

    total_item_qty = matched_qty + unmatched_qty
    coverage = round(matched_qty / total_item_qty * 100) if total_item_qty else 0

    # ---------- 门店与时段 ----------
    stores = Counter(o["storeName"] for o in orders)
    buckets = Counter(bucket_of(d.hour) for d in dates)
    hours = Counter(d.hour for d in dates)
    monthly = Counter(d.strftime("%Y-%m") for d in dates)
    spend_by_month: dict[str, float] = {}
    for o, d in zip(orders, dates):
        key = d.strftime("%Y-%m")
        spend_by_month[key] = round(spend_by_month.get(key, 0) + float(o["realTotalAmount"]), 1)

    # ---------- 人格判定（规则可解释，不做黑盒打分） ----------
    top_item, top_qty = item_qty.most_common(1)[0]
    top_bucket, top_bucket_n = buckets.most_common(1)[0]
    loyalty = top_qty / total_item_qty * 100

    PERSONA_BY_BUCKET = {
        "夜宵": "深夜食堂常驻嘉宾", "晚餐": "下班慰劳型选手",
        "午餐": "工作日干饭担当", "早餐": "早八续命大师",
        "下午茶": "下午茶点单机",
    }
    if loyalty >= 50:
        persona = "麦门忠诚股东"
        reason = f"{top_item} 占你全部 {total_item_qty} 件餐品里的 {loyalty:.0f}%"
    else:
        persona = PERSONA_BY_BUCKET.get(top_bucket, "随心而食型选手")
        reason = (f"最常在{top_bucket}下单（{top_bucket_n}/{len(orders)} 单），"
                  f"最爱 {top_item}（{top_qty} 次）")

    yearbook = {
        "source": {**source,
                   "nutritionTool": "list-nutrition-foods",
                   "orderCount": len(orders)},
        "period": {
            "first": first.strftime("%Y.%m.%d"),
            "last": last.strftime("%Y.%m.%d"),
            "spanDays": span_days,
        },
        "headline": {
            "totalSpend": round(total_spend, 1),
            "orderCount": len(orders),
            "avgPerOrder": round(total_spend / len(orders), 1),
            "itemCount": total_item_qty,
            "distinctItems": len(item_qty),
            "ordersPerMonth": round(len(orders) / max(len(monthly), 1), 1),
        },
        "topItems": [
            {"name": n, "qty": q, "orders": item_orders[n],
             "share": round(q / total_item_qty * 100, 1)}
            for n, q in item_qty.most_common(8)
        ],
        "stores": [
            {"name": n, "orders": c, "share": round(c / len(orders) * 100)}
            for n, c in stores.most_common()
        ],
        "timeBuckets": [
            {"name": n, "orders": buckets.get(n, 0)} for n, _, _ in TIME_BUCKETS
        ],
        "hourHistogram": [
            {"hour": h, "orders": hours.get(h, 0)} for h in range(24)
        ],
        "monthly": [
            {"month": m, "orders": monthly.get(m, 0),
             "spend": spend_by_month.get(m, 0.0)}
            for m in sorted(set(monthly) | set(spend_by_month))
        ],
        "nutrition": {
            "coverage": coverage,
            "matchedQty": matched_qty,
            "unmatchedQty": unmatched_qty,
            "unmatchedNames": [{"name": n, "qty": q} for n, q in unmatched_names.most_common()],
            "energyKcal": round(kcal),
            "protein": round(protein),
            "fat": round(fat),
            "sodium": round(sodium),
            "proteinEggEquivalent": round(protein / 7),      # 一个鸡蛋约 7g 蛋白
            # 钠→食盐：食盐中钠的质量分数约 39.3%，所以 1 g 钠 ≈ 2.54 g 盐
            "sodiumSaltGrams": round(sodium * 2.54 / 1000, 2),
        },
        "persona": {"label": persona, "reason": reason,
                    "loyaltyPercent": round(loyalty)},
    }

    OUT.write_text(json.dumps(yearbook, ensure_ascii=False, indent=2), encoding="utf-8")

    h = yearbook["headline"]
    print(f"订单 {h['orderCount']} 笔 · 消费 ¥{h['totalSpend']} · "
          f"{h['itemCount']} 件餐品 · 覆盖 {period_str(yearbook)}")
    print(f"本命：{top_item} ×{top_qty}（{loyalty:.0f}%）· 人格：{persona}")
    print(f"营养匹配率 {coverage}% · 已匹配热量 {yearbook['nutrition']['energyKcal']} kcal")
    return 0


def period_str(yb: dict) -> str:
    return f"{yb['period']['first']}–{yb['period']['last']}"


if __name__ == "__main__":
    raise SystemExit(main())
