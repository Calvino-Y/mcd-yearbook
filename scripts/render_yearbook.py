#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 data/yearbook.json 注入 assets/yearbook-template.html，产出 docs/index.html。

和 mcd-muscle-coach 的渲染器同构：换一个账号、重新拉一次订单，
重跑一遍就能得到属于你自己的那份麦门年报。
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets" / "yearbook-template.html"
DATASET = ROOT / "data" / "yearbook.json"
OUT = ROOT / "docs" / "index.html"


def main() -> int:
    payload = DATASET.read_text(encoding="utf-8").strip()
    html = TEMPLATE.read_text(encoding="utf-8")
    if "/*__DATA__*/" not in html:
        raise SystemExit("模板里找不到 /*__DATA__*/ 占位符")
    html = html.replace("/*__DATA__*/", payload)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"已生成 {OUT.relative_to(ROOT)}（{len(html.encode('utf-8'))/1024:.1f} KB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
