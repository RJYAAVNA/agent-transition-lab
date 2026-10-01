# Day05 - Research Agent and Tool Calling

## 今日目标

第一次建立面向业务目标的 Agent Layer，理解：

```text
User Goal
  ->
ResearchAgent
  ->
LLM + Tool Schemas
  ->
Tool Call
  ->
Tool Execution
  ->
Observation
  ->
LLM
  ->
Structured Final Output
```

## 为什么单独增加 ResearchAgent

`ResearchService` 仍然适合表达固定的研究 Workflow。Day05 的目标是学习 LLM 动态选择工具，因此新增 `ResearchAgent`，避免直接重写 `/research` 或把 Workflow 和 Agent 混为一谈。

当前 `ResearchAgent` 负责：

- 业务 system prompt。
- `search_web` 和 `rss_feed` 的 Tool Schema。
- 真实 RSS/Search 工具注册。
- LLM 调用适配。
- 最终 `ResearchResponse` 校验。

Day06 进一步把通用 loop 抽到 `AgentRuntime`，所以当前源码中的 Day05 调用链已经包含 Day06 的 Runtime。

## Tool Schema 与 Tool Implementation

模型看到的是 `TOOL_SCHEMAS`。真实执行的是 `ToolSpec.func` 指向的 Python callable。二者通过工具名称和参数模型连接，但不是同一个对象。

```text
Tool Schema
  ->
LLM 产生 tool_call
  ->
ToolExecutor 根据名称查找 ToolSpec
  ->
参数解析和校验
  ->
Python tool
```

## Workflow 与 Agent

确定性 Workflow：

```text
Code -> RSS -> Search -> Response
```

Agent：

```text
LLM -> Decide -> Tool -> Observe -> Decide
```

Workflow 的下一步由代码预先决定。Agent 的下一步由模型输出的结构化动作请求决定，但是否执行、如何执行和何时停止仍由 Runtime 控制。

## 结构化最终输出

Tool observation 不直接等于用户最终结果。模型读取 observation 后生成最终 JSON，最后仍然经过 `ResearchResponse` 校验：

```text
Tool Result
  ->
LLM Context
  ->
Final JSON
  ->
Pydantic Validation
  ->
ResearchResponse
```

## Day05 代码验收

TASK-005 的代码能力已经落地，并由 Day06 测试继续覆盖：

- LLM 可以看到两个 Tool Schema。
- Tool call 可以映射到真实 RSS/Search 工具。
- Observation 会回填 messages。
- Agent 可以继续请求工具或返回最终结果。
- 最终结果仍使用现有 schema。

## 学习验收尚未自动判定

代码已经存在不等于学习者已经掌握。需要自行回答：

1. LLM 为什么不能直接执行 Python 函数？
2. Tool Schema 在哪里发挥作用？
3. tool name 如何映射到真实工具？
4. 为什么 Observation 要回到上下文？
5. Agent 与固定 Workflow 的本质差异是什么？

