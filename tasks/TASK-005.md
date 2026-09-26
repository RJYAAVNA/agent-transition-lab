# TASK-005 — Minimal Agent Loop & Tool Calling

## 1. Task Metadata

* Task ID: TASK-005
* Day: Day05
* Phase: Agent Fundamentals
* Status: DONE
* Priority: High

---

## 2. Learning Objective

本任务的核心目标不是扩展业务功能，而是理解并亲手实现一个最小可运行的 **LLM Tool Calling / Agent Loop**。

完成本任务后，需要能够解释：

1. LLM 如何知道有哪些 Tool 可以使用
2. Tool Schema 与真实 Python Tool 之间是什么关系
3. LLM 返回的 `tool_call` 本质是什么
4. 为什么 LLM 本身并不会直接执行 Python 函数
5. Agent Runtime 如何根据 tool name 找到并执行真实 Tool
6. Tool Result 为什么需要重新加入 messages/context
7. Agent 为什么需要循环执行，而不是只调用一次 LLM
8. Workflow 与 Agent 的核心区别

---

## 3. Current State

在开始本任务前，项目已经具备以下能力：

* 已有 RSS Tool
* 已有 Search Tool
* Tool 层可以访问真实外部数据源
* Tool 返回自己的领域对象，例如：

  * RSSItem
  * SearchResult
* Service 层会将不同 Tool 的返回值统一转换为 Evidence
* 已建立基本异常分层
* 已建立 ResearchRequest / ResearchResponse 等 Pydantic Schema
* 当前 ResearchService 属于确定性流程：

  * 代码固定调用 RSS
  * 代码固定调用 Search
  * 代码固定聚合 Evidence

当前模式本质上仍然是 Workflow：

```text
Request
  ↓
ResearchService
  ↓
RSS Tool
  ↓
Search Tool
  ↓
Evidence
  ↓
Response
```

本任务需要第一次引入：

```text
User Goal
  ↓
LLM
  ↓
Decision
  ↓
Tool Call
  ↓
Tool Execution
  ↓
Observation
  ↓
LLM
  ↓
Continue / Final Answer
```

---

## 4. Core Concept

本任务必须明确区分以下三部分：

### 4.1 Tool Implementation

真实可执行的 Python 代码，例如：

```python
search_tool.search(query)
```

### 4.2 Tool Schema

提供给 LLM 的工具说明。

至少需要包含：

```text
name
description
parameters
```

LLM 能看到的是 Tool Schema，而不是 Python 函数本身。

### 4.3 Tool Call

当 LLM 判断需要调用 Tool 时，它不会直接执行 Python 代码，而是返回结构化调用请求，例如：

```json
{
  "name": "search_web",
  "arguments": {
    "query": "AI Agent engineering trends"
  }
}
```

真正执行 Tool 的责任属于 Agent Runtime。

---

## 5. Implementation Goal

新增一个最小 Agent Layer，使调用链变为：

```text
User Goal
  ↓
ResearchAgent
  ↓
LLM + Tool Schemas
  ↓
tool_calls ?
  ├─ No → Parse Final Output → Return
  │
  └─ Yes
       ↓
    Tool Dispatcher
       ↓
    Execute Python Tool
       ↓
    Serialize Tool Result
       ↓
    Append role=tool message
       ↓
    Call LLM again
       ↓
    Continue Loop
```

---

## 6. Implementation Requirements

### 6.1 Add Agent Layer

新增独立 Agent 文件。

推荐：

```text
app/agents/research_agent.py
```

不要直接删除或大规模重构当前 `ResearchService`。

本任务重点是新增 Agent Runtime，而不是重写已有系统。

---

### 6.2 Define Tool Schemas

为现有 Tool 提供 LLM 可识别的 Tool Schema。

至少提供：

```text
search_web
rss_feed
```

每个 Schema 至少包含：

```text
name
description
parameters
```

例如 Search Tool：

```text
name:
search_web

description:
Search external information for the given query.

parameters:
query: string
```

RSS Tool 的参数根据当前项目真实接口设计，不要为了 Tool Calling 强行增加无意义参数。

---

### 6.3 Implement Explicit Agent Loop

必须手写 Agent Loop。

不允许使用 Agent Framework 隐藏核心流程。

基础逻辑应接近：

```python
for iteration in range(max_iterations):

    response = call_llm(messages, tools)

    if response contains no tool_calls:
        return parse_final_response(response)

    for tool_call in response.tool_calls:

        tool_result = execute_tool(tool_call)

        messages.append(
            tool_result_as_tool_message
        )

raise MaxIterationsError(...)
```

关键步骤必须在代码中清晰可见。

