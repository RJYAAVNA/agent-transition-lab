# Learning State

## 当前学习阶段

Phase 1 - Agent Foundation。Day01-Day07 的代码实践和学习记录已经补齐，当前停在 Day07 Structured Agent State 的学习验收，不自动进入下一任务。

## 当前 Day

Day 7

## 当前状态判断

- Day01-Day04：已完成最小 LLM、Tool Calling、真实工具接入和分层建模代码实践。
- Day05：已完成独立 `ResearchAgent` 和真实 Tool Schema/Tool Calling。
- Day06：已完成 `AgentRuntime`、多步 loop、`max_steps`、Tool Error Boundary 和 Execution Trace。
- Day07：已完成独立 `AgentState`，Runtime 会更新 step、observation、终止状态和 final result。
- 代码验收和自动化测试已完成。
- 代码验收和自动化测试已完成；学习复盘证据仍不足以证明已经独立掌握，因此 Day07 暂记为 CONDITIONAL PASS，不自动进入下一 Day。

## 已有基础

- Java 后端工程经验。
- FastAPI、Pydantic、pytest 的 Python 项目实践。
- LLM 基本调用链、Prompt/Message 和结构化输出实践。
- Service、Tool、DTO 和领域模型的基础分层实践。

## 已完成的项目实践

- `ResearchResponse` 结构化输出和 Pydantic 校验。
- Day02 最小 Tool Calling：Tool Schema、tool call、dispatcher、tool result 回填。
- Day03 RSS/Search 外部数据源工具和解析异常边界。
- Day04 `SearchResult` / `RSSItem` 到 `Evidence` 的模型转换。
- Day05 `ResearchAgent`：`search_web`、`rss_feed`、LLM 决策和最终结构化结果。
- Day06 `AgentRuntime`：多步执行、同轮多个 tool call、`max_steps`、统一 `ToolExecutor`、失败 observation 和 execution trace。
- Day07 `AgentState`：显式保存 goal、messages、current_step、observations、status 和 final_result，并由 `AgentRuntime` 驱动更新。

## 需要强化的知识

- 用自己的话解释 Agent Loop、Action、Observation 和 State。
- 区分 Message History 与 Agent State：前者是模型上下文，后者是执行进度和结果。
- 独立说明 `AgentState` 如何由 Runtime 更新，以及它与 Execution Trace 的边界。
- 区分模型的决策权与 Runtime 的执行控制权。
- 独立解释 `max_steps` 和其他 termination condition 为什么是安全边界。
- 区分 Execution Trace、application log 和后续 Observability。
- 解释第三方 DTO、Agent Domain Model、Tool、Client、Service 的边界。
- Python 工程实践、异常分层和可测试性。

## 当前未解决问题

- `/research` API 仍然使用确定性 `ResearchService`，尚未接入新版 `ResearchAgent` / `AgentRuntime`；这是有意保留的学习边界，不是本轮任务缺陷。
- `src/app/tools/__init__.py` 的 Day03 legacy dispatcher 与真实 RSS/Search 工具仍同时存在，命名边界需要后续小步梳理。
- 外部 RSS/Search 请求缺少更完整的集成测试和运行时超时观测。
- Day06 的 Mandatory Learning Checkpoints 和 Day07 State Learning Checkpoints 尚未由学习者在文档中填写答案。

## 学习记录索引

- [Day01 - LLM Minimum Loop](../notes/week01/day01.md)
- [Day02 - Tool Calling Foundation](../notes/week01/day02.md)
- [Day03 - Real Tool Integration](../notes/week01/day03.md)
- [Day04 - Layering and Domain Model](../notes/week01/day04.md)
- [Day05 - Research Agent and Tool Calling](../notes/week01/day05.md)
- [Day06 - Controllable Agent Loop](../notes/week01/day06.md)
- [Day07 - Structured Agent State](../notes/week01/day07.md)

历史任务记录：

- [TASK-001](../tasks/TASK-001.md) 到 [TASK-004](../tasks/TASK-004.md) 是根据现有代码和路线补齐的历史任务说明。
- [TASK-005](../tasks/TASK-005.md) 和 [TASK-006](../tasks/TASK-006.md) 是仓库中已有的实现任务。
- [TASK-007](../tasks/TASK-007.md) 已完成代码实现和自动化测试。

## 下一学习目标

先完成 Day07 State Learning Checkpoints，确认可以独立解释：

```text
Message History != Agent State
AgentState
Runtime Control
max_steps
Tool Error Boundary
Execution Trace
```

是否进入下一 Day，由学习验收结果和 `LEARNING_ROADMAP.md` 决定，不由 Codex 自动推进。

## 最近一次更新时间

2026-10-01
