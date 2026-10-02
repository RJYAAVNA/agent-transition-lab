# TASK-008 — LLM-driven Tool Selection

## 0. Task Metadata

* **Day**: Day08
* **Stage**: Agent Fundamentals
* **Theme**: LLM-driven Tool Selection
* **Primary Goal**: 理解并实现由 LLM 决定 Tool Selection，而 Runtime 负责验证、执行和控制整个 Agent Loop。
* **Mode**: Learn by Building

---

# 1. Learning Position

Day01-Day05 已经完成：

```text
LLM
 ↓
Structured Output
 ↓
Tool Calling
 ↓
Real Tools
 ↓
ResearchAgent
```

Day06 完成：

```text
Agent Loop
Runtime
ToolExecutor
max_steps
Execution Trace
```

Day07 完成：

```text
AgentState
```

当前已经形成：

```text
Goal
 ↓
AgentState
 ↓
Runtime
 ↓
LLM
 ↓
Tool Call
 ↓
ToolExecutor
 ↓
Observation
 ↓
AgentState
 ↓
Next Step
```

Day08 不再主要研究 State，而是研究：

> **LLM 到底如何决定下一步应该调用什么 Tool。**

---

# 2. Core Learning Question

今天必须真正理解：

```text
为什么 Agent 不需要在代码里写：

if topic_requires_search:
    search_web()

elif topic_requires_rss:
    rss_feed()
```

而可以让：

```text
LLM
 ↓
根据 Tool Schema
 ↓
决定调用哪个 Tool
 ↓
生成 Tool Arguments
```

这意味着 Agent 的“行为选择”从：

```text
Application Code
```

逐步移动到：

```text
LLM Decision
```

但必须注意：

> LLM 获得的是“决策权”，不是“执行权”。

---

# 3. Core Mental Model

重点理解下面的架构：

```text
                    ┌─────────────────┐
                    │      LLM        │
                    │                 │
Goal + Messages ──→ │ Decide Next     │
                    │ Action          │
                    └────────┬────────┘
                             │
                      Tool Call
                             │
                             ↓
                    ┌─────────────────┐
                    │    Runtime      │
                    │                 │
                    │ Validate       │
                    │ Execute        │
                    │ Control Loop   │
                    └────────┬────────┘
                             │
                             ↓
                    ┌─────────────────┐
                    │  ToolExecutor   │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 ↓                       ↓
            SearchTool               RSSTool
                 │                       │
                 └───────────┬───────────┘
                             ↓
                        Observation
                             ↓
                         AgentState
                             ↓
                           LLM
```

今天必须明确：

```text
LLM
= Decision Maker

Runtime
= Execution Controller

ToolExecutor
= Execution Boundary

Tool
= Capability

AgentState
= Execution State
```

---

# 4. Current Problem

先检查当前 `ResearchAgent`。

确认当前 Tool Selection 是否已经主要由 LLM 完成。

重点检查：

```text
src/app/agents/research_agent.py
src/app/agents/runtime.py
src/app/agents/state.py
src/app/tools/
tests/
```

回答：

1. Tool Schema 是在哪里提供给 LLM 的？
2. LLM 如何知道有哪些 Tool？
3. LLM 返回 Tool Call 后谁解析它？
4. 谁判断 Tool 是否存在？
5. 谁校验 arguments？
6. 谁真正执行 Tool？
7. Tool 返回结果后谁把结果重新交给 LLM？
8. Runtime 是否可以拒绝执行一个 LLM 请求的 Tool？

如果当前代码已经实现其中大部分能力：

**不要重复实现。**

Day08 的重点是理解、梳理边界，并补齐缺失的工程行为。

---

# 5. Tool Selection 的三个层次

今天重点区分三个概念。

## 5.1 Tool Availability

系统告诉 LLM：

```text
你现在可以使用：

search_web
rss_feed
```

这来自：

```text
Tool Schema
```

---

## 5.2 Tool Selection

LLM 根据：

```text
User Goal
+
Conversation Context
+
Tool Description
```

决定：

```text
search_web
```

还是：

```text
rss_feed
```

或者：

```text
不调用 Tool
```

这是：

```text
LLM Decision
```

---

## 5.3 Tool Execution

LLM 返回：

```json
{
  "name": "search_web",
  "arguments": {
    "query": "..."
  }
}
```

之后：

```text
Runtime
 ↓
ToolExecutor
 ↓
search_web(...)
```

