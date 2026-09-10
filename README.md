# Agent Transition Lab

这是一个用于 **Java Backend -> Agent Engineer** 的三个月学习实践项目。

本项目同时承担：

- Agent 技术学习
- 实战代码开发
- 学习状态管理
- 架构演进记录
- Codex 与 ChatGPT 之间的上下文同步

## 项目目标

帮助具备 Java 后端经验的开发者，在三个月内逐步建立 Agent Engineer 所需的核心能力，并通过持续的小型实战项目沉淀可运行代码、架构记录和学习状态。

## 当前阶段

当前阶段：Day1-Day4 旧项目代码已迁移，正在作为后续学习实践基础。

## 项目结构

```text
agent-transition-lab/
├── README.md
├── AGENTS.md
├── docs/
│   ├── LEARNING_ROADMAP.md
│   ├── LEARNING_STATE.md
│   ├── CAPABILITY_MATRIX.md
│   ├── AI_CONTEXT.md
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   └── glossary.md
├── notes/
├── tasks/
├── src/
│   └── app/
├── tests/
└── examples/
```

## 如何运行

安装依赖：

```powershell
py -m uv sync --dev
```

运行测试：

```powershell
py -m uv run pytest
```

启动 FastAPI 服务：

```powershell
py -m uv run uvicorn --app-dir src app.main:app --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 文档入口

- [AGENTS.md](AGENTS.md)：Codex 后续开发规则
- [docs/AI_CONTEXT.md](docs/AI_CONTEXT.md)：当前有效上下文
- [docs/LEARNING_STATE.md](docs/LEARNING_STATE.md)：学习状态
- [docs/CAPABILITY_MATRIX.md](docs/CAPABILITY_MATRIX.md)：Agent Engineer 能力矩阵
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：当前架构
- [docs/DECISIONS.md](docs/DECISIONS.md)：重要技术决策记录
- [docs/LEARNING_ROADMAP.md](docs/LEARNING_ROADMAP.md)：三个月学习路线结构
