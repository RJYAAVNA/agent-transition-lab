# TASK-006 — Build a Controllable Agent Loop

## 0. Task Metadata

- **Day**: Day 06
- **Stage**: Agent Fundamentals
- **Theme**: 可控 Agent Loop：多步执行、终止条件、Trace、错误边界
- **Primary Goal**: 在不依赖 LangGraph 等 Agent Framework 的前提下，把当前单轮 Tool Calling Agent 升级为一个“可多步执行、可终止、可追踪、可测试”的 Agent Runtime。
- **Mode**: Learn by building
- **Important**: 本任务重点是理解 Agent Runtime 的底层机制，不追求复杂业务功能，不要为了“高级”而引入框架。

---

# 1. Background

当前项目已经具备以下基础能力：

1. 能通过 LLM 生成结构化结果。
2. 已实现 Tool Calling。
3. 已有 `search_web` / RSS / Search 等外部数据能力。
4. 已有 ResearchService / schema 等业务层结构。
5. 当前 Agent 执行逻辑仍偏向固定流程：
   - 请求 LLM
   - 判断是否调用工具
   - 执行工具
   - 再请求一次 LLM
   - 返回结果

这种实现可以帮助理解最基础的 Tool Calling，但它还不是真正通用的 Agent Loop。

一个更接近生产环境的 Agent Runtime 至少需要解决：

- 模型连续调用多个工具怎么办？
- 模型调用完工具后仍想继续调用工具怎么办？
- Agent 什么时候结束？
- 如果模型陷入循环怎么办？
- 一个 Tool 执行失败是否应该直接让整个 Agent 崩溃？
- 如何知道 Agent 每一步到底做了什么？
- 后续做日志、评估、Observability 时，从哪里拿执行轨迹？

Day06 就解决这些问题。

---

# 2. Learning Objectives

完成本任务后，我应该能够用自己的话解释：

1. 什么是 **Agent Loop**。
2. Agent 与普通 LLM 调用最大的区别是什么。
3. 为什么 Agent Runtime 必须存在 `max_steps`。
4. Agent 常见的终止条件有哪些。
5. `tool_call` 为什么本质上只是模型输出的一种结构化“动作请求”。
6. Tool Executor 与 Agent Loop 为什么应该解耦。
7. 为什么 Tool Exception 不应该默认直接炸掉整个 Agent。
8. 什么是 Execution Trace，它与普通 application log 有什么区别。
9. 为什么“模型觉得完成了”不等于“系统一定允许结束”。
10. Framework（如 LangGraph）本质上帮我们封装了哪些底层能力。

---

# 3. Core Mental Model

请围绕下面这个状态机理解 Agent：

```text
User Input
    |
    v
+-----------+
| LLM Call  |
+-----------+
    |
    +----------------------+
    |                      |
 tool_calls             final answer
    |                      |
    v                      v
Execute Tools          Validate Result
    |                      |
    v                      v
Append Results           END
    |
    v
Next LLM Call
    |
    +---- repeat ---->
```

核心不是“让 LLM 回答问题”，而是：

> Agent Runtime 不断把当前状态交给模型，由模型决定下一步 Action，再由 Runtime 执行 Action，并把 Observation 返回给模型，直到满足终止条件。

可以将其抽象为：

```text
Thought / Decision
        ↓
Action
        ↓
Observation
        ↓
Next Decision
```

注意：

- 不要求模型输出显式 Chain-of-Thought。
- 项目中只保存可观察的 `Action / Observation / Result`。
- 不记录、打印、要求模型返回隐藏推理过程。

---

# 4. Implementation Scope

本任务需要在现有项目基础上实现一个轻量级 Agent Runtime。

建议结构如下，但必须先阅读现有项目结构，再决定最终文件位置：

```text
app/
├── agent.py
├── agent_runtime.py        # 可新增
├── tools.py
├── models.py / schemas/
└── ...
```

如果当前项目结构已有更合理位置，应复用现有结构，不要机械创建重复模块。

---

# 5. Requirements

## 5.1 Agent Loop

实现一个通用循环，伪代码：

