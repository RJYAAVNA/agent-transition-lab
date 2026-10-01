# TASK-002 - Tool Calling Foundation

## 1. Task Metadata

- Task ID: TASK-002
- Day: Day02
- Phase: Agent Foundation
- Status: DONE
- Record type: Historical task reconstruction

> 该任务文件在仓库早期没有被保存。本记录根据路线、Day3 学习笔记和当前 legacy Agent Loop 重建。

## 2. Learning Objective

理解 Tool Calling 的最小协议和职责边界：

```text
User
  ->
LLM + Tool Schema
  ->
Tool Call
  ->
Application Dispatcher
  ->
Python Tool
  ->
Tool Result
  ->
LLM
```

完成后应能够解释：

1. Tool Schema 是给谁看的。
2. Tool Schema 为什么不能直接执行 Python。
3. `tool_call.name` 如何映射到真实函数。
4. Tool result 为什么必须回到 messages。
5. Tool Calling 与普通函数调用的区别。

## 3. Current Project Context

Day01 只有“用户输入到结构化结果”的调用链。Day02 在此基础上加入一个最小 `search_web` 工具，并保留一个简单的 registry/dispatcher。

当前 legacy 学习实现位于：

- `src/app/agent.py`
- `src/app/tools/__init__.py`
- `tests/test_agent_loop.py`
- `tests/test_tools.py`

后续 Day05/Day06 新增了更清晰的 `ResearchAgent`、`ToolExecutor` 和 `AgentRuntime`，但 Day02 的最小实现仍作为学习对照保留。

## 4. Implementation Scope

本任务应完成：

- 定义 `search_web` 的 Tool Schema。
- 定义一个可执行的 Python `search_web` 工具。
- 建立 `TOOL_REGISTRY`。
- 根据模型返回的工具名找到真实工具。
- 解析工具参数 JSON。
- 执行工具并序列化返回值。
- 追加 assistant tool call message 和 `role=tool` message。
- 再次调用 LLM，让模型基于 observation 决定下一步。
- 保留最小 `max_steps`，防止固定工具调用循环无限继续。

## 5. Core Call Flow

```text
Research topic
  ->
LLM receives tool schema
  ->
message.tool_calls
  ->
tool_call.function.name = "search_web"
  ->
TOOL_REGISTRY["search_web"]
  ->
search_web(query)
  ->
JSON serializable result
  ->
messages.append(role="tool")
  ->
next LLM call
  ->
final JSON
```

## 6. Important Concepts

### 6.1 Tool Schema

Tool Schema 至少描述工具名、用途和参数结构。模型看到的是 schema，不是 Python 函数对象。

### 6.2 Tool Call

Tool Call 是模型生成的结构化动作请求。它只是数据，必须由应用代码验证、查找和执行。

### 6.3 Dispatcher

Dispatcher 把模型给出的字符串名称映射成可执行工具。它是一个很小的 registry，不应把业务规则和所有工具实现塞进 Agent 主循环。

### 6.4 Observation

Tool 执行结果要以模型能够读取的消息重新放回上下文。否则下一轮模型看不到刚才的外部信息。

## 7. Definition of Done

- [x] 至少一个工具有 Tool Schema。
- [x] LLM 可以返回 `tool_calls`。
- [x] 工具名可以映射到 Python 工具。
- [x] 工具参数会解析和校验。
- [x] 工具结果会序列化。
- [x] `role=tool` 消息会追加到上下文。
- [x] Agent 会进行下一轮 LLM 调用。
- [x] 未知工具、非法 JSON 和工具执行失败有明确错误。
- [x] 关键调用链有 fake client 测试。

## 8. Learning Verification

1. 为什么 LLM 不能直接执行 `search_web(query)`？
2. Schema 与 dispatcher 分别负责什么？
3. `role=assistant` 的 tool call message 和 `role=tool` message 有什么不同？
4. 如果不把 tool result append 回 messages，下一轮会缺少什么信息？
5. 为什么 `max_steps` 在 Day02 就应该出现，即使功能还很小？

## 9. Out of Scope

- 真实 RSS/搜索外部服务
- 多工具并行
- RAG、Memory、MCP
- LangChain、LangGraph 等框架
- 复杂重试和持久化状态

