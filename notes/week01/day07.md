# Day07 - Structured Agent State

## Learning Goal

把 Day06 中分散在 `messages`、循环变量和 trace 里的执行上下文，整理成显式、可观察、可测试的 `AgentState`，并让 Runtime 负责推进和更新它。

## Acceptance Review

- AgentState 的初始字段和默认值：通过。代码与测试覆盖 `pending`、step `0`、空 observations 和空 final result。
- Runtime 状态更新：通过。测试覆盖单工具、多步、completed、max_steps 和 error 路径。
- 设计理解验收：部分通过。仓库有实现和测试证据，但当前没有学习者独立回答 checkpoints 的记录，不能据此升级能力等级。

## Core Mental Model

`messages` 表示 LLM 看到了什么；`AgentState` 表示 Agent 执行到哪里、收集了什么、当前处于什么状态以及最终结果是什么；`trace` 表示这次运行如何发生，三者职责不同。

## Main Call Flow

```text
ResearchAgent
  -> AgentState(pending, step=0)
  -> AgentRuntime(status=running)
  -> current_step += 1
  -> LLM decision
  -> ToolExecutor
  -> ToolObservation
  -> state.observations + state.messages
  -> next step
  -> final ResearchResponse
  -> state.final_result + status=completed
```

达到步数上限时，状态为 `max_steps` 且没有 final result；Runtime 异常时状态为 `error`，并保留已执行的部分状态和 trace。

## Key Concepts

- 最小 State 包含 `goal`、`messages`、`current_step`、`observations`、`status` 和 `final_result`。
- `AgentState` 是一次运行的可观察数据，不包含 Tool 实例、LLM Client、API Key 或隐藏推理过程。
- Runtime 拥有执行控制权：推进 step、执行工具、写入 observation、校验最终结果并决定何时停止。
- 模型拥有决策权：决定是否请求工具以及下一步需要什么信息，但不能越过 Runtime 的边界直接执行代码或无限循环。
- `AgentRunResult` 同时保留 final result、state 和 execution trace，便于分别理解结果、当前状态和运行过程。

## Why

只依赖 message history 会把“模型上下文”和“程序执行状态”混在一起。显式 State 让测试可以直接断言 step、observation、终止状态和 final result，也为后续恢复或观测留下清晰边界，而不需要先解析 messages 或 trace。

## Java Analogy

可以把 `AgentState` 类比为一次请求或任务执行的 application DTO / aggregate snapshot，把 `AgentRuntime` 类比为控制流程的 orchestration service。`messages` 更像传给外部模型的协议上下文，`ExecutionTrace` 更像结构化运行记录；它们不应互相替代。

## Common Misunderstandings

- State 不是把所有运行时对象都塞进一个上下文容器。
- messages 里有历史消息，不代表它已经表达了当前 step、最终状态或失败原因。
- `max_steps` 不是普通调参，而是防止模型持续请求工具的 Runtime safety boundary。
- Tool failure 作为 observation 返回，不等于忽略错误；Runtime 仍记录失败，模型获得一次受控的修正机会。
- Execution trace 不是 hidden Chain-of-Thought，也不等同于普通 application log。

## Current Evidence

代码和测试已经覆盖 initial、单工具、多步、completed、max_steps 和 error 状态；这些证明实现行为已经落地。学习者是否能够独立说明 State 在 Runtime 中的更新位置，以及为什么保留旧的 `run(messages, ...)` API，仍待回答 checkpoints 后确认。

## Still Unclear

- 需要用自己的话独立解释 Message History 与 AgentState 的边界。
- 需要独立说明 Runtime 如何在模型决策之后重新取得控制权。
- 需要进一步区分可恢复 State、Execution Trace 和未来的 checkpoint persistence。
- Day06 的 Mandatory Learning Checkpoints 仍未由学习者填写答案。

## Day Conclusion

- Agent 执行上下文不应只隐藏在 messages、局部变量和 trace 中。
- `AgentState` 明确承载进度、观测、状态和结果。
- Runtime 负责状态推进和终止边界，LLM 只负责下一步决策。
- 当前代码验收已完成，但能力等级仍需学习者独立解释和排障来确认。
