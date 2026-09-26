# Learning State

## 当前学习阶段

Day06 可控 Agent Loop 已完成，进入 Agent Runtime 底层机制复盘阶段。

## 当前 Day

Day 6

## 已掌握知识

- Java 后端基础经验
- LLM 基本调用链已有代码实践
- Tool Calling 基础已有代码实践
- Tool 与普通工具方法的区别已有初步理解
- LLM 根据 Tool 描述进行工具选择已有测试覆盖
- Service / Tool 基础职责划分已有代码实践
- `SearchResult` -> `Evidence` 的模型转换思路已有代码实践
- Tool 异常与 Service 异常边界已有初步理解
- 最小 Agent Loop 已有代码实践：LLM 决策、Tool Call、Tool Dispatch、Observation 回填、结构化输出校验
- 可控 Agent Runtime 已有代码实践：max_steps、多步执行、Tool Error Boundary、Execution Trace

## 需要强化的知识

- Agent 基础概念
- LLM 应用开发流程
- Python 工程实践
- Tool Calling
- Agent Loop 的独立解释能力
- max_steps 与 termination condition 的独立解释能力
- Execution Trace 与 application log 的区别
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
- 已新增 TASK-005 `ResearchAgent`，支持 `search_web` / `rss_feed` 两个 Tool Schema 和真实工具调用。
- 已新增 TASK-006 `AgentRuntime`，支持多步 loop、`max_steps`、统一 `ToolExecutor`、Tool failure observation 和 execution trace。
- 已迁移并运行 API、Service、Tool、Schema 和 Agent Loop 测试。

## 当前未解决问题

- `/research` API 当前未接入 `OpportunityResearchAgent`。
- `/research` API 当前未接入 TASK-006 `ResearchAgent` / `AgentRuntime`。
- `tools` 包内 legacy dispatcher 与真实 RSS/Search 工具命名边界仍需后续梳理。
- 外部 API 请求缺少更完整的集成测试和超时观测。

## 下一学习目标

复盘 TASK-006，确保可以独立解释 Loop、State、Runtime Control、max_steps、Tool Error Boundary 和 Execution Trace。

## 最近一次更新时间

2026-09-13

## Day06

### Learned

- Agent Loop
- Action / Observation
- termination condition
- max_steps
- Tool Registry
- Tool Error Boundary
- Execution Trace

### Implemented

- 新增 `AgentRuntime`，每一次 LLM 请求计为一个 step，并通过 `max_steps` 防止无限 tool calling。
- 新增 `ToolExecutor` 和 `ToolSpec`，将工具注册、参数解析、工具执行与主 Agent Loop 解耦。
- 将 unknown tool、invalid tool arguments、tool execution failure 转换为 `ok=false` tool observation。
- 新增 `AgentRunTrace` / `AgentStepTrace` / `ToolCallTrace`，记录 step、tool call、success/failure、stop reason。
- `ResearchAgent` 继续负责 prompt、tool schema、真实 RSS/Search 工具和最终 `ResearchResponse` 校验。
- 自动化测试覆盖 direct final、单工具、多步、多工具同轮、工具失败、unknown tool、max_steps、invalid final output。

### Problems Encountered

- `tasks/TASK-001.md` 到 `tasks/TASK-004.md` 当前仓库中不存在，只能基于 roadmap、上下文文档、TASK-005 和现有代码判断历史状态。
- 项目同时保留 Day3 legacy `OpportunityResearchAgent` 与 Day05/Day06 `ResearchAgent`，需要继续注意两条学习路径的命名边界。

### My Understanding

- TODO: 用自己的话解释 Agent Loop 如何形成。
- TODO: 用自己的话解释 State 如何在每一步之间传递。
- TODO: 用自己的话解释 Runtime 在哪里夺回模型的控制权。
- TODO: 用自己的话解释系统如何保证 Agent 最终停下来。

### Still Unclear

- TODO: 学习复盘后填写仍不清楚的问题。

### Next

- 先完成 Day06 Mandatory Learning Checkpoints，不自动进入 TASK-007。
