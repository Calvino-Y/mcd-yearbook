---
name: mcd-yearbook
description: >
  麦门年报。当用户想看「我的麦当劳消费总结」「我在麦当劳花了多少钱」「我常点什么」
  「我的麦当劳年度账单」「麦当劳年度报告」「我的麦门人格」时使用。
  基于麦当劳 MCP 返回的真实历史订单与官方营养数据，生成一份 Wrapped 风格、
  可直接截图分享的可视化年报，含消费统计、本命餐品、时段画像、门店足迹、
  营养换算与人格认证。
  This skill should be used when a user wants a personalized McDonald's China
  spending recap, order-history insights, or a shareable Wrapped-style yearbook.
agent_created: true
license: MIT
---

# 麦门年报

把一串订单号，变成一份愿意发朋友圈的年度总结。

## 什么时候用这个 Skill

触发场景：

- 「我的麦当劳年度账单」「我在麦当劳花了多少钱」
- 「我常在麦当劳点什么」「我的本命汉堡是哪个」
- 「给我生成一份麦当劳年报」
- 「我是不是麦门忠诚用户」

## 工作流

### 第 1 步：确认 Token

需要环境变量 `MCD_MCP_TOKEN`（https://open.mcd.cn/mcp 免费激活）。缺失时告知申请方式。

### 第 2 步：取数与构建

```bash
python scripts/build_yearbook.py     # 订单 + 营养 -> data/yearbook.json
python scripts/render_yearbook.py    # -> docs/index.html
```

需要重新拉订单时：

```bash
export MCD_MCP_TOKEN="..."
python scripts/mcd_client.py call order-list
```

把返回写入 `data/orders_raw.json`（保持 `{"source":..., "orders":[...]}` 结构）后重跑上面两条命令。

### 第 3 步：输出

构建脚本会打印核心数字。回答用户时务必带上：

- 覆盖时间区间（**是「近期」不是「全年」**，MCP 只返回近期订单）
- 累计消费、订单数、平均每单
- 本命餐品及占比
- 人格标签与判定依据

然后展示 `docs/index.html`。

## 必须遵守的约束

1. **不要把「近期」说成「年度」。** `order-list` 只返回近期订单。页面标题写「麦门年报」，
   但时间区间必须如实展示，并且要说明这是 MCP 可返回的范围。
2. **营养数据必须标注覆盖率。** 很多在售单品（如培根芝士双牛堡）不在官方营养表里。
   只统计匹配成功的部分，覆盖率写在页面上。**宁可少报，不要编造。**
3. **人格判定要可解释。** 输出必须附上判定依据（哪个人物规则命中、依据是什么数字），
   不做黑盒打分。用户看到「为什么」，才愿意截图分享。
4. **隐私优先。** `data/orders_raw.json` 含订单号与门店信息，属于个人数据。
   不要把它贴到公开场合，也不要在回复中复述完整订单号。

## 常见坑

- **顶层 `const top` 会让整段脚本静默失效。** 经典脚本的顶层 `const` 若与
  `window` 上的既有属性（如 `window.top`）同名，直接 SyntaxError，
  且页面上看不到任何报错——整个年报就是一片空白。已改为 `topBucket`，
  新增变量时避开 `top` / `name` / `length` / `location` 这类名字。
- **纯单品的 `comboItemList` 是空数组。** 回退时要用 `productName` 字段，
  不是 `name`。
- **钠→食盐换算**：食盐中钠的质量分数约 39.3%，即 1 g 钠 ≈ 2.54 g 盐。
  别把单位换算错两次。

## 参考

- 工具参数与坑位记录：`references/mcp-tools.md`
- 数据来源与设计决策：`MCP_INTEGRATION.md`
