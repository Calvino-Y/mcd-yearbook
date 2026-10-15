# 麦当劳 MCP 工具速查

> 官方仓库：<https://github.com/M-China/mcd-mcp-server> · Token 申请：<https://open.mcd.cn/mcp>

## 本项目用到的

### `order-list`

```
入参：无
返回：近期订单列表（非商城订单）
  orderId / orderType / createTime / beType / beCode / storeCode /
  storeName / orderStatus / realTotalAmount / orderProductList[]
```

- **只返回近期记录**，不是全部历史。不要把它包装成「年度全量数据」
- 套餐订单：`orderProductList[].comboItemList` 是子项明细
- 纯单品：`comboItemList` 为空数组，此时 `productName` 自身就是一条明细
  （踩坑记录：直接把空数组回退成父项会 `KeyError: 'name'`，因为父项字段叫 `productName` 不是 `name`）

### `list-nutrition-foods`

```
入参：无
返回：158 项餐品的营养字段
```

- 用于把订单从「花了多少钱」升级成「吃进去多少」
- 并非所有在售单品都在营养表里，**必须处理未匹配的情况**并上报覆盖率

### `query-my-account`（扩展点）

```
返回：availablePoint / accumulativePoint / frozenPoint /
      currentMouthExpirePoint / nextMouthExpirePoint / expiredPoint
```

可用于在年报中追加「积分资产」一节。

### `campaign-calendar`（扩展点）

```
入参：specifiedDate（可选，yyyy-MM-dd）
返回：当月营销活动，含进行中 / 往期 / 未来
```

可用于在年报中标注「你是在哪个活动期间下的单」。

## 项目未用到、但同一 Server 提供的

`delivery-query-addresses` `delivery-create-address` `delivery-query-stores`
`query-nearby-stores` `query-meals` `query-meal-assistance` `query-meal-detail`
`query-store-coupons` `calculate-price` `create-order` `cancel-order`
`query-order` `available-coupons` `auto-bind-coupons` `query-my-coupons`
`mall-points-products` `mall-product-detail` `mall-create-order`
`mall-order-list` `mall-order-detail` `now-time-info` `query-lottery-info`
`draw-lottery` `query-my-prizes` `query-party-city` `query-party-store`
`query-partystore-date` `query-partystore-session` `party-order-create`

## 通用注意事项

- 限流 600 次/分钟，超限返回 429
- 401 = Token 无效/过期/未提供
- 订单数据属个人数据，展示与分享前需确认已脱敏