```python
messages = initial_messages()

for step in range(max_steps):
    response = call_llm(messages)

    if response.has_tool_calls:
        tool_results = execute_tools(response.tool_calls)
        messages.extend(...)
        continue

    final_result = parse_final_response(response)
    return final_result

raise AgentMaxStepsExceeded(...)
```

要求：

- 默认 `max_steps` 建议为 `5`。
- 不允许无限 while。
- step 计数语义必须清晰。
- 每一轮模型请求算一个 Agent Step。
- 支持一轮返回多个 tool calls。
- 一轮多个 tool calls 可以顺序执行，本任务暂不要求并行。

---

## 5.2 Termination Conditions

至少实现以下终止条件：

### Condition A — Normal Completion

模型没有返回 `tool_calls`，且输出能被成功解析为最终结构化结果。

### Condition B — Maximum Steps

达到 `max_steps` 后仍未获得最终答案：

```python
class AgentMaxStepsExceeded(RuntimeError):
    ...
```

异常信息至少包含：

- max_steps
- 已执行 step 数
- 最后一步的可观察状态摘要

不要把完整 prompt、API Key 或敏感数据放入异常。

### Condition C — Invalid Final Result

如果模型返回 final answer，但无法通过现有 schema / parser 校验，应进入明确的错误路径。

优先复用项目现有结构化输出校验逻辑。

---

# 6. Tool Registry

当前如果仍然存在类似：

```python
if tool_name == "search_web":
    ...
elif tool_name == "...":
    ...
```

将 Tool 执行改造成 Registry 思路。

目标结构示例：

```python
TOOL_REGISTRY = {
    "search_web": search_web,
}
```

并提供统一入口：

```python
def execute_tool(name: str, arguments: dict) -> str:
    ...
```

要求：

1. 未注册 Tool 必须返回明确错误。
2. Tool arguments JSON 解析失败必须明确区分。
3. Tool 自身执行失败必须被 Runtime 捕获。
4. Agent Loop 不应该知道每个 Tool 的具体实现。

---

# 7. Tool Error Boundary

Tool 执行失败时，不要默认直接中断 Agent。

将 Tool Error 转换为可返回给模型的 Observation，例如：

```json
{
  "ok": false,
  "tool": "search_web",
  "error": "search provider timeout"
}
```

成功则类似：

```json
{
  "ok": true,
  "tool": "search_web",
  "result": "..."
}
```

然后作为 tool message 返回给模型，让模型有机会：

- 修改 query 后重试
- 改用其他策略
- 根据已有证据继续
- 最终明确告诉用户无法完成

但以下错误可以直接终止：

- Runtime 本身状态损坏
- 无法解析模型 tool call 基本结构
- 达到 max_steps
- 最终 schema 无法校验且项目当前没有 repair 机制

本 Day 不实现复杂 Retry Policy。

---

# 8. Execution Trace

新增最小化 Trace 数据结构。

例如：

```python
@dataclass
class AgentStepTrace:
    step: int
    tool_calls: list[str]
    tool_results: list[str]
    status: str
```

也可以使用 Pydantic，但应与项目现有风格保持一致。

完整执行结果可以类似：

```python
@dataclass
class AgentRunTrace:
    steps: list[AgentStepTrace]
    total_steps: int
    stop_reason: str
```

建议的 `stop_reason`：

```text
completed
max_steps
invalid_output
runtime_error
```

要求：

- Trace 面向工程诊断。
- 不保存隐藏 Chain-of-Thought。
- 不要求模型暴露 reasoning。
- 可以保存：
  - step
  - tool name
  - sanitized arguments
  - success / failure
  - duration（可选）
  - stop reason
- 不保存 API Key 等 Secret。

---

# 9. Keep Business Logic Separate

不要把 Opportunity Research 的业务逻辑和 Agent Runtime 全部混在一起。

理想依赖关系：

```text
OpportunityResearchAgent
        |
        v
    AgentRuntime
        |
        +------> LLM Client
        |
        +------> Tool Executor / Registry
        |
        +------> Trace
```

业务 Agent 负责：

- System Prompt
- Tool definitions
- 最终 schema
- 业务输入输出

Runtime 负责：

- Loop
- Step
- Tool execution orchestration
- termination
- trace
- runtime errors

