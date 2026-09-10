# Day 3 Agent Loop Guide

## 1. 本次修改文件

- `app/api/research.py`
  - 保持 FastAPI Controller 职责不变：接收 `ResearchRequest`，调用 `ResearchService`，返回 `ResearchResponse`。
- `app/services/research_service.py`
  - 从 Day 2 mock 返回改为调用 `OpportunityResearchAgent`。
  - 仍然是业务入口，类似 Java Spring 中的 Application Service。
- `app/agent.py`
  - 新增最小可读版 `OpportunityResearchAgent`。
  - 实现 LLM tool calling、Agent Loop、`max_steps`、最终 JSON 解析、Pydantic 校验和 Agent 级异常。
- `app/tools.py`
  - 新增真实 Python tool：`search_web(query: str)`。
  - 新增 `TOOL_REGISTRY` 和 `execute_tool(tool_name, arguments)`。
  - 新增最小工具异常：工具不存在、参数 JSON 错误、工具执行失败。
- `app/core/config.py`
  - 读取 `.env`。
  - 增加 LLM provider、model、API key、search provider 配置。
- `app/main.py`
  - 增加最小日志配置，方便观察 Agent 执行过程。
- `tests/test_agent_loop.py`
  - 用 fake LLM client 验证：LLM 请求 tool、Python tool 执行、messages 继续 append、最终返回结构化结果。
- `tests/test_tools.py`
  - 验证 dispatcher 的工具查找、JSON 参数解析和工具执行。
- `tests/test_research_api.py`
  - API 单元测试 mock 掉 service 结果，避免测试依赖真实 LLM。
- `pyproject.toml` / `uv.lock`
  - 增加 `openai` SDK。

## 2. 完整调用链

```text
HTTP POST /research
  -> app/api/research.py
  -> ResearchService.research()
  -> OpportunityResearchAgent.research()
  -> LLM
  -> tool_calls: search_web({"query": "..."})
  -> execute_tool()
  -> Python function search_web()
  -> tool result append 到 messages
  -> LLM 再次读取上下文
  -> final JSON
  -> parse_opportunity_report()
  -> ResearchResponse
```

目标架构仍然是：

```text
API
  -> ResearchService
  -> Agent / Workflow
  -> LLM
  -> Tool
  -> LLM
  -> Structured Response
```

## 3. Agent Loop 每一步发生了什么

`OpportunityResearchAgent.research(topic)` 会先初始化 `messages`：

- `system`：告诉模型它是机会研究 Agent，最终必须返回 JSON。
- `user`：传入研究目标。

然后进入：

```python
for step in range(1, self.max_steps + 1):
```

每一轮做四件事：

1. 把 `messages` 和 `tools` 发给 LLM。
2. 如果 LLM 返回 `tool_calls`，说明模型决定先调用工具。
3. Agent 通过 `execute_tool()` 执行真实 Python 函数，并把 tool result append 回 `messages`。
4. 下一轮循环，LLM 会看到之前的 tool result，再决定继续调用工具还是输出最终 JSON。

如果某一轮 LLM 没有返回 `tool_calls`，Agent 就认为任务完成，并把最终内容解析成 `ResearchResponse`。

## 4. Tool Schema 的作用

`app/agent.py` 里的 `SEARCH_WEB_TOOL_SCHEMA` 是给 LLM 看的工具说明。

它说明：

- 工具名是 `search_web`
- 工具用途是“根据 query 搜索与研究目标相关的信息”
- 参数是一个 JSON object
- 必填字段是 `query: string`

注意：Tool Schema 本身不会执行 Python 函数。

它只是告诉 LLM：

```text
系统有哪些工具，以及调用工具需要哪些参数。
```

真正执行 Python 函数的是 `app/tools.py` 里的 dispatcher。

## 5. Tool Dispatcher 的作用

`app/tools.py` 中有一个非常小的 registry：

```python
TOOL_REGISTRY = {
    "search_web": search_web,
}
```

`execute_tool(tool_name, arguments)` 负责：

