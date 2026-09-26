# AI Context

本文件记录项目当前有效状态，供 Codex 与 ChatGPT 同步上下文。

## Current Goal

以机会研究为实践场景，学习从外部信息获取到结构化研究结果的完整流程，重点理解手写 Agent Loop 的工具执行、步数控制、错误边界和执行轨迹。

## Current Architecture

Python FastAPI 项目，当前有三条独立执行路径：

- `/research`：`ResearchService` 固定先获取 RSS，再按 topic 搜索，将结果转换为 Evidence，组合模板化研究结果；不调用 LLM。
- `ResearchAgent`：负责业务 prompt、Tool Schema、工具注册、LLM 请求和最终结果校验；委托 `AgentRuntime` 控制循环，由 `ToolExecutor` 执行真实 RSS/Search 工具。当前未接入 HTTP API。
- `OpportunityResearchAgent`：保留的 Day3 学习实现，使用 `app.tools` 的 legacy dispatcher 和 mock 搜索，不使用新版 Runtime。

RSS/Search 工具直接承担外部请求和解析，没有独立的 SearchService/SearchClient 层。当前未引入 Agent Framework。

## Main Modules

- `src/app/main.py`、`src/app/api/`：FastAPI 装配、研究接口及 HTTP 异常映射。
- `src/app/services/research_service.py`：确定性研究流程、RSS 相关性筛选、工具结果到 Evidence 的转换。
- `src/app/agents/research_agent.py`：研究 Agent 的业务输入输出、LLM 适配与真实工具注册。
- `src/app/agents/runtime.py`：AgentRuntime、ToolExecutor、工具 observation、运行结果和 trace。
- `src/app/tools/rss_tool.py`、`search_tool.py`：真实数据源访问、解析与工具异常。
- `src/app/schemas/research.py`：研究请求、响应及业务模型校验。
- `src/app/core/config.py`：环境变量、手写 `.env` 加载及服务配置。
- `src/app/agent.py`、`src/app/tools/__init__.py`：legacy Agent Loop 和 mock dispatcher。
- `tests/`：API、Service、Tool、Schema 和 Agent 测试；LLM 和 Agent 工具使用替身，当前 31 项测试通过。

## Important Domain Models

- `ResearchRequest.topic`：确定性研究流程的输入；新版 Agent 直接接收 goal 字符串。
- `RSSItem` / `SearchResult` → `Evidence`：由 ResearchService 转换，分别映射摘要/片段、来源和链接。
- `ResearchResponse`：包含 topic、summary、Signal/Opportunity/Risk/Evidence 列表和 confidence；四类列表均非空，confidence 范围为 0–1。
- Agent 路径将 `RSSItem` / `SearchResult` 序列化为 observation，由 LLM 生成最终 `ResearchResponse` JSON，再做模型校验，不经过 Service 的 Evidence 转换。
- Runtime 模型：`ToolSpec` 绑定工具名、函数与参数模型；`ToolObservation` 表达成功结果或错误；`AgentRunResult` 包含 final_result 和 `AgentRunTrace`，后者包含 `AgentStepTrace`，每步记录 `ToolCallTrace`。

## Main Call Chains

确定性 HTTP 路径：

```text
POST /research → ResearchRequest → ResearchService.research()
  → RSSFeedTool.fetch() → RSSItem 列表
  → SearchTool.search(topic) → SearchResult 列表
  → RSS 筛选 + 两类结果转换为 Evidence → ResearchResponse
```

新版 Agent 路径：

```text
goal → ResearchAgent.research() → research_with_trace() → AgentRuntime.run()
  → ResearchAgent._call_llm() → client.chat.completions.create()
  → 有 tool_calls：ToolExecutor.execute_tool() → 参数解析/校验
    → SearchTool.search() / RSSFeedTool.fetch()
    → ToolObservation → ok=true/false JSON → role=tool 回填 messages → 下一轮 LLM
  → 无 tool_calls：_parse_final_response() → ResearchResponse.model_validate()
    → AgentRunResult(final_result, trace) → research() 返回 ResearchResponse
```

每次 LLM 请求计一步，默认 `max_steps=5`；同轮多个工具顺序执行。未知工具、参数错误和工具执行异常转为失败 observation。成功、无效最终输出和步数耗尽分别记录 `completed`、`invalid_output`、`max_steps`；后两者抛出异常。Trace 可通过 `research_with_trace()` 返回值或 `last_trace` 读取，异常路径的限制见 Known Issues。

## External Dependencies

- FastAPI / Uvicorn：HTTP API 与服务运行。
- Pydantic：业务输出、工具参数和配置模型。
- OpenAI SDK：访问 OpenAI 或 DeepSeek 的兼容 LLM API。
- feedparser：RSS/Atom 解析；默认 feed 为 BBC Technology。
- Wikipedia Search API：默认搜索数据源，结果链接固定构造为英文 Wikipedia URL。
- pytest、httpx2：开发依赖，用于测试及 FastAPI TestClient 支持。

## Recent Structural Changes

- 2026-09-26：采用 `main` + 短期 TASK 分支流程；任务分支从最新 `main` 创建，完成并测试后通过 PR 合入。
- TASK-005/006：新增独立 ResearchAgent，并抽离 AgentRuntime / ToolExecutor，实现真实工具调用、多步循环、max_steps、错误 observation 和 execution trace。
- 2026-09-10：Day1–Day4 代码迁移到 `src/app/`，测试迁移到 `tests/`。
- 2026-09-10：建立长期文档和任务目录，保留 Day3 Agent Loop 学习说明。

## Known Issues

- Runtime 在 LLM 请求失败或响应结构异常时未保存本次 trace，也未在运行开始清空 `last_trace`；因此可能得到 None 或上次运行的 trace。部分畸形 tool call 在包装 assistant message 时会直接触发 AttributeError。
- Trace 保存工具参数、完整 observation 和异常文本，当前没有脱敏处理。
- 配置加载路径实际为 `src/.env`，不会自动读取仓库根目录 `.env`；根目录提供了 `.env.example`，需注意位置差异。
- RSS/Search HTTP 请求层缺少测试覆盖；现有工具测试主要验证样例解析，Agent 测试使用替身，不验证真实外部服务连通性。

## Current Task

Completed: TASK-005、TASK-006（代码开发已完成；学习检查点由学习者确认）。

## Next Recommended Task

技术建议：补齐 Runtime 异常终止时的 trace 生命周期，并以 LLM 失败、畸形响应和同一实例连续运行的回归测试验证。是否安排及最终学习顺序由 `LEARNING_ROADMAP` 和 ChatGPT 决定，本建议不自动启动后续 TASK。