才是真正执行。

---

# 6. Critical Boundary

必须理解：

## LLM 可以决定：

```text
我要调用 search_web
```

## LLM 不能直接：

```text
执行 Python 函数
访问数据库
访问网络
修改文件
```

真正的流程：

```text
LLM
 ↓
Tool Call
 ↓
Runtime
 ↓
Validation
 ↓
ToolExecutor
 ↓
Actual Tool
```

因此：

> Tool Calling 本质上是 LLM 输出的一种结构化 Action Request。

而不是：

> LLM 直接执行函数。

---

# 7. Tool Schema Learning

阅读当前项目中的 Tool Schema。

重点理解类似：

```python
{
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "...",
        "parameters": {
            ...
        }
    }
}
```

回答：

### Q1

为什么 LLM 需要：

```text
name
description
parameters
```

而不是只告诉它：

```text
search_web
```

---

### Q2

Tool Description 为什么会影响 Tool Selection？

---

### Q3

如果两个 Tool 的 description 非常相似，会发生什么？

---

### Q4

Tool Schema 和 Python Function Signature 是不是同一个东西？

---

# 8. Implementation Task

在不大规模重构当前项目的情况下，确保当前 Agent 具备清晰的：

```text
LLM Decision
        ↓
Tool Call
        ↓
Runtime Validation
        ↓
Tool Execution
```

边界。

---

## Requirement A — LLM Receives Tool Definitions

确认每次需要进行 Agent Decision 的 LLM Request 都能够获得当前可用 Tool Schema。

不要：

```text
if query_type == ...
```

来代替 LLM Tool Selection。

---

## Requirement B — LLM Selects Tool

至少保留两个不同用途的 Tool：

```text
search_web
rss_feed
```

让 LLM 根据 Goal 自己决定。

例如：

```text
Goal:
Find current information about AI Agent engineering.

可能：

search_web
```

另一个：

```text
Goal:
Check recent articles from a specific RSS source.

可能：

rss_feed
```

不要在 Application Code 中根据关键词硬编码选择结果。

---

## Requirement C — Runtime Validates Tool Call

LLM 返回：

```text
tool_name
arguments
```

之后 Runtime / ToolExecutor 必须负责：

1. Tool 是否注册
2. arguments 是否是合法 JSON
3. arguments 是否符合 Tool 参数 schema
4. Tool 是否可以执行

---

## Requirement D — Unknown Tool

如果 LLM 返回：

```text
tool_name = "unknown_tool"
```

不能出现：

```python
KeyError
```

而应该产生一个受控 Observation。

例如：

```json
{
  "ok": false,
  "tool": "unknown_tool",
  "error": "unknown tool"
}
```

然后按照当前 Runtime 的既有机制继续处理。

不要额外设计复杂 Error Framework。

---

## Requirement E — Invalid Arguments

例如 Tool 需要：

```json
{
  "query": "..."
}
```

但 LLM 返回：

```json
{
  "wrong_field": "..."
}
```

应该：

```text
Tool Call
 ↓
Argument Validation
 ↓
Validation Error
 ↓
Observation
```

而不是直接让整个 Runtime 崩溃。

---

# 9. Decision vs Execution

必须检查并保持以下边界：

```text
ResearchAgent
    ↓
提供 Tool Schema
    ↓
LLM
    ↓
决定 Tool
    ↓
AgentRuntime
    ↓
ToolExecutor
    ↓
Tool
```

不要让：

```text
ResearchAgent
```

直接：

```text
if tool_name == ...
```

执行具体 Tool。

如果当前实现已经满足，则不要为了形式修改代码。

---

# 10. Tests

新增或完善测试。

---

## Test 1 — LLM Selects Search Tool

模拟：

```text
Goal
 ↓
LLM
 ↓
search_web
 ↓
Observation
 ↓
LLM
 ↓
Final
```

验证：

* LLM 返回的是 `search_web`
* Runtime 没有硬编码选择 Tool
* ToolExecutor 执行了 `search_web`
* Observation 写入 State
* 最终正常完成

---

## Test 2 — LLM Selects RSS Tool

模拟：

```text
Goal
 ↓
LLM
 ↓
rss_feed
 ↓
Observation
 ↓
LLM
 ↓
Final
```

验证同样的边界。

---

## Test 3 — Different Goal, Different Tool

构造两个不同 Goal。

