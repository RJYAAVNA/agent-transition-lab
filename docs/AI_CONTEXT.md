# AI Context

本文件记录项目当前有效状态，供 Codex 与 ChatGPT 同步上下文。

## Current Goal

以 Opportunity Research Agent 为实践场景，学习从外部信息获取到结构化研究结果的完整流程，当前重点是理解 Message History 与显式 AgentState 的区别，以及 State 如何驱动手写 Agent Runtime 的工具执行、多步循环、终止边界、错误 observation 和 execution trace。

## Current Architecture

Python FastAPI 项目，当前有三条独立执行路径：

- `/research`：`ResearchService` 固定获取 RSS 和 Search 结果，将它们转换为 `Evidence` 并组合 `ResearchResponse`；不调用 LLM。
- `ResearchAgent`：负责业务 prompt、Tool Schema、真实 RSS/Search 工具注册、LLM 请求和最终结果校验；创建 `AgentState` 并委托 `AgentRuntime` 控制循环，当前未接入 HTTP API。
- `OpportunityResearchAgent`：保留的 Day03 legacy 学习实现，使用 `app.tools` 的 mock dispatcher，不使用新版 Runtime。

`AgentState`、`AgentRuntime` 和 `ToolExecutor` 是轻量手写实现，当前未引入 LangChain、LangGraph 或其他 Agent Framework。RSS/Search 工具直接承担外部请求和解析，尚未拆出独立 Client/Service 层。

## Main Modules

- `src/app/main.py`、`src/app/api/`：FastAPI 装配、研究接口和 HTTP 异常映射。
- `src/app/services/research_service.py`：确定性研究流程、RSS 相关性筛选、工具结果到 `Evidence` 的转换。
- `src/app/agents/research_agent.py`：业务 Agent、Tool Schema、真实工具注册、LLM 适配和 `ResearchResponse` 校验。
- `src/app/agents/state.py`：`AgentState` 和 `AgentStatus`，表示一次运行的可观察执行状态。
- `src/app/agents/runtime.py`：多步 loop、`max_steps`、`ToolExecutor`、失败 observation 和 execution trace。
- `src/app/tools/rss_tool.py`、`src/app/tools/search_tool.py`：RSS/Search 外部请求、解析和工具异常。
- `src/app/schemas/research.py`：请求、证据和研究响应模型。
- `src/app/agent.py`、`src/app/tools/__init__.py`：Day03 legacy Agent Loop 和 mock dispatcher。
- `tests/`：API、Service、Tool、Schema、legacy Agent Loop 和新版 ResearchAgent/Runtime 测试。

## Important Domain Models

- `ResearchRequest.topic`：确定性 HTTP 流程的输入；新版 Agent 直接接收 `goal` 字符串。
- `RSSItem`、`SearchResult`：两个外部数据源的内部工具结果。
- `Evidence`：`ResearchService` 统一使用的研究证据模型。
- `ResearchResponse`：包含 `topic`、`summary`、`signals`、`opportunities`、`risks`、`evidence` 和 `confidence`；列表非空，`confidence` 范围为 `0-1`。
- `ToolSpec`：绑定工具名、函数和参数模型。
- `ToolObservation`：表示工具成功结果或失败信息。
- `AgentState`：表示 goal、messages、current_step、observations、status 和 final_result；不保存 Tool 实例或敏感配置。
- `AgentRunResult` / `AgentRunTrace` / `AgentStepTrace` / `ToolCallTrace`：表示一次 Agent 运行结果和可观察执行轨迹。

## Main Call Chains

确定性 HTTP 路径：

```text
POST /research
  -> ResearchRequest
  -> ResearchService.research()
  -> RSSFeedTool.fetch() -> RSSItem[]
  -> SearchTool.search(topic) -> SearchResult[]
  -> RSS/Search -> Evidence
  -> ResearchResponse
  -> HTTP JSON
```

新版 Agent 路径：

```text
goal
  -> ResearchAgent 创建 pending AgentState
  -> AgentRuntime.run(state)
  -> state.status=running, current_step 由 Runtime 更新
  -> ResearchAgent._call_llm()
  -> LLM response
  -> tool_calls?
     -> ToolExecutor.execute_tool()
     -> parse and validate arguments
     -> SearchTool.search() / RSSFeedTool.fetch()
     -> ToolObservation
     -> observation 写入 state.observations
     -> role=tool observation appended to state.messages
     -> next LLM step
  -> final content
  -> ResearchResponse validation
   -> state.status=completed, state.final_result=ResearchResponse
   -> AgentRunResult(final_result, trace, state)
```

每次 LLM 请求计为一个 step，默认 `max_steps=5`；同轮多个工具顺序执行。未知工具、非法参数和工具执行异常会变成 `ok=false` observation。正常完成、非法最终输出和步数耗尽分别记录 `completed`、`invalid_output` 和 `max_steps`。

## External Dependencies

- FastAPI / Uvicorn：HTTP API 和服务运行。
- Pydantic：请求、工具参数、领域结果和配置校验。
- OpenAI SDK：访问 OpenAI 或 DeepSeek 的兼容 LLM API。
- feedparser：RSS/Atom 解析。
- Wikipedia Search API：当前默认 Search provider。
- pytest、httpx2：自动化测试和 FastAPI 测试支持。

## Recent Structural Changes

- 2026-10-01：完成 TASK-007，新增 `AgentState`，将 step、observation、终止状态和最终结果接入 `AgentRuntime`。
- 2026-09-26：采用 `main` + 短期 TASK 分支流程；任务分支从最新 `main` 创建，完成并测试后通过 PR 合入。
- TASK-005/006：新增独立 `ResearchAgent`，并抽离 `AgentRuntime` / `ToolExecutor`，实现真实工具调用、多步循环、`max_steps`、错误 observation 和 execution trace。
- 2026-09-10：Day01-Day04 代码迁移到 `src/app/`，测试迁移到 `tests/`。
- 2026-09-10：建立长期文档、任务目录和学习上下文同步入口。

## Known Issues

- Runtime 异常会把 State 标记为 `error` 并保存已有的部分 trace；异常发生前没有完成的 step 可能没有单独的 error trace 节点。
- Trace 当前保存工具参数、完整 observation 和异常文本，没有脱敏处理。
- 配置加载路径实际为 `src/.env`，不会自动读取仓库根目录 `.env`；根目录仅提供 `.env.example`。
- RSS/Search HTTP 请求层缺少更完整的集成测试和超时观测；Agent 测试使用替身，不验证真实外部服务连通性。

## Current Task

TASK-007 已完成：新增显式 `AgentState`，并通过测试验证 initial、单工具、多步、completed、max_steps 和 error 状态。本轮没有接入 `/research` API，也没有启动 TASK-008。

## Next Recommended Step

先完成 Day07 学习验收，能够用自己的话解释 Message History、AgentState、Runtime Control 和 State 更新顺序。最终学习顺序仍由 `LEARNING_ROADMAP.md` 和 ChatGPT 的学习验收决定。
