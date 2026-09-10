# Decisions

本文件采用简单 ADR 风格记录重要技术决策。

## ADR-0001: 初始化学习实践项目结构

### 日期

2026-09-10

### 决策

建立 `docs/`、`tasks/`、`notes/`、`src/`、`tests/`、`examples/` 的长期项目结构，并使用 `docs/AI_CONTEXT.md` 作为 Codex 与 ChatGPT 的简洁上下文同步入口。

### 原因

项目既承担学习管理，也承担代码实践和架构演进记录。固定目录和文档入口可以降低后续任务切换成本，避免上下文散落在对话历史中。

### 被放弃方案

- 只保留代码目录，不维护学习状态。
- 只通过聊天记录同步上下文。
- 一开始引入完整企业级工程结构。

### 后续影响

- 后续每个 TASK 都需要维护 `docs/AI_CONTEXT.md`。
- 架构变化需要同步更新 `docs/ARCHITECTURE.md`。
- 重要技术取舍需要追加到本文件。

## ADR-0002: 保守迁移 Day1-Day4 旧项目代码到 src/app

### 日期

2026-09-10

### 决策

将旧项目中仍有学习和运行价值的 FastAPI、Service、Tool、Schema、Agent Loop 和测试代码迁移到新仓库，并采用 `src/app` 作为源码目录。

### 原因

旧代码已经覆盖 LLM 调用链、Tool Calling、Service/Tool 职责划分、RSS/Search 证据获取和结构化输出，适合作为后续学习实践基础。迁移时保持原有 `app.*` import 和调用链，可以降低重写成本并保留学习连续性。

### 被放弃方案

- 将旧代码机械复制到仓库根目录。
- 立即改成全新的包名和分层架构。
- 将 Day3 Agent Loop 直接并入 `/research` API。

### 后续影响

- 运行 Uvicorn 时需要使用 `--app-dir src`。
- 后续 TASK 需要决定 `/research` 是否接入 `OpportunityResearchAgent`。
- `src/app/tools/__init__.py` 的 legacy dispatcher 命名边界后续需要小步梳理。