例如：

```text
Goal A → search_web
Goal B → rss_feed
```

注意：

测试不是为了证明“LLM 很聪明”。

而是为了证明：

> Tool Selection 是由 LLM Response 决定，而不是由 Application Code 根据 Goal 硬编码决定。

---

## Test 4 — Unknown Tool

LLM：

```text
unknown_tool
```

验证：

```text
Runtime 不崩溃
 ↓
产生受控 Observation
```

---

## Test 5 — Invalid Arguments

LLM 返回：

```text
search_web
```

但参数不符合 schema。

验证：

```text
Argument Validation Error
 ↓
Observation
```

---

## Test 6 — No Tool Needed

LLM 第一轮直接返回最终结果。

验证：

```text
ToolExecutor 没有执行
status = completed
```

---

## Test 7 — Multi-step Selection

模拟：

```text
Step 1
LLM → search_web

Step 2
LLM → rss_feed

Step 3
LLM → final
```

验证：

```text
search_web
     ↓
observation
     ↓
rss_feed
     ↓
observation
     ↓
final
```

并检查：

```text
AgentState.current_step
AgentState.observations
AgentState.status
ExecutionTrace
```

都正确。

---

# 11. Important Anti-Pattern

重点检查项目中是否存在类似：

```python
if "news" in goal:
    tool = search_web

elif "rss" in goal:
    tool = rss_feed
```

如果存在：

不要简单删除。

先判断它是不是：

```text
Business Rule
```

还是：

```text
Tool Selection
```

如果它是在替代 LLM 做 Tool Selection，应移除或调整。

今天的目标不是：

> “所有 if 都不好。”

而是：

> **不能用 Application Code 偷偷替代本应该由 LLM 完成的 Tool Selection。**

---

# 12. State / Trace Verification

Day08 必须继续使用 Day07 的：

```text
AgentState
ExecutionTrace
```

不能重新设计新的状态系统。

确认一次完整运行后：

```text
AgentState
```

至少可以回答：

```text
Goal 是什么？
当前执行到第几步？
调用过哪些 Tool？
得到过哪些 Observation？
当前状态是什么？
最终结果是什么？
```

而：

```text
ExecutionTrace
```

回答：

```text
这次 Agent Run 是怎么执行的？
```

---

# 13. What Must NOT Be Added

本 TASK 禁止主动引入：

```text
LangChain
LangGraph
MCP
RAG
Memory
Multi-Agent
Database
Redis
Vector Database
Checkpoint Persistence
复杂 Retry Framework
Planning Framework
ReAct Framework
Frontend
```

也不要实现复杂的：

```text
Tool Ranking
Tool Recommendation Engine
Embedding-based Tool Retrieval
```

今天只理解最基础的：

```text
LLM
 ↓
Tool Schema
 ↓
Tool Selection
 ↓
Tool Call
 ↓
Runtime
 ↓
Tool Execution
```

---

# 14. Mandatory Learning Checkpoints

Codex 完成代码后，不要替我回答下面问题。

必须把问题留给我。

## Q1

为什么说：

```text
LLM 有 Tool Selection 权限
```

但：

```text
LLM 没有 Tool Execution 权限？
```

---

## Q2

Tool Calling 和普通 Function Calling 有什么本质区别？

至少从：

```text
调用者
决策者
执行者
参数来源
```

几个角度回答。

---

## Q3

为什么 Tool Description 会影响 LLM 的 Tool Selection？

如果两个 Tool：

```text
search_web
search_news
```

Description 非常相似，可能发生什么？

---

## Q4

下面两种设计有什么区别？

### Design A

```python
if "news" in goal:
    search_web()
```

### Design B

```text
Goal
 ↓
LLM
 ↓
Tool Call: search_web
 ↓
Runtime
 ↓
ToolExecutor
```

为什么 Agent 系统通常希望逐步从 A 走向 B？

---

## Q5

如果 LLM 返回：

```json
{
  "name": "search_web",
  "arguments": {
    "xxx": "abc"
  }
}
```

但 `search_web` 要求：

```json
{
  "query": "..."
}
```

这个错误应该由谁发现？

为什么？

---

## Q6

为什么 Runtime 不能完全相信 LLM 返回的 Tool Call？

---

## Q7

Day07 的：

```text
AgentState
```

和 Day08 的：

```text
Tool Selection
```

是什么关系？

---

## Q8

