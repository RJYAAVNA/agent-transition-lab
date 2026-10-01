# Capability Matrix

状态说明：

- 未学习
- 学习中
- 基本掌握
- 可独立实现

> 代码已经实现不等于学习者已经掌握。没有独立解释和排查证据时，保持“学习中”。

| Capability | Status | Notes |
| --- | --- | --- |
| Python | 学习中 | 已有 FastAPI、Pydantic、pytest 基础实践，仍需持续补强 Python 工程表达 |
| LLM Fundamentals | 学习中 | 已有 OpenAI-compatible chat completions 调用链实践 |
| Prompt Engineering | 学习中 | 已有 Agent system prompt 和最终 JSON 输出要求 |
| Structured Output | 学习中 | 已有 Pydantic schema 与 LLM final JSON 校验实践 |
| Tool Calling | 学习中 | 已有 Tool Schema、tool_calls、dispatcher、参数校验和 observation 回填实践 |
| Agent Loop | 学习中 | 已有多步 loop、messages state、tool result 回传和 termination 实践；独立解释待验收 |
| Agent Runtime | 学习中 | 已有 `AgentRuntime`、`ToolExecutor`、`max_steps`、Tool Error Boundary 和 execution trace 实践 |
| RAG | 未学习 | 待学习知识库问答基本架构 |
| Embedding | 未学习 | 待学习向量表示与模型选择 |
| Retrieval | 学习中 | 已有 RSS/Search 结果到 Evidence 的筛选与转换，但尚未学习向量检索 |
| Memory | 未学习 | 待学习短期记忆、长期记忆和状态压缩 |
| MCP | 未学习 | 待学习 MCP 基本概念与工具接入 |
| Workflow | 学习中 | 已有确定性 `ResearchService` workflow，并开始比较 Workflow 与 Agent |
| Multi-Agent | 未学习 | 待学习多 Agent 分工、通信和风险控制 |
| Evaluation | 未学习 | 待学习离线评测、回归集和质量指标 |
| Observability | 学习中 | 已接触 application log、execution trace 和运行诊断；完整 Observability 体系待学习 |
| Testing | 学习中 | 已有 API、Service、Tool、Schema、legacy Agent Loop 和 Runtime 基础测试 |
| Deployment | 未学习 | 待学习 Agent 服务部署和运行时配置 |
| Java + Agent Integration | 学习中 | 已通过 Java 后端分层视角理解 Service / Tool / DTO 边界 |