这是本任务最重要的工程设计点之一。

---

# 10. Tests

必须新增自动化测试。

不得只靠手工运行验证。

至少覆盖：

## Test 1 — Direct Final Answer

LLM 第一轮直接返回最终答案。

期望：

```text
steps = 1
tool invocation = 0
stop_reason = completed
```

---

## Test 2 — One Tool Call

流程：

```text
LLM
 -> tool call
 -> tool result
 -> LLM
 -> final answer
```

期望正常完成。

---

## Test 3 — Multiple Sequential Tool Steps

流程至少：

```text
Step 1 -> search_web
Step 2 -> search_web
Step 3 -> final
```

用于证明 Agent Loop 不再局限于固定“两次 LLM 调用”。

---

## Test 4 — Multiple Tools in One Step

模型一次返回两个 tool calls。

期望：

- 两个都能执行。
- 两个 observation 都追加回 messages。
- 下一轮 LLM 能收到完整结果。

---

## Test 5 — Tool Failure

Tool 抛出异常。

期望：

- Runtime 不直接 crash。
- Tool failure 被转换成 observation。
- 模型可以继续下一步。

---

## Test 6 — Unknown Tool

模型请求一个未注册工具。

期望：

- 得到受控错误。
- 不出现 `KeyError` 等无语义异常。

---

## Test 7 — max_steps

Mock LLM 每轮都要求调用工具。

期望：

```text
AgentMaxStepsExceeded
```

验证不存在死循环。

---

## Test 8 — Invalid Final Output

最终结果无法通过 schema 校验。

期望进入明确失败路径。

---

# 11. Coding Constraints

Codex 修改项目时遵守：

1. **先阅读后修改**：
   - README
   - AI_CONTEXT.md
   - LEARNING_STATE.md
   - Learning Roadmap / ROADMAP
   - Day01-Day05 task 文档
   - 当前 Agent / Tool / Schema / Test 实现

2. 不大规模重构无关代码。

3. 遵循 YAGNI：
   - 不上 LangChain。
   - 不上 LangGraph。
   - 不引入 Redis。
   - 不引入消息队列。
   - 不做多 Agent。
   - 不做并行 Tool Calling。
   - 不做持久化 Memory。
   - 不做复杂 Retry / Backoff。
   - 不做前端。

4. 优先复用现有模型、schema、tool implementation。

5. 保持代码可测试。

6. LLM API 测试必须 Mock，不能让单元测试依赖真实付费 API。

7. 不提交 Secret。

8. `.env` 中的 Key 不允许进入 git。

---

# 12. Expected Runtime Example

实现后，应能表达如下执行：

```text
User:
Research whether AI Agent engineering is a good transition direction
for a Java backend engineer.

Step 1
LLM:
Need current market evidence.
Action:
search_web("AI agent engineer backend skills 2026")

Observation:
<search result>

Step 2
LLM:
Need evidence about Java/backend transferability.
Action:
search_web("Java backend to AI agent engineer skills")

Observation:
<search result>

Step 3
LLM:
Enough evidence.
Final:
OpportunityResearchReport(...)
```

Trace：

```json
{
  "total_steps": 3,
  "stop_reason": "completed",
  "steps": [
    {
      "step": 1,
      "tool_calls": ["search_web"],
      "status": "tool_called"
    },
    {
      "step": 2,
      "tool_calls": ["search_web"],
      "status": "tool_called"
    },
    {
      "step": 3,
      "tool_calls": [],
      "status": "completed"
    }
  ]
}
```

输出格式不要求完全一致，重点是语义。

---

# 13. Deliverables

完成任务后必须产出：

```text
1. 可多轮执行的 Agent Loop
2. max_steps 限制
3. Tool Registry / Executor
4. Tool Error Boundary
5. Execution Trace
6. 对应异常类型
7. 单元测试
8. README 或相关文档的必要更新
9. LEARNING_STATE.md 更新
10. AI_CONTEXT.md 更新
```

---

# 14. Documentation Update Requirements

## 14.1 LEARNING_STATE.md

完成后新增 Day06 学习记录，至少包含：

