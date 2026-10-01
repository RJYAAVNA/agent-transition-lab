# Day06 - Controllable Agent Loop

## 今日目标

把“会调用工具的 LLM”升级为“由 Runtime 控制的多步 Agent”：

```text
Goal
  ->
LLM Decision
  ->
Action
  ->
Observation
  ->
Next Decision
  ->
Final Result or Controlled Stop
```

本日重点观察四件事：

1. Loop 怎么形成。
2. State 怎么在每一步之间传递。
3. Runtime 在哪里夺回模型的控制权。
4. 系统如何保证 Agent 最终停下来。

## Runtime 的职责

`src/app/agents/runtime.py` 中的 `AgentRuntime` 负责：

- 初始化并持续传递 `messages`。
- 每次 LLM 请求计为一个 step。
- 判断模型返回的是 tool calls 还是最终答案。
- 将多个 tool call 顺序执行。
- 将 observation 追加回 LLM context。
- 通过 `max_steps` 限制运行长度。
- 记录 `AgentRunTrace`。

`ResearchAgent` 保留业务职责，`ToolExecutor` 保留工具注册、参数解析、工具调用和失败 observation 的职责。

## State 如何传递

当前最小 state 主要由 `messages` 和 trace 组成：

```text
messages
  = system message
  + user message
  + assistant tool-call message
  + tool observation message
  + ...
```

下一轮 LLM 调用使用更新后的 messages，因此模型可以看到之前的动作和工具结果。Trace 记录的是可观察的执行过程，不是隐藏的 Chain-of-Thought。

## Tool Error Boundary

未知工具、非法 JSON 参数和工具自身异常会被转换为受控 observation，例如：

```json
{
  "ok": false,
  "tool": "search_web",
  "error": "..."
}
```

这样模型有机会修改查询、换工具或输出无法完成的结果。Runtime 自身损坏、基本 tool call 结构无法解析、达到 `max_steps` 和最终 schema 校验失败，仍然可以终止运行。

## Termination Conditions

当前至少有三类终止：

1. `completed`：没有 tool calls，且最终结果通过 schema 校验。
2. `max_steps`：执行到上限仍未得到最终结果。
3. `invalid_output`：模型停止调用工具，但最终内容无法通过解析或 `ResearchResponse` 校验。

因此，“模型认为自己完成了”只是模型输出状态，是否允许系统结束还要经过 Runtime 和 schema 校验。

## Execution Trace

Trace 记录：

- step。
- tool name。
- tool call 是否成功。
- observation 摘要或序列化结果。
- 每一步状态。
- 总步数。
- stop reason。

Application log 主要服务于运行时诊断和排障；Execution Trace 面向一次 Agent Run 的结构化回放、测试和后续 Observability。两者可以同时存在，但用途不同。

## 自动化测试覆盖

`tests/test_research_agent.py` 已覆盖：

- 第一轮直接返回最终结果。
- 单工具调用。
- 连续多步工具调用。
- 同一轮多个工具调用。
- 工具执行失败。
- unknown tool。
- invalid tool arguments。
- `max_steps`。
- invalid final output。

## 当前验收状态

- 代码验收：已完成。
- 自动化测试：已完成。
- 学习理解验收：待学习者独立回答 Mandatory Learning Checkpoints。
- TASK-007：不自动开始。

## Mandatory Learning Checkpoints

请用自己的话回答：

1. `while True` 的 Agent Loop 为什么危险？
2. 为什么 `max_steps` 是 Runtime Safety，而不只是普通配置？
3. 为什么 Tool failure 常被作为 Observation 返回给模型？
4. Application Log 和 Execution Trace 有什么区别？
5. 为什么 Tool Registry 比不断堆叠 `if/elif` 更适合扩展？
6. LangGraph 等框架未来会替我们封装哪些 state、node、edge、loop、checkpoint、retry 和 observability 能力？

## 仍需强化

- 独立解释 Agent Loop、State、Runtime Control。
- 区分模型的决策权和 Runtime 的执行控制权。
- 解释为什么错误 observation 不等于忽略错误。
- 解释 Trace 如何为 Evaluation 和 Observability 提供数据。

