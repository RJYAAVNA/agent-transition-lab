# Day08 — LLM-driven Tool Selection

## Learning Goal

理解 Tool Selection 如何从应用代码中的固定规则转移为 LLM 根据 Tool Schema 做出的结构化决策，同时保留 Runtime 的验证、执行和循环控制权。

## Core Mental Model

LLM 只能提出 Tool Call，不能直接执行 Python 函数。Runtime 把 Tool Call 当作不可信的请求，交给 ToolExecutor 检查工具是否注册、JSON 是否有效、参数是否符合 schema，然后决定是否执行。执行结果形成 Observation，写入 AgentState 和 Message History，供 LLM 进行下一轮决策。

## Main Call Flow

```text
User Goal -> Runtime 初始化 AgentState -> LLM 接收 messages + Tool Schema
-> LLM 返回 Tool Call 或 Final Answer -> Runtime/ToolExecutor 校验
-> 执行 Tool -> Observation 写入 AgentState 和 messages -> LLM 再次决策
-> completed / invalid_output / max_steps / error
```

## Key Concepts

- Tool Schema 的 `name`、`description` 和 `parameters` 告诉 LLM 可用能力、用途和参数格式。
- `tool_choice="auto"` 表示允许模型自动选择；它不替代 Tool Schema，也不保证选择一定正确。
- Tool Selection 是 LLM 的决策；Tool Execution 是 Runtime/ToolExecutor 的职责。
- Tool Calling 比一次普通函数调用多了模型决策、Runtime 校验、Observation、State 更新和后续循环。
- Unknown tool、非法 JSON、schema 不匹配和工具异常都应转为受控 Observation。
- AgentState 记录执行进度和结果；Message History 是模型上下文；ExecutionTrace 记录本次运行如何发生。

## Why

Design A 在应用代码中根据关键词直接决定工具，规则固定在程序里。Design B 将目标和工具描述交给 LLM，由 LLM 返回 Tool Call，再由 Runtime 验证和执行。后者允许根据上下文选择能力，但必须保留 Runtime 边界。

## Java Analogy

Tool Schema 类似对外暴露的接口契约，ToolExecutor 类似校验请求 DTO 后调用具体 Service 的应用层边界。LLM 像根据接口说明提出调用请求的客户端，不能直接绕过服务端执行内部方法。

## Acceptance Review

- Q1：通过。能够说明 LLM 只有选择权，Runtime 才负责真实执行和控制。
- Q2：部分通过。已理解 Tool Calling 包含 observation 和 AgentState，但还需更准确地区分协议调用请求和 Agent 循环。
- Q3：部分通过。知道与 `tool_choice="auto"` 有关，但还需掌握 description、parameters 如何影响选择。
- Q4：未通过。还不能清楚解释关键词硬编码与 LLM Tool Call 的决策责任差异。
- Q5：通过。能够说明 Runtime 应在执行前校验参数。
- Q6：通过。知道模型输出可能是未知工具、错误 JSON 或非法参数，不能被完全信任。
- Q7：部分通过。知道 State 会影响后续上下文，但需修正为 State 记录选择造成的执行变化，而非专门为 LLM 选择工具而存在。
- Q8：部分通过。主链路正确，但终止还包括 final answer 合法性、`max_steps` 和 error 等 Runtime 条件。

## What I Can Explain Now

- LLM 决定调用哪个已声明的工具，Runtime 决定这个请求是否可以执行。
- ToolExecutor 如何把未知工具和非法参数转换成 Observation。
- Observation 如何回到 State 和下一轮 LLM 上下文。
- `max_steps` 如何作为 Agent Loop 的终止边界。

## Still Unclear

- Tool Schema 的 description 和 parameters 如何具体影响模型选择。
- 关键词路由与 LLM Tool Selection 的责任边界。
- AgentState、Message History 和 Tool Selection 的准确关系。
- Tool Calling 与一次普通 Function Calling 的协议层差异。

## Day Conclusion

- 已建立“LLM 决策、Runtime 执行控制”的基本边界。
- 已理解 Tool Call 是结构化 Action Request，而不是函数已经被执行。
- 已能解释 Observation 回填和多步循环的主路径。
- 已能识别未知工具和非法参数必须在 Runtime 边界受控处理。
- Day08 为 CONDITIONAL PASS，下一阶段需强化 Schema、硬编码路由和 State 边界。
