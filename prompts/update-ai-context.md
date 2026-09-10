本次 TASK 的代码开发已经完成。

现在不要继续开发任何新功能。

请基于当前仓库的真实代码状态更新：

docs/AI_CONTEXT.md

开始前：

1. 查看本次 git diff
2. 查看本次修改涉及的实际代码
3. 阅读当前 docs/AI_CONTEXT.md
4. 必要时阅读 docs/ARCHITECTURE.md

更新原则：

AI_CONTEXT.md 描述的是：

**项目当前真实状态**

而不是开发日志。

请检查并更新以下内容：

## Current Goal

当前项目正在解决什么问题。

只保留当前有效目标。

## Current Architecture

根据真实代码更新当前模块关系。

不要描述不存在或计划中的模块。

## Main Modules

列出目前真正存在的重要模块及职责。

不要罗列所有文件。

## Important Domain Models

记录当前重要业务模型，以及模型之间的关系。

例如：

SearchResult
→ Evidence

只有真实存在于代码中的模型才记录。

## Main Call Chains

根据当前代码更新最重要的调用链。

例如：

User Input
→ ResearchWorkflow
→ SearchTool
→ SearchService
→ SearchClient
→ SearchResult
→ Evidence

必须以实际代码为准。

## External Dependencies

记录当前实际使用的重要外部服务或核心框架。

不要记录普通 Python 标准库。

## Recent Structural Changes

根据本次 TASK 增加一条简短记录。

只保留最近 3–5 次重要结构变化。

旧内容超过数量后删除。

不要将这里写成完整 ChangeLog。

## Known Issues

重新检查当前代码。

只记录当前仍然存在的问题。

已经解决的问题删除。

不要因为 Roadmap 中未来会实现某功能，就把“暂未实现未来功能”算作 Issue。

## Current Task

标记刚刚完成的 TASK。

如果 TASK 已完成，明确：

Completed: TASK-XXX

## Next Recommended Task

只根据当前代码状态给出一个技术上的下一步建议。

注意：

最终学习顺序由 LEARNING_ROADMAP 和 ChatGPT 决定。

这里的建议不能自行改变学习路线。

---

更新完成后再次检查：

AI_CONTEXT.md 必须满足：

1. 与当前真实代码一致
2. 没有已经失效的架构描述
3. 没有大段代码
4. 没有详细开发流水账
5. 没有未来功能幻想
6. 总体保持简洁
7. 新的 AI 或开发者能通过它快速理解当前项目

最后只向我输出：

1. 本次更新了哪些 AI_CONTEXT 内容
2. 删除了哪些失效信息
3. 当前最重要的 Main Call Chain
4. 是否发现文档与代码不一致

不要继续修改业务代码。