1. 根据工具名查找 Python function。
2. 如果工具不存在，抛出 `ToolNotFoundError`。
3. 把 LLM 给的 JSON 字符串解析成 Python dict。
4. 如果 JSON 无法解析，抛出 `ToolArgumentsError`。
5. 调用真实 Python function。
6. 如果工具执行失败，抛出 `ToolExecutionError`。
7. 把工具结果序列化成 JSON string，作为 tool message 返回给 LLM。

这样 Agent Loop 不需要写很多：

```python
if tool_name == "search_web":
```

新增工具时，只要新增函数，再注册到 `TOOL_REGISTRY`。

## 6. messages 为什么不断 append

Agent 的记忆不是隐藏变量，而是 `messages`。

每次 LLM 请求工具时，Agent 会 append 两类消息：

- assistant message：记录“模型刚才请求了哪个 tool call”
- tool message：记录“Python tool 实际返回了什么结果”

这样下一轮 LLM 调用时，模型能看到完整上下文：

```text
用户要研究什么
模型刚才决定调用什么工具
工具返回了哪些信息
```

如果不 append tool result，LLM 下一轮就不知道工具查到了什么，也无法基于工具结果生成最终答案。

## 7. max_steps 为什么必要

`MAX_STEPS = 5` 是 Agent 系统的重要安全边界。

没有它，模型可能陷入无限循环：

```text
LLM -> Tool -> LLM -> Tool -> LLM -> Tool ...
```

`max_steps` 的作用类似后端系统里的超时、重试上限、熔断边界。它不是业务逻辑的一部分，但它保护系统不会被一次异常决策拖住。

超过限制时，Agent 抛出 `AgentMaxStepsExceeded`。

## 8. 与 Java 开发的类比

- Tool Schema ≈ 接口描述 / DTO
  - 它描述工具名称、用途和参数结构，但不执行逻辑。
- Tool Dispatcher ≈ Factory / Strategy Registry
  - 根据字符串名字找到具体策略类或函数。
- Agent Loop ≈ while + 状态机 + 动态决策
  - 每一步根据 LLM 输出决定下一步：调用工具，还是结束。
- Pydantic Model ≈ DTO + Validator
  - `ResearchRequest` 和 `ResearchResponse` 既是数据结构，也是校验边界。
- ResearchService ≈ Application Service
  - Controller 不直接编排 LLM 和工具，业务入口仍然在 Service 层。
- Tool Function ≈ 领域服务 / 外部网关
  - `search_web()` 是真实 Python 函数，可以访问搜索服务、数据库、内部 API 或其他系统。

## 9. Day 3 验收方式

安装依赖：

```powershell
py -m uv sync --dev
```

运行测试：

```powershell
py -m uv run pytest
```

启动 API：

```powershell
py -m uv run uvicorn app.main:app --reload
```

请求 demo：

```powershell
curl.exe -X POST http://127.0.0.1:8000/research `
  -H "Content-Type: application/json" `
  -d "{\"topic\":\"研究 AI Agent 对 Java 后端工程师未来职业机会的影响\"}"
```

期望日志大致类似：

```text
Agent start: topic=研究 AI Agent 对 Java 后端工程师未来职业机会的影响
Agent step: 1
LLM requested tool: search_web args={"query":"AI Agent Java backend engineer career opportunities"}
Tool execution start: search_web
Tool execution result: {...}
Agent step: 2
Agent final answer: {...}
Agent finished
```

期望最终响应是结构化 `ResearchResponse`：

```json
{
  "topic": "研究 AI Agent 对 Java 后端工程师未来职业机会的影响",
  "summary": "...",
  "signals": [{"title": "...", "description": "..."}],
  "opportunities": [{"title": "...", "description": "..."}],
  "risks": [{"title": "...", "description": "..."}],
  "evidence": [{"title": "...", "source": "...", "url": null, "excerpt": "..."}],
  "confidence": 0.7
}
```

如果没有可用 key，需要在 `.env` 中配置：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=your_real_key
OPENAI_MODEL=gpt-4.1-mini
```

或使用 OpenAI-compatible DeepSeek：

```text
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_real_key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```
