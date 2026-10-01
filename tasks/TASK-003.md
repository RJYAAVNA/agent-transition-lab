# TASK-003 - Real Tool Integration

## 1. Task Metadata

- Task ID: TASK-003
- Day: Day03
- Phase: Agent Foundation
- Status: DONE
- Record type: Historical task reconstruction

> 该任务文件在仓库早期没有被保存。本记录根据 `notes/DAY3_AGENT_LOOP_GUIDE.md`、当前数据源工具、Service 和测试重建。

## 2. Learning Objective

把 Day02 的 mock tool 调用扩展为真实外部数据源能力，并理解不同工具的输入方式：

- RSS 是 source-driven tool：从指定 feed 获取一组条目。
- Search 是 query-driven tool：根据当前研究主题发起搜索。

重点不是接入某个特定供应商，而是看清：

```text
External HTTP Response
  ->
Parser
  ->
Internal Tool Result
  ->
Agent or Service
```

## 3. Implementation Scope

本任务应完成：

- `RSSFeedTool` 获取 RSS/Atom feed。
- `SearchTool` 调用搜索 provider。
- 将外部响应解析为 `RSSItem` 和 `SearchResult`。
- 清理 HTML、空白和不稳定的 provider 字段。
- 对请求失败、解析失败和输入错误使用工具层异常。
- 使用 timeout、User-Agent 和结果数量限制。
- 为 parser 和失败路径增加不依赖网络的测试。

当前代码中的主要落点：

- `src/app/tools/rss_tool.py`
- `src/app/tools/search_tool.py`
- `tests/test_rss_tool.py`
- `tests/test_search_tool.py`

## 4. Core Call Flow

### RSS

```text
RSSFeedTool.fetch()
  ->
HTTP GET feed_url
  ->
feedparser.parse()
  ->
RSSItem list
```

### Search

```text
SearchTool.search(query)
  ->
validate query and limit
  ->
HTTP GET search provider
  ->
parse JSON payload
  ->
SearchResult list
```

## 5. Tool Boundary

工具层负责：

- 外部请求。
- provider response 解析。
- provider 字段到工具结果的最小归一化。
- 工具相关异常。

工具层不负责：

- 研究主题的业务结论。
- Signal、Opportunity、Risk 的生成。
- 最终 `ResearchResponse` 的结构化业务语义。

这些职责由上层 Service 或 Agent 处理。

## 6. Definition of Done

- [x] RSS feed 能转换为 `RSSItem`。
- [x] Search provider 响应能转换为 `SearchResult`。
- [x] 外部 HTML 片段会清理为纯文本。
- [x] RSS、Search 有独立异常边界。
- [x] 请求配置支持 URL、timeout、User-Agent 和数量限制。
- [x] 空查询、空 feed、无效 JSON 和 provider 结构错误有测试。
- [x] 单元测试使用样例响应，不依赖真实外部网络。

## 7. Learning Verification

1. RSS Tool 和 Search Tool 的输入驱动方式有什么不同？
2. 为什么不把 provider 的原始 JSON 直接交给 Agent？
3. parser 失败应该属于 Tool 层还是业务 Service 层？
4. timeout 和 User-Agent 为什么属于外部请求边界的责任？
5. 如果 provider 更换字段结构，哪一层应该吸收变化？

## 8. Out of Scope

- RAG 和向量数据库
- Search ranking 或复杂相关性算法
- 多 provider fallback
- 重试框架和异步 worker
- Agent Framework