---

### 6.4 Tool Dispatcher

建立最小 Tool Registry / Dispatcher。

示例：

```python
tool_registry = {
    "search_web": ...,
    "rss_feed": ...,
}
```

调用链需要清楚表现：

```text
LLM tool name
      ↓
Tool Registry
      ↓
Python Function / Tool Instance
```

不要使用复杂依赖注入框架。

---

### 6.5 Parse Tool Arguments

必须解析 LLM 返回的 Tool Arguments。

例如：

```python
json.loads(tool_call.function.arguments)
```

需要处理：

* 非法 JSON
* 缺少必填参数
* 参数类型不正确

可以使用已有 Pydantic Model 或最小参数校验模型。

不要过度设计参数系统。

---

### 6.6 Execute Tool

根据 `tool_call.name` 找到对应 Tool 并执行。

必须处理：

* Search Tool
* RSS Tool
* Unknown Tool

未知 Tool 不允许静默忽略。

---

### 6.7 Serialize Tool Result

Tool Result 在重新传给 LLM 之前必须转换为 JSON Serializable 数据。

禁止直接把复杂 Python 对象交给 SDK。

例如：

```python
model.model_dump()
```

或：

```python
json.dumps(...)
```

目标是形成类似：

```text
Python Object
   ↓
Serializable Data
   ↓
JSON String
   ↓
role=tool
```

---

### 6.8 Append Tool Observation

Tool 执行完成后，需要将 Tool Result 加入 messages。

结构参考：

```python
{
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": serialized_result
}
```

这一过程必须保留在 Agent Loop 中，不能隐藏在框架内部。

---

### 6.9 Continue Agent Loop

Tool Result 加回 Context 后，再次调用 LLM。

LLM 应可以：

```text
继续调用 Tool
```

或者：

```text
生成 Final Answer
```

本任务必须支持多轮 Tool Calling，而不是：

```text
LLM → Tool → Final
```

这种写死的两次调用模式。

---

### 6.10 Max Iterations

Agent Loop 必须提供 `max_iterations`。

例如：

```python
max_iterations = 5
```

超过限制后抛出明确异常。

目的：

```text
防止模型无限 Tool Calling
```

无需实现复杂 Token Budget 或 Cost Budget。

---

## 7. Structured Final Output

最终 Agent 输出继续使用项目已有的结构化 Schema。

优先复用：

```text
ResearchResponse
```

如果当前 Schema 与 Agent 最终输出确实存在明显冲突，可以做最小必要调整。

不要另外设计一整套重复 DTO。

最终链路必须体现：

```text
Tool Result
  ↓
LLM Context
  ↓
LLM Final Output
  ↓
Pydantic Validation
  ↓
ResearchResponse
```

---

## 8. Error Handling

至少区分以下错误：

### LLM / API Error

例如：

```text
网络错误
API 调用失败
模型响应异常
```

### Invalid Tool Arguments

例如：

```text
arguments 不是合法 JSON
缺少 query
参数类型错误
```

### Unknown Tool

例如：

```text
LLM 请求了不存在的 tool name
```

### Tool Execution Error

复用当前 Tool 层异常。

例如：

```text
SearchToolError
RSSToolError
```

Agent 层负责转换为合理的 Agent Error。

### Max Iterations

当 Agent 达到最大循环次数仍未生成 Final Answer 时：

```text
raise AgentMaxIterationsError
```

不要建立复杂 Exception Hierarchy。

---

## 9. Testing Requirements

只测试 Agent Loop 的关键行为。

至少覆盖：

### Test A

LLM 不调用 Tool。

```text
LLM
→ Final Response
```

验证：

```text
Agent 可以直接返回结构化结果
```

### Test B

LLM 请求 Search Tool。

验证：

```text
tool_call.name
→ search_web
→ SearchTool executed
```

### Test C

LLM 请求 RSS Tool。

验证：

```text
tool_call.name
→ rss_feed
→ RSS Tool executed
```

### Test D

Tool Result 被正确加入 Messages。

需要验证存在：

```text
role = tool
tool_call_id
content
```

### Test E

Unknown Tool。

例如：

```text
tool_call.name = "unknown_tool"
```

应抛出明确异常。

### Test F

Invalid Tool Arguments。

例如：

```text
{invalid json
```

应抛出明确异常。

### Test G

Max Iterations。

Mock LLM 每次都继续请求 Tool。

Agent 最终需要触发：

```text
AgentMaxIterationsError
```

---

## 10. Code Readability Requirements

这是学习项目。

Agent Loop 的核心步骤必须显式保留。

建议使用注释：

