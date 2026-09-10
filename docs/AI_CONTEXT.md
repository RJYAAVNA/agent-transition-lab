# AI Context

本文件用于 Codex 与 ChatGPT 同步当前有效上下文。保持简洁，只保留当前仍然有效的信息。

## Current Goal

维护一个 Java Backend -> Agent Engineer 三个月学习实践项目，并以 Day1-Day4 迁移代码作为当前实战基础。

## Current Architecture

当前项目是一个 Python FastAPI 后端，包含两条学习价值不同的路径：

- `/research` API：通过 `ResearchService` 调用 RSS 和 Search 工具，返回结构化 `ResearchResponse`。
- `OpportunityResearchAgent`：保留 Day3 Tool Calling / Agent Loop 学习代码，当前主要由测试覆盖，尚未接入 `/research` API。

## Main Modules

- `src/app/main.py`：FastAPI 应用入口
- `src/app/api/research.py`：`/research` API 路由
- `src/app/services/research_service.py`：研究业务服务，编排 RSS/Search 工具并转换 Evidence
- `src/app/tools/`：RSS、Search 和 legacy Agent tool dispatcher
- `src/app/schemas/research.py`：请求、响应和 Agent 领域输出模型
- `src/app/agent.py`：Day3 Tool Calling Agent Loop
- `tests/`：API、Service、Tool、Schema 和 Agent Loop 测试
- `notes/DAY3_AGENT_LOOP_GUIDE.md`：Day3 历史学习说明

## Important Domain Models

- `ResearchRequest`
- `ResearchResponse`
- `Signal`
- `Opportunity`
- `Risk`
- `Evidence`
- `RSSItem`
- `SearchResult`

## Main Call Chains

```text
HTTP POST /research
  -> API route
  -> ResearchService.research()
  -> RSSFeedTool.fetch()
  -> RSSItem
  -> SearchTool.search()
  -> SearchResult
  -> Evidence
  -> ResearchResponse
```

```text
OpportunityResearchAgent.research()
  -> LLM chat.completions.create()
  -> tool_calls: search_web
  -> execute_tool()
  -> search_web()
  -> tool result appended to messages
  -> LLM final JSON
  -> ResearchResponse
```

## External Dependencies

- FastAPI
- Uvicorn
- Pydantic
- OpenAI SDK
- feedparser
- httpx2
- pytest
- Wikipedia Search API compatible endpoint
- RSS/Atom feed endpoint

## Recent Structural Changes

- 2026-09-10：初始化 Git 仓库，准备以 `main` 分支推送到 GitHub 远端 `RJYAAVNA/agent-transition-lab`。
- 2026-09-10：将 Day1-Day4 旧项目代码迁移到 `src/app/`，测试迁移到 `tests/`。
- 2026-09-10：保留 Day3 Agent Loop 学习说明到 `notes/DAY3_AGENT_LOOP_GUIDE.md`。
- 2026-09-10：初始化项目目录和长期文档结构。

## Known Issues

- 尚未创建具体 TASK。
- `/research` 当前走 RSS/Search Service，不走 `OpportunityResearchAgent`。
- `src/app/tools/__init__.py` 同时承担 legacy mock tool 和 dispatcher，命名容易与 RSS/Search tool 混淆。
- 配置加载为手写 `.env` 解析，后续是否引入更正式配置方案待定。
- 外部 RSS/Search 请求的集成测试缺失，当前测试主要覆盖解析和错误边界。

## Current Task

初始化 Git 仓库并推送 `main` 分支到 GitHub。

## Next Recommended Task

创建 `tasks/TASK-001.md`，明确下一步是继续沿 `/research` Service 路径演进，还是把 `OpportunityResearchAgent` 接入 API 路径。
