# Learning State

## 当前学习阶段

Day1-Day4 旧项目代码已迁移，进入保守 Review 和后续演进阶段。

## 当前 Day

Day 4

## 已掌握知识

- Java 后端基础经验
- LLM 基本调用链已有代码实践
- Tool Calling 基础已有代码实践
- Tool 与普通工具方法的区别已有初步理解
- LLM 根据 Tool 描述进行工具选择已有测试覆盖
- Service / Tool 基础职责划分已有代码实践
- `SearchResult` -> `Evidence` 的模型转换思路已有代码实践
- Tool 异常与 Service 异常边界已有初步理解

## 需要强化的知识

- Agent 基础概念
- LLM 应用开发流程
- Python 工程实践
- Tool Calling
- Agent Loop
- 第三方 DTO 与 Agent Domain Model 的隔离
- Tool、Client、Service 的边界划分
- 异常分层与可观测性
- RAG
- Evaluation
- Observability

## 当前项目实践

- 已迁移一个 FastAPI 研究服务。
- 已迁移 RSS/Search 外部数据源工具。
- 已迁移 Day3 Tool Calling Agent Loop。
- 已迁移并运行 API、Service、Tool、Schema 和 Agent Loop 测试。

## 当前未解决问题

- 三个月详细学习路线尚未制定。
- 首个 TASK 尚未创建。
- `/research` API 当前未接入 `OpportunityResearchAgent`。
- `tools` 包内 legacy dispatcher 与真实 RSS/Search 工具命名边界仍需后续梳理。
- 外部 API 请求缺少更完整的集成测试和超时观测。

## 下一学习目标

创建第一个可执行 TASK，明确下一步演进方向：继续强化 Service/Tool 边界，或将 Agent Loop 接入 `/research`。

## 最近一次更新时间

2026-09-10
