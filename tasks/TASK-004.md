# TASK-004 - Layering and Domain Model

## 1. Task Metadata

- Task ID: TASK-004
- Day: Day04
- Phase: Agent Foundation
- Status: DONE
- Record type: Historical task reconstruction

> 该任务文件在仓库早期没有被保存。本记录根据路线、当前 Service/Tool/Schema 实现、测试和架构文档重建。

## 2. Learning Objective

理解并实践以下边界：

```text
API
  ->
Service / Use Case
  ->
Tool
  ->
External Provider
```

以及：

```text
Third-party DTO
  ->
Internal Domain Model
  ->
Structured Response
```

完成后应能够解释：

1. 为什么 `SearchResult` 不等于 `Evidence`。
2. 为什么 API 不应该直接编排外部请求。
3. Tool、Service、DTO 和 Domain Model 各自负责什么。
4. 外部异常如何在边界上转换。
5. 为什么当前 `/research` 是确定性 Workflow，而不是 Agent。

## 3. Implementation Scope

本任务应完成或确认：

- `ResearchService` 作为研究用例入口。
- Service 固定编排 RSS 和 Search。
- `RSSItem` 和 `SearchResult` 转换为统一的 `Evidence`。
- Service 生成 `ResearchResponse`。
- API 层只处理 HTTP 输入、输出和状态码。
- Tool 异常在 Service 层转换为 `ResearchServiceError`。
- Pydantic schema 作为请求、领域结果和边界校验。
- 通过依赖注入式构造参数使用 fake tools 测试 Service。

当前代码中的主要落点：

- `src/app/api/research.py`
- `src/app/services/research_service.py`
- `src/app/schemas/research.py`
- `tests/test_research_service.py`
- `tests/test_research_api.py`

## 4. Core Call Flow

```text
POST /research
  ->
ResearchRequest
  ->
ResearchService.research()
  ->
RSSFeedTool.fetch() -> RSSItem
  ->
SearchTool.search(topic) -> SearchResult
  ->
RSSItem/SearchResult -> Evidence
  ->
ResearchResponse
  ->
HTTP JSON response
```

## 5. Boundary Responsibilities

### API

负责 HTTP contract、请求模型、响应模型和错误状态码。不负责 RSS、Search 或 Evidence 的业务编排。

### Service

负责一个完整研究用例的执行顺序、结果组合、证据转换和业务级错误边界。

### Tool

负责一个外部能力的访问和 provider response 解析，不负责整个研究用例的结论。

### DTO / Domain Model

`RSSItem` 和 `SearchResult` 保留不同来源的字段；`Evidence` 是内部研究领域统一表示。这样外部 provider 的字段变化不会直接扩散到最终响应。

## 6. Definition of Done

- [x] API、Service、Tool 职责可以从调用链中区分。
- [x] RSS 和 Search 结果可以统一转换成 `Evidence`。
- [x] `ResearchResponse` 经过 Pydantic 校验。
- [x] Tool failure 会转换为可定位的 Service error。
- [x] Service 测试可以用 fake tools 替换真实外部依赖。
- [x] API 测试不依赖真实网络和 LLM。
- [x] 当前 `/research` 的确定性性质有文档说明。

## 7. Learning Verification

1. `SearchResult` 和 `Evidence` 的差异是什么？
2. 如果 Search provider 改字段，应该修改哪一层？
3. 为什么 Service 不能只把两个工具返回值直接拼接后交给 API？
4. Tool exception 和 Service exception 的边界在哪里？
5. 当前流程为什么属于 Workflow，而不是由 LLM 动态选择工具的 Agent？

## 8. Out of Scope

- 把 `/research` 改造成 Agent API
- 自动规划和动态 Tool Selection
- RAG、Memory、MCP
- 过度拆分 Client、Adapter、Repository
- 无关的企业级依赖注入框架

