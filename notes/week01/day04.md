# Day04 - Layering and Domain Model

## 今日目标

把外部数据能力放进清晰的应用层次中：

```text
HTTP API
  ->
ResearchService
  ->
RSS/Search Tool
  ->
External Provider
```

同时把不同来源的 DTO 统一成研究领域模型：

```text
RSSItem / SearchResult
  ->
Evidence
  ->
ResearchResponse
```

## 各层职责

### API

`src/app/api/research.py` 接收 `ResearchRequest`，调用 Service，返回 `ResearchResponse`，并把 Service 错误映射为 HTTP 状态码。它不应该直接访问 RSS 或 Search。

### Service

`ResearchService` 编排完整的研究用例：

1. 获取 RSS。
2. 根据 topic 搜索。
3. 筛选或组合结果。
4. 将外部结果转换为 `Evidence`。
5. 生成 `ResearchResponse`。

### Tool

Tool 只负责一个外部能力的访问和解析。它不负责生成完整研究结论，也不应该知道 API 的 HTTP 状态码。

### DTO 与 Domain Model

`RSSItem` 和 `SearchResult` 反映不同来源的字段。`Evidence` 是项目内部统一的研究证据模型。使用 `Evidence` 可以让上层不依赖某一个 provider 的原始结构。

## 异常边界

```text
RSSFetchError / SearchToolError
  ->
ResearchServiceError
  ->
HTTP 502
```

这条边界让 API 不必知道底层是 RSS 超时、Search provider 返回坏 JSON，还是其他数据源问题。

## Workflow 与 Agent

当前 `/research` 是确定性 Workflow：

```text
代码固定调用 RSS
  ->
代码固定调用 Search
  ->
代码固定转换 Evidence
  ->
返回结果
```

它还不是由 LLM 动态决定下一步的 Agent。Day05 才在保留 Service Workflow 的同时加入独立 `ResearchAgent`。

## 测试策略

- Service 通过构造函数接收 fake tools，测试转换和异常边界。
- API 测试替换 Service，验证 HTTP contract。
- schema 测试验证 `ResearchResponse` 的字段约束。

## 已有代码实践

- `SearchResult` 和 `RSSItem` 都能转换为 `Evidence`。
- Service 不把 provider 原始结构暴露给 API。
- API、Service、Tool 可分别替换和测试。
- `/research` 与后续 Agent 学习路径保持独立。

## 尚未确认的理解

- 为什么 `Evidence` 不是多余的一层。
- Tool exception 与 Service exception 的边界。
- 为什么“固定步骤”属于 Workflow，而不是 Agent。

## Day04 验收问题

1. `SearchResult` 为什么不能直接作为最终响应中的 `Evidence`？
2. provider 字段变化应该由哪一层吸收？
3. API 为什么不直接调用 Tool？
4. 当前 `/research` 为什么仍是确定性 Workflow？

