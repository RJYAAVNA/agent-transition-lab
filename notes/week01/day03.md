# Day03 - Real Tool Integration

## 今日目标

把 mock tool 换成真实外部数据能力，并理解两种不同的数据获取方式：

```text
RSS: 指定数据源 -> 一组条目
Search: 研究主题 -> 搜索结果
```

## RSS Tool

`RSSFeedTool` 负责：

1. 校验 feed URL。
2. 发起 HTTP GET。
3. 设置 User-Agent 和 timeout。
4. 使用 `feedparser` 解析 RSS/Atom。
5. 清理 HTML 和多余空白。
6. 转换为 `RSSItem` 列表。

RSS 是 source-driven。调用方先指定信息源，工具再读取该源的最新内容。

## Search Tool

`SearchTool` 负责：

1. 校验非空 query。
2. 校验结果数量范围。
3. 拼接 provider 请求参数。
4. 发起 HTTP GET。
5. 解析 provider JSON。
6. 将结果转换为 `SearchResult` 列表。

Search 是 query-driven。调用方根据当前研究目标生成查询词。

## 工具层的异常边界

- RSS 请求或解析失败归入 `RSSToolError`。
- Search 输入、请求或解析失败归入 `SearchToolError`。
- 上层不需要理解 provider 的所有底层异常，只需要知道对应工具没有提供可用结果。

## 测试策略

当前测试不依赖真实网络：

- `tests/test_rss_tool.py` 使用样例 feed 验证解析和空 feed 错误。
- `tests/test_search_tool.py` 使用样例 JSON 验证解析、空查询和非法 provider 响应。
- Service 测试使用 fake RSS/Search 工具。

真实 HTTP 连通性和超时观测仍是后续可以补的工程问题，不属于 Day03 的核心学习目标。

## 与 Agent 的关系

工具只负责提供外部能力，不负责自己生成研究结论。工具输出会被 Agent 或 Service 继续处理：

```text
External Response
  ->
RSSItem / SearchResult
  ->
Agent Observation 或 Evidence
```

## 已有代码实践

- RSS 与 Search 使用不同的输入驱动方式。
- 外部 provider DTO 被转换成项目内部模型。
- 外部错误在工具边界被归一化。
- 解析器可以脱离网络独立测试。

## 尚未确认的理解

- 哪些字段属于 provider 偶然细节，哪些字段值得进入内部模型。
- Tool、Client 和 Service 的边界是否能够用自己的话讲清楚。
- provider 变更时，应该在哪一层吸收变化。

## Day03 验收问题

1. RSS 和 Search 的调用模型有什么差异？
2. 为什么不能把原始 provider JSON 直接传给 Agent？
3. timeout 和解析错误应该由谁负责？
4. 如果 Search provider 更换字段结构，需要修改哪些模块？

## 补充阅读

Day03 的原始详细说明仍保留在 [DAY3_AGENT_LOOP_GUIDE.md](../DAY3_AGENT_LOOP_GUIDE.md)。

