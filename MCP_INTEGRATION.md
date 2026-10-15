# MCP 集成说明 · MCP_INTEGRATION

本文说明本项目实际使用的麦当劳 MCP Server、每个 Tool 的用途、调用流程，以及这些数据带来的业务价值。

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| Server 名称 | `mcd-mcp`（麦当劳中国官方 MCP Server） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权方式 | `Authorization: Bearer <MCP_TOKEN>` 请求头 |
| Token 获取 | https://open.mcd.cn/mcp → 手机号登录 → 控制台激活 |
| 限流 | 600 次/分钟，超限返回 429 |

客户端实现见 `scripts/mcd_client.py`，仅用 Python 标准库 `urllib`，零第三方依赖。

**实现要点**：

- 请求头必须同时声明 `Accept: application/json, text/event-stream`，只声明 `application/json` 会拿不到响应。
- `initialize` 成功后，服务端可能通过响应头下发 `Mcp-Session-Id`，**后续所有请求都要原样带回**。
- 响应可能是纯 JSON，也可能是 SSE（`data: {...}` 逐行），客户端两种都要能解。
- `initialize` 之后按规范补一条 `notifications/initialized` 通知（无 id、无需等待响应）。

## 2. 使用的 Tool 及用途

### `order-list` — 历史订单（本项目的数据地基）

- **输入**：无参数
- **返回**：近期订单列表，含 `orderId / createTime / storeCode / storeName / orderStatus / realTotalAmount / orderProductList`
- **注意**：只返回**近期**记录，不是全部消费历史。本项目在页面与 README 中都明确标注了实际覆盖区间，**不把「近期」包装成「年度」**
- 套餐订单的 `orderProductList[].comboItemList` 是子项明细；纯单品（如麦旋风）`comboItemList` 为空数组，此时该商品自身就是一条明细

### `list-nutrition-foods` — 营养成分

- **输入**：无参数
- **返回**：158 项餐品的 `productName / energyKcal / protein / fat / carbohydrate / sodium / calcium`
- **在本项目中的角色**：把订单从「花了多少钱」升级成「吃进去多少」

### `query-my-account` — 积分账户（可选增强）

- 返回 `availablePoint / accumulativePoint / currentMouthExpirePoint / expiredPoint` 等
- 在本项目中用于在年报末尾追加「积分资产」一节（当前版本未启用，留作扩展点）

### `campaign-calendar` — 营销活动日历（可选增强）

- 可用于在年报中标注「你在哪些活动期间下的单」，把消费行为和营销节奏对上。当前版本未启用，留作扩展点。

## 3. 调用流程

```
order-list
        │  原始订单（含套餐子项）
        ▼
build_yearbook.py
        │  1. 展开到单品粒度，统计频次
        │  2. 解析 createTime -> 时段 / 小时 / 月份
        │  3. 按门店聚合
        │  4. 与营养表按名称对齐 -> 热量/蛋白/钠（只计匹配成功的）
        │  5. 规则化判定麦门人格（可解释，无黑盒打分）
        ▼
data/yearbook.json
        │
        └─▶ render_yearbook.py  ->  docs/index.html（Wrapped 风格可视化年报）
```

## 4. 关键设计决策

### 4.1 营养覆盖率，而不是假装全覆盖

订单里很多单品在官方营养表里**没有对应条目**（例如「培根芝士双牛堡」「柠檬脆脆麦旋风」）。

两种处理方式：

- ❌ 用相近餐品的营养值近似填充 —— 数字好看，但是编的
- ✅ 只统计匹配成功的部分，并把覆盖率明明白白写在页面上

本项目选后者。实测匹配率 55%（19/33 件）。页面底部有专门的「诚实声明」解释这一点。

### 4.2 人格判定用规则，不用模型打分

`麦门人格` 由一组**可解释的 if/else** 得出：

1. 单品占全部餐品量 ≥ 50% → `麦门忠诚股东`
2. 否则按下单最多的时段映射：夜宵 → `深夜食堂常驻嘉宾`、晚餐 → `下班慰劳型选手`、午餐 → `工作日干饭担当`、早餐 → `早八续命大师`、下午茶 → `下午茶点单机`
3. 附上判定依据原文（「最常在午餐下单（5/10 单），最爱 培根芝士双牛堡（7 次）」）

用户能看到为什么，才愿意截图分享。

### 4.3 时段映射的边界

`21:11` 属于「夜宵」（21–24 点）而不是「晚餐」，这个边界写死在 `TIME_BUCKETS` 里。改的时候注意 `bucket_of()` 用的是 `lo <= hour < hi`，且夜宵区间写成 `21..25` 以容纳跨零点订单。

## 5. 业务价值

**把一串订单号变成一份愿意发朋友圈的年度总结。**

- 对用户：麦当劳的 App 只给你看「最近一笔」，从不给你看「你是谁」。这份年报补上了自我认知那一块。
- 对麦当劳：Wrapped 类内容的转发率远高于优惠券，是几乎零成本的自来水传播。
- 对 MCP 生态：示范了 `order-list` + `list-nutrition-foods` 怎么组合出「个性化数据叙事」这类高价值场景，而不是停留在查订单。

## 6. 隐私与合规

- **本仓库不包含任何真实账号的 Token、openId 或手机号**。
- `data/orders_raw.json` 中的 `orderId` 已全部替换为 `ORD-0001` 形式的占位符，原始订单号不随仓库公开；`storeName` 是公开的门店名称，不构成个人敏感信息。如需以自己的数据运行，替换该文件即可。
- 年报页面默认展示的是**仓库作者自己的脱敏数据**；他人复用时通过 `build_yearbook.py` 重新生成，不会上传任何数据。
