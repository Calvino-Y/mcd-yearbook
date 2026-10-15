# WorkBuddy 开发记录 · workbuddy.md

本项目（麦门年报 / mcd-yearbook）使用 **WorkBuddy** 完成创意构思、开发与调试，
用于申请麦当劳程序员创意开发大赛的 WorkBuddy 专项奖励。

## 开发环境

- 工具：WorkBuddy（Agent 模式）
- 麦当劳 MCP：通过 WorkBuddy 自定义连接器接入 `https://mcp.mcd.cn`（Streamable HTTP + Bearer Token）
- 本地运行时：Python 3.13、Node.js 22、无头 Chrome（均为 WorkBuddy 托管或本机已有，未污染系统环境）

## 开发过程

### 1. 赛题分析与赛道选择

- WorkBuddy 抓取大赛官方仓库与 `mcd-mcp-server` 仓库，梳理**必须提交的文件清单**、
  **报名 Issue 格式**、**按 Star 数排名**、**2026-10-25 23:59 截止**等硬约束
- 拉取官方 `RANKING.md`，统计已报名项目分布，发现「订单数据可视化 / 年度总结」
  方向虽有竞品（mcd-receipt-persona 33★）但都没做可视化，
  传播型内容（Wrapped 类）在 Star 榜上有天然优势

### 2. 用真实数据而不是编数据

让 WorkBuddy 实际调用 MCP：

- `order-list` → 10 笔真实历史订单（含套餐子项展开）
- `list-nutrition-foods` → 158 项餐品营养数据
- `query-my-account` → 积分账户（预留为年报的积分资产扩展点）
- `campaign-calendar` → 活动日历（预留为「你是在哪个活动期间下的单」扩展点）

**从第一天就定下原则：订单是真实的，营养是真实的，匹配不上的就标注覆盖率，不填估算值。**

### 3. 数据管线

- `scripts/build_yearbook.py`：展开订单到单品粒度、时段/月份/门店聚合、营养对齐、人格判定
- **实测修正**：纯单品（如「柠檬脆脆麦旋风」）的 `comboItemList` 是空数组，
  回退成父项时会 `KeyError: 'name'`——因为父项字段叫 `productName` 不是 `name`。已修复
- **实测修正**：钠→食盐换算写错，`2777 mg` 被算成 `0.01 g`（多除了一次 1000）。
  正确为 `2777 × 2.54 / 1000 = 7.05 g`。已修复并在代码里注明 39.3% 质量分数的来源

### 4. 人格判定做成可解释规则

不做黑盒打分。`麦门忠诚股东 / 深夜食堂常驻嘉宾 / 下班慰劳型选手 / 工作日干饭担当 /
早八续命大师 / 下午茶点单机` 由一组 if/else 得出，并输出判定依据原文
（「最常在午餐下单（5/10 单），最爱 培根芝士双牛堡（7 次）」）。

理由：Wrapped 类内容能不能被分享，取决于用户相不相信这个标签。

### 5. 可视化

- `assets/yearbook-template.html`：Wrapped 风格，麦当劳本品牌配色
  （红 `#DA291C` / 黄 `#FFC72C` / 奶油底），每个板块换底色形成翻页节奏
- 用无头 Chrome `--screenshot` 实测渲染，迭代了三轮截图确认视觉效果

### 6. 修复过一个很有意思的 Bug

第一版页面在浏览器里渲染出来是一片空白：所有动态数字都是占位符 `–`，
但 Node 里跑同一段脚本完全正常。

排查过程：

1. 先怀疑 JSON 注入失败 → 排除
2. 用 Node + DOM 桩跑 → 无异常
3. 用 Chrome `--dump-dom` → 确认静态内容在、动态内容不在
4. 注入 `window.onerror` → **没捕获到**（因为 onerror 也要靠脚本执行，而脚本根本没执行）
5. 改成把错误**写进 DOM**（`document.body.appendChild`）→ 终于抓到：

```
Uncaught SyntaxError: Identifier 'top' has already been declared
```

根因：经典脚本的**顶层 `const top`** 与全局不可配置属性 `window.top` 冲突，
整个 script 在解析阶段就失败，且页面上没有任何可见报错。

修复：改名为 `topBucket`，并把这条坑位记录写进 `SKILL.md`，
提醒后续开发者避开 `top` / `name` / `length` / `location` 这类名字。

这个 Bug 的价值在于：它解释了「为什么页面空白却毫无报错」，
而这类问题在传统开发里往往要耗掉半天。

## 使用 WorkBuddy 的价值

1. **连接器直接调 MCP**：对话里就能实测每个 Tool 的真实返回，不用自己搭调试环境
2. **从数据反推产品**：是 `query-my-account` 返回的 `expiredPoint: 1537.8`
   触发了另一个项目的创意，也是 `order-list` 只有 10 笔这个事实，
   决定了本项目必须诚实标注「近期」而不是假装「年度」
3. **浏览器实测闭环**：WorkBuddy 能起无头浏览器截图、dump DOM、注入探针，
   把「看起来对」变成「验证过对」

## 复现本记录

本文件为人工整理的开发过程摘要。WorkBuddy 会话中的完整对话与工具调用记录
可在 WorkBuddy 会话历史中导出。