```markdown
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
- ...

### Problems Encountered
- ...

### My Understanding
- ...

### Still Unclear
- ...

### Next
- ...
```

其中 `My Understanding` 不要由 Codex 直接替我编答案。

Codex应保留 TODO，让我学习完成后自己填写。

---

## 14.2 AI_CONTEXT.md

只更新长期有效的项目状态：

- 当前 Agent Runtime 已支持多步 loop。
- 已具备 max_steps。
- 已统一 Tool Executor。
- 已具备 execution trace。
- 当前尚未引入 Agent Framework。

不要把当天流水账全部写进 AI_CONTEXT。

---

# 15. Mandatory Learning Checkpoints

Codex 完成实现后，不要只给我“代码已完成”。

请在最终回复中要求我回答下面的问题：

### Q1

下面代码为什么危险？

```python
while True:
    response = llm(...)
    if response.tool_calls:
        execute(...)
        continue
    return response
```

---

### Q2

为什么 `max_steps` 属于 Runtime Safety，而不只是一个普通配置项？

---

### Q3

Tool 执行失败时，为什么很多 Agent 系统会把错误作为 Observation 返回给模型，而不是直接抛异常结束？

---

### Q4

下面两者有什么区别？

```text
Application Log
Execution Trace
```

---

### Q5

为什么 Tool Registry 比在 Agent Loop 里不断写：

```python
if tool_name == ...
elif tool_name == ...
```

更适合后续 Agent 扩展？

---

### Q6

Agent Framework（例如 LangGraph）未来能帮我们减少哪些手写代码？

至少从以下角度回答：

```text
state
node
edge
loop
checkpoint
retry
observability
```

---

# 16. Definition of Done

只有同时满足以下条件才算 Day06 完成：

- [ ] Agent 可以执行超过 1 轮 Tool Calling。
- [ ] Agent 不存在无限循环。
- [ ] `max_steps` 有自动化测试。
- [ ] 一轮多个 tool calls 可处理。
- [ ] Tool 调用逻辑从 Agent 主循环解耦。
- [ ] Tool failure 有统一边界。
- [ ] 可以得到 execution trace。
- [ ] Trace 不包含隐藏 Chain-of-Thought。
- [ ] 最终结构化输出仍能通过现有 schema 校验。
- [ ] 所有新增/现有测试通过。
- [ ] README / 文档按需更新。
- [ ] `LEARNING_STATE.md` 更新。
- [ ] `AI_CONTEXT.md` 更新。
- [ ] 我能够回答 Mandatory Learning Checkpoints。

---

# 17. Codex Execution Instruction

请直接在当前项目中执行 TASK-006。

开始前：

1. 阅读项目目录结构。
2. 阅读 `Learning Roadmap`、`LEARNING_STATE.md`、`AI_CONTEXT.md`。
3. 阅读 `TASK-001.md` ~ `TASK-005.md`。
4. 阅读当前 Agent、Tool、Schema 和 tests。
5. 判断 TASK-006 与当前实现是否存在冲突。

如果项目实际状态已经部分实现本任务：

- 不重复造轮子。
- 说明哪些部分已经存在。
- 只补齐缺失能力。

然后：

1. 给出 5~10 行实施计划。
2. 直接修改代码。
3. 增加测试。
4. 运行完整测试。
5. 修复本任务引入的问题。
6. 更新相关文档。
7. 最终输出：

```text
## TASK-006 Result

### Changed Files
...

### What Was Implemented
...

### Tests
...

### Key Design Decisions
...

### What I Should Study
...

### Questions For Me
Q1...
Q2...
...
```

不要自动开始 TASK-007。

---

# 18. What I Need to Focus On Today

今天学习时，不要把注意力放在“Codex 写了多少代码”。

重点观察这 4 件事：

```text
1. Loop 怎么形成？
2. State 怎么在每一步之间传递？
3. Runtime 在哪里夺回模型的控制权？
4. 系统如何保证 Agent 最终停下来？
```

如果这四点理解清楚，Day06 才真正完成。

---

# 19. One-Sentence Summary

> Day06 的目标，是把“会调用工具的 LLM”升级成“由 Runtime 控制、能够多步行动并且一定可以被系统约束住的 Agent”。
