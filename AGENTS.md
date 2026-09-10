# AGENTS.md

本文件定义 Codex 在本仓库中长期工作的规则。所有后续任务都应遵循这些约束。

## 任务开始前

每次开始任务前，优先阅读：

- `AGENTS.md`
- `docs/AI_CONTEXT.md`
- 当前任务文件：`tasks/TASK-XXX.md`

如果任务涉及架构调整，额外阅读：

- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`

## 开发原则

- 禁止为了完成当前任务进行无关重构。
- 优先保持实现简单，遵循：
  - YAGNI
  - KISS
  - 单一职责
  - 清晰的模块边界
- 这是学习项目，不追求过早的企业级复杂设计。
- 新增抽象、框架、设计模式前，必须能够解释其当前必要性。
- 教学相关代码优先保证：
  - 可读
  - 可解释
  - 调用链清晰
- 教学相关代码不追求高度抽象，除非抽象本身是当前学习目标。

## 任务完成后

每次任务完成后必须：

- 运行已有测试。
- 补充必要测试。
- 汇总修改文件。
- 更新 `docs/AI_CONTEXT.md`。
- 如果架构变化，更新 `docs/ARCHITECTURE.md`。
- 如果产生重要技术决策，更新 `docs/DECISIONS.md`。

## 上下文维护

- `docs/AI_CONTEXT.md` 必须保持简洁。
- `docs/AI_CONTEXT.md` 只记录当前有效状态，不写流水账。
- 不得把旧实现和废弃设计继续留在 `docs/AI_CONTEXT.md`。
- `Recent Structural Changes` 只保留最近 3 到 5 项。

## 协作方式

- 当前任务只处理当前 TASK 明确要求的内容。
- 如果发现任务描述不完整，优先提出最小必要问题。
- 如果可以基于现有上下文安全推进，则先推进再记录假设。
- Codex 与 ChatGPT 之间通过 `docs/AI_CONTEXT.md`、`docs/LEARNING_STATE.md` 和 `tasks/` 目录同步上下文。

