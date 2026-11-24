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

## 项目结构和命令

- `src/app/` 包含 FastAPI、研究服务、Agent Runtime、配置与 RSS/Search 工具。
- `tests/` 包含离线测试。LLM 使用注入的假客户端，RSS/Search 使用固定数据或请求替身。
- `scripts/` 提供 Linux 和 Codex Cloud 安装及测试入口。
- `tasks/` 存放任务范围与验收条件。`docs/` 存放项目上下文、架构和学习状态，`notes/` 存放学习记录。
- Linux/Codex Cloud 安装用 `bash scripts/codex-setup.sh`，测试用 `bash scripts/codex-test.sh`，可追加 pytest 参数。
- Windows PowerShell 安装用 `py -m uv sync --locked --dev`，测试用 `py -m uv run --locked pytest`。
- 启动 API 用 `uv run --locked uvicorn --app-dir src app.main:app --host 127.0.0.1 --port 8765`，Windows 可将 `uv` 换成 `py -m uv`。
- 默认测试使用 Python 3.11+ 和 `uv.lock`，无需数据库、真实凭证或外部 API。云端配置见 [CODEX_CLOUD_SETUP.md](docs/CODEX_CLOUD_SETUP.md)。
- 提交配置示例时使用空值和公开默认值。真实凭证只通过本地忽略文件或云端凭证配置提供。

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

## Git 分支管理

- `main` 始终保存已完成、测试通过且可继续开发的版本。
- 每个 TASK 从最新 `main` 创建独立分支，命名为 `feature/TASK-XXX-short-name`。
- 一个 TASK 跨多天时继续使用同一分支；同一天有多个独立 TASK 时分别创建分支。
- 任务完成后运行测试、更新文档，通过 Pull Request 检查差异后合入 `main`。
- 默认使用 Squash Merge，使一个 TASK 在 `main` 上对应一个提交；合入后删除任务分支。
- 多个 Codex 任务并行开发时，为每个任务使用独立 Git worktree。
- 保留其他任务的未提交改动，先确认当前分支和工作区。云端从 GitHub 可见的目标分支继续，本地未推送的提交和未提交文件不会同步。
- 检查差异与测试结果后交由用户决定提交、推送和合并。本任务禁止自动推送或合并到 `main`。
