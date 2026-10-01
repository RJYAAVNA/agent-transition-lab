# TASK-001 - LLM Minimum Loop and Structured Output

## 1. Task Metadata

- Task ID: TASK-001
- Day: Day01
- Phase: Agent Foundation
- Status: DONE
- Record type: Historical task reconstruction

> 该任务文件在仓库早期没有被保存。本记录根据 `LEARNING_ROADMAP.md`、当前源码、测试和后续任务的前置状态重建。它描述的是 Day01 的学习边界，不代表原始对话逐字记录。

## 2. Learning Objective

建立一个最小的 LLM 应用调用链，并能够解释：

1. 用户输入如何进入应用。
2. Prompt 和 messages 如何传给 LLM。
3. LLM 客户端在哪里发起请求。
4. 模型返回的文本如何被解析。
5. 为什么最终结果需要经过结构化模型校验。

Day01 的重点是先看清：

```text
User Input
    ->
Messages
    ->
LLM
    ->
JSON Content
    ->
Pydantic Validation
    ->
Structured Result
```

## 3. Current Project Context

当前项目的结构化研究结果使用 `ResearchResponse`，其中包含：

- `topic`
- `summary`
- `signals`
- `opportunities`
- `risks`
- `evidence`
- `confidence`

后续 Day02-Day06 在这条结构化输出链路上继续增加 Tool Calling、真实数据源和 Agent Runtime。

## 4. Implementation Scope

本任务应完成以下最小能力：

- 使用 OpenAI-compatible SDK 发起 chat completion。
- 将用户的研究主题放入 user message。
- 使用 system message 约束模型角色和输出格式。
- 将模型返回内容解析为 JSON。
- 使用 `ResearchResponse.model_validate()` 校验最终结果。
- 将配置从代码中分离到环境变量和 `Settings`。
- 对 LLM 调用失败、JSON 无效和 schema 校验失败提供明确错误。

当前代码中的主要落点：

- `src/app/core/config.py`
- `src/app/agent.py`
- `src/app/schemas/research.py`
- `tests/test_research_schemas.py`

## 5. Core Call Flow

```text
POST /research
  ->
ResearchRequest.topic
  ->
Agent messages
  ->
OpenAI-compatible client
  ->
message.content
  ->
json.loads()
  ->
ResearchResponse.model_validate()
  ->
ResearchResponse
```

## 6. Important Concepts

### 6.1 Message

LLM 请求不是简单地传入一个字符串，而是由带有 `role` 和 `content` 的 messages 组成。当前 Agent 至少需要 system message 和 user message。

### 6.2 Structured Output

JSON 文本只是传输格式，不等于已经满足业务契约。`ResearchResponse` 负责检查字段是否存在、列表是否非空以及 `confidence` 是否位于 `0` 到 `1` 之间。

### 6.3 Boundary Validation

模型输出是不可信的外部输入。解析和 Pydantic 校验把它转换成应用内部可以依赖的对象，也让错误更容易定位。

## 7. Definition of Done

- [x] 用户主题可以进入 LLM 请求。
- [x] LLM 调用使用明确的 messages。
- [x] 模型结果经过 JSON 解析。
- [x] 模型结果经过 `ResearchResponse` 校验。
- [x] 配置支持环境变量。
- [x] LLM、JSON 和 schema 错误有明确边界。
- [x] 测试不依赖真实付费 API。

## 8. Learning Verification

完成 Day01 后，学习者应该能够回答：

1. 用户输入从哪个对象进入应用？
2. LLM 调用具体发生在哪一层？
3. `json.loads()` 和 Pydantic 校验分别解决什么问题？
4. 如果模型少返回一个必填字段，错误在哪里暴露？
5. 为什么不能把模型输出直接当成可信的业务对象？

## 9. Out of Scope

- Tool Calling
- RSS/Search 接入
- Agent Loop
- RAG、Memory、MCP
- Agent Framework