```python
# 1. Ask the LLM what to do next

# 2. Inspect requested tool calls

# 3. Execute tools

# 4. Append tool observations to context

# 5. Continue loop or return final answer
```

不要把全部逻辑封装到一个看不到过程的 abstraction 中。

---

## 11. Out of Scope

本任务禁止主动引入：

* LangChain
* LangGraph
* CrewAI
* AutoGen
* MCP Server
* Multi-Agent
* Redis
* Database
* Vector Database
* RAG
* Async Worker
* Queue
* Memory System
* Retry Framework
* Observability Platform
* Streaming
* Prompt Management Platform

这些不是 TASK-005 的学习目标。

遵循 YAGNI。

---

## 12. Constraints

必须：

* 复用当前代码结构
* 尽量保持修改范围小
* 保持现有测试通过
* 不删除 Day01-Day04 已完成能力
* 不提前开发 Day06
* 不为了“企业级”而增加复杂度
* 优先保证 Agent Loop 可读性

---

## 13. Definition of Done

满足以下条件才可以认为 TASK-005 完成：

* [x] 新增 ResearchAgent 或等价 Agent Layer
* [x] LLM 可以看到至少两个 Tool Schema
* [x] Agent 可以识别 LLM 返回的 tool_calls
* [x] Agent 可以通过 tool name 找到真实 Python Tool
* [x] Agent 可以解析 tool arguments
* [x] Agent 可以执行 Search Tool
* [x] Agent 可以执行 RSS Tool
* [x] Tool Result 可以序列化
* [x] Tool Result 会以 role=tool 加入 messages
* [x] Agent 会再次调用 LLM
* [x] Agent 支持连续多轮 Tool Calling
* [x] Agent 有 max_iterations
* [x] Final Output 经过 Pydantic 校验
* [x] 关键异常场景有测试
* [x] 原有测试保持通过

---

## 14. Learning Verification

代码完成后，不要直接进入下一个任务。

请向学习者解释以下问题。

### Question 1

LLM 为什么不能直接执行：

```python
search_tool.search(query)
```

### Question 2

Tool Schema 在整个 Agent 系统中的作用是什么？

### Question 3

`tool_call.name = "search_web"` 是如何最终映射到真实 Python Tool 的？

### Question 4

Tool 执行结束以后，为什么还要：

```python
messages.append({
    "role": "tool",
    ...
})
```

### Question 5

为什么 Agent Loop 通常需要：

```python
while / for
```

而不是固定两次 LLM 调用？

### Question 6

以下两种模式有什么本质区别？

```text
Workflow:

Code
→ RSS
→ Search
→ Response
```

```text
Agent:

LLM
→ Decide
→ Tool
→ Observe
→ Decide
```

---

## 15. Codex Execution Instructions

开始实现前：

1. 阅读本文件
2. 阅读项目中的 Learning Roadmap
3. 阅读 LEARNING_STATE
4. 阅读 AI_CONTEXT
5. 检查当前代码实际状态
6. 不要假设文档描述一定与代码完全一致
7. 如果代码状态与文档存在差异，以当前代码为事实基础，并在结果中说明

完成实现后：

不要继续 TASK-006。

请输出：

### 1. Implementation Summary

说明本次实现了什么。

### 2. Files Changed

列出：

```text
新增文件
修改文件
测试文件
```

### 3. Agent Loop

用流程图说明当前真实调用链。

### 4. Key Code

挑出最重要的三段代码：

```text
Tool Schema
Tool Dispatcher
Agent Loop
```

并解释作用。

### 5. Tests

说明：

```text
新增了哪些测试
测试结果
```

### 6. Learning Notes

重点解释：

```text
Tool Schema
Tool Call
Tool Execution
Tool Result
Observation
Agent Loop
Structured Output
```

### 7. Issues / Deviations

如果实现与本 TASK 文档存在任何差异，请明确列出。

不要静默调整需求。

---

## 16. Final Learning Goal

TASK-005 完成后，学习者应该能够脱离代码，用自己的话完整描述：

```text
用户提出 Goal

→ Agent 将 Goal、Context、Tool Schemas 发给 LLM

→ LLM 根据当前信息决定下一步

→ 如果需要外部能力，LLM 返回 Tool Call

→ Agent Runtime 根据 Tool Name 找到真实 Python Tool

→ Agent Runtime 解析 Arguments

→ Python Tool 真正执行

→ Tool 返回 Observation

→ Observation 被序列化

→ 以 role=tool 加回 LLM Context

→ LLM 再次决策

→ 可能继续调用 Tool

→ 或输出 Final Answer

→ Final Answer 通过 Pydantic Schema 校验
```

真正掌握这条链路，才算完成 Day05。
