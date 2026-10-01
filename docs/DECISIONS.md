# Decisions

本文件采用简单 ADR 风格记录重要技术决策。

## ADR-0001: 初始化学习实践项目结构

### 日期

2026-09-10

### 决策

建立 `docs/`、`tasks/`、`notes/`、`src/`、`tests/`、`examples/` 的长期项目结构，并使用 `docs/AI_CONTEXT.md` 作为 Codex 与 ChatGPT 的简洁上下文同步入口。

### 原因

项目既承担学习管理，也承担代码实践和架构演进记录。固定目录和文档入口可以降低后续任务切换成本，避免上下文散落在对话历史中。

### 被放弃方案

- 只保留代码目录，不维护学习状态。
- 只通过聊天记录同步上下文。
- 一开始引入完整企业级工程结构。

### 后续影响

- 后续每个 TASK 都需要维护 `docs/AI_CONTEXT.md`。
- 架构变化需要同步更新 `docs/ARCHITECTURE.md`。
- 重要技术取舍需要追加到本文件。

## ADR-0002: 保守迁移 Day1-Day4 旧项目代码到 src/app

### 日期

2026-09-10

### 决策

将旧项目中仍有学习和运行价值的 FastAPI、Service、Tool、Schema、Agent Loop 和测试代码迁移到新仓库，并采用 `src/app` 作为源码目录。

### 原因

旧代码已经覆盖 LLM 调用链、Tool Calling、Service/Tool 职责划分、RSS/Search 证据获取和结构化输出，适合作为后续学习实践基础。迁移时保持原有 `app.*` import 和调用链，可以降低重写成本并保留学习连续性。

### 被放弃方案

- 将旧代码机械复制到仓库根目录。
- 立即改成全新的包名和分层架构。
- 将 Day3 Agent Loop 直接并入 `/research` API。

### 后续影响

- 运行 Uvicorn 时需要使用 `--app-dir src`。
- 后续 TASK 需要决定 `/research` 是否接入 `OpportunityResearchAgent`。
- `src/app/tools/__init__.py` 的 legacy dispatcher 命名边界后续需要小步梳理。

## ADR-0003: 新增独立 ResearchAgent 承载最小 Agent Loop

### 日期

2026-09-11

### 决策

在 `src/app/agents/research_agent.py` 新增 `ResearchAgent`，用手写循环实现 LLM Tool Calling / Agent Loop，并通过显式 `tool_registry` 将 `search_web`、`rss_feed` 映射到现有 `SearchTool.search()` 和 `RSSFeedTool.fetch()`。

### 原因

TASK-005 的学习目标是看清 Tool Schema、Tool Call、Tool Execution、Observation 和循环决策的完整链路。独立 Agent Layer 可以保留 Day3 legacy `OpportunityResearchAgent` 和当前 `/research` Service workflow，不用为了教学目标重写已有 API 路径。

### 被放弃方案

- 直接改造 `ResearchService` 为 Agent。
- 复用 `src/app/tools/__init__.py` 的 legacy mock dispatcher。
- 引入 LangChain、LangGraph 或其他 Agent Framework。

### 后续影响

- `/research` API 仍然走确定性 `ResearchService`。
- 后续任务可以在学习者掌握 TASK-005 后，再决定是否把 `ResearchAgent` 接入 API 或继续强化 Agent 状态与异常处理。

## ADR-0004: 抽离轻量 AgentRuntime 和 ToolExecutor

### 日期

2026-09-13

### 决策

在 `src/app/agents/runtime.py` 新增轻量 `AgentRuntime`、`ToolExecutor` 和 execution trace 数据结构。`ResearchAgent` 保留业务职责：prompt、Tool Schema、RSS/Search 工具注册、LLM 调用和最终 `ResearchResponse` 校验；Runtime 负责多步 loop、`max_steps`、Tool Observation 回填、终止条件和 trace。

### 原因

TASK-006 的学习目标是理解 Agent Runtime 的底层机制。将 loop 与业务 Agent 分离后，可以清楚看到：

- 每一次 LLM 请求如何成为一个 step。
- Runtime 如何限制 `max_steps`。
- Tool failure 如何转成 observation 返回给模型。
- Trace 如何记录可观察的 action / observation，而不记录隐藏推理过程。

### 被放弃方案

- 引入 LangChain、LangGraph 或其他 Agent Framework。
- 继续把 loop、tool dispatch、trace 全部堆在 `ResearchAgent` 一个类里。
- 将 tool failure 直接抛出并终止 Agent。

### 后续影响

- 后续任务可以在同一个 Runtime 上继续学习 state、evaluation、observability 或再迁移到 LangGraph。
- `/research` API 当前仍不接入 `ResearchAgent`，避免把 Day06 学习目标扩大成 API 重构。

## ADR-0005: 使用最小显式 AgentState 驱动 Runtime

### 日期

2026-10-01

### 决策

新增 `src/app/agents/state.py`，使用 dataclass 定义 `AgentState` 和 `AgentStatus`。一次运行的 State 保存 `goal`、`messages`、`current_step`、`observations`、`status` 和 `final_result`。`ResearchAgent` 创建 State，`AgentRuntime` 负责在每个 step、工具 observation、正常完成、max steps 和异常路径更新 State。

`AgentRunResult` 同时返回 `final_result`、`trace` 和 `state`；旧的 `AgentRuntime.run(messages, ...)` 形式仍可用，兼容已有调用方式。

### 原因

Day06 中执行上下文主要分散在 messages、循环变量和 trace。显式 State 可以清楚区分：

- `messages`：LLM 看到的上下文。
- `AgentState`：Agent 执行到哪里、获得了什么、当前状态和最终结果。
- `trace`：面向诊断的执行轨迹。

选择 dataclass 是因为当前 Runtime 和 trace 已使用 dataclass，State 只需要轻量的内存模型，不需要额外的持久化或序列化框架。

### 被放弃方案

- 继续只使用 messages 和局部变量。
- 将 Tool 实例、LLM Client、API Key 或隐藏推理过程放进 State。
- 为当前学习目标引入 LangGraph、数据库或 checkpoint persistence。

### 后续影响

- `ResearchAgent` 现在可以通过 `last_state` 观察最近一次运行。
- 运行失败时 State 会保留已执行部分，并标记为 `error`；达到限制时标记为 `max_steps`。
- `/research` API 仍然保留确定性 `ResearchService`，不在本 TASK 接入 Agent Runtime。