完整解释：

```text
User Goal
 ↓
LLM
 ↓
Tool Selection
 ↓
Tool Call
 ↓
Runtime
 ↓
ToolExecutor
 ↓
Tool
 ↓
Observation
 ↓
AgentState
 ↓
LLM
```

每一步分别负责什么。

---

# 15. Documentation

完成代码后更新：

## docs/LEARNING_STATE.md

记录：

```text
Day08
Theme:
LLM-driven Tool Selection

Learned:
- Tool Schema
- Tool Selection
- Tool Call
- Decision vs Execution
- Argument Validation
- Runtime Boundary

Implemented:
...

Problems:
...

My Understanding:
TODO - 留给学习者填写

Still Unclear:
...

Next:
...
```

特别注意：

**`My Understanding` 不要替我填写。**

---

## docs/AI_CONTEXT.md

只记录长期有效的信息。

例如：

```text
Agent Tool Selection is driven by LLM Tool Calls.
Runtime remains responsible for validation and execution.
ToolExecutor remains the execution boundary.
```

不要把当天的学习流水账全部写进去。

---

## docs/ARCHITECTURE.md

如果架构发生实际变化，再更新。

不要为了“完成任务”而机械修改。

---

## docs/DECISIONS.md

如果今天产生重要架构决策，再追加 ADR。

如果没有重要决策，不需要新增。

---

# 16. Implementation Process

开始修改之前：

1. 阅读：

```text
docs/LEARNING_ROADMAP.md
docs/LEARNING_STATE.md
docs/AI_CONTEXT.md
docs/ARCHITECTURE.md
docs/DECISIONS.md
```

2. 阅读：

```text
tasks/TASK-005.md
tasks/TASK-006.md
tasks/TASK-007.md
```

3. 阅读：

```text
src/app/agents/research_agent.py
src/app/agents/runtime.py
src/app/agents/state.py
src/app/tools/
tests/
```

4. 输出 5~10 行实施计划。

5. 判断当前 Tool Selection 已经实现到什么程度。

6. 不重复实现已经存在的能力。

7. 只补齐 Day08 学习目标需要的内容。

8. 增加自动化测试。

9. 运行完整：

```bash
pytest
```

10. 修复回归。

11. 更新学习文档。

12. 不自动开始 TASK-009。

---

# 17. Final Output

最终严格输出：

```text
TASK-008 Result

Changed Files
...

Current Tool Selection Flow
...

LLM Decision Boundary
...

Runtime Execution Boundary
...

Argument Validation
...

Tests
...

Key Design Decisions
...

What I Should Study
...

Questions For Me
Q1...
Q2...
Q3...
Q4...
Q5...
Q6...
Q7...
Q8...
```

不要替我回答 Questions For Me。

---

# 18. Definition of Done

只有满足以下条件才算 Day08 完成：

* [ ] LLM 可以根据 Tool Schema 选择 Tool。
* [ ] Application Code 没有偷偷替代 LLM 做 Tool Selection。
* [ ] Runtime 保留执行控制权。
* [ ] ToolExecutor 保留执行边界。
* [ ] Unknown Tool 有受控错误。
* [ ] Invalid Arguments 有受控错误。
* [ ] Tool Observation 能返回 LLM。
* [ ] AgentState 正确记录执行状态。
* [ ] ExecutionTrace 正常工作。
* [ ] 支持至少两种不同 Tool 的选择。
* [ ] 支持多 Step Tool Selection。
* [ ] No Tool Needed 场景正常。
* [ ] 全部 pytest 通过。
* [ ] LEARNING_STATE.md 更新。
* [ ] AI_CONTEXT.md 按需更新。
* [ ] 没有引入 Agent Framework。
* [ ] 能够独立回答 Mandatory Learning Checkpoints。

---

# 19. Today's Mental Model

今天不要记大量 API。

只需要真正理解：

```text
Tool Schema
     ↓
告诉 LLM “你有什么能力”
     ↓
LLM Decision
     ↓
告诉 Runtime “我想使用什么能力”
     ↓
Runtime Validation
     ↓
判断这个请求是否合法
     ↓
ToolExecutor
     ↓
真正执行
     ↓
Observation
     ↓
AgentState
     ↓
下一次 LLM Decision
```

最终形成一句自己的理解：

> **LLM 决定下一步做什么，Runtime 决定这个决定能不能执行以及执行后是否继续。**
