# Day01 - LLM Minimum Loop

## 今日目标

先建立 LLM 应用最小调用链，不急着引入 Agent Framework：

```text
用户输入
  ->
messages
  ->
LLM
  ->
JSON 文本
  ->
Pydantic 校验
  ->
结构化研究结果
```

## 代码对应关系

- `ResearchRequest.topic` 是 HTTP 输入进入应用的边界。
- `messages` 携带 system message 和 user message。
- OpenAI-compatible client 的 `chat.completions.create()` 发起模型请求。
- `message.content` 是模型返回的文本。
- `json.loads()` 负责把文本解析为 Python 数据。
- `ResearchResponse.model_validate()` 负责把不可信的模型输出转换为业务模型。

当前代码后来已经演进到 Tool Calling，因此 `src/app/agent.py` 中还能看到更多逻辑。阅读 Day01 时只抽出“输入、LLM、结构化输出”这条主线。

## 关键理解

### 1. Prompt 和 Message

Prompt 的内容最终要进入 messages。system message 约束角色和输出要求，user message 携带具体研究目标。LLM 并不会直接读取 Python 变量，应用必须先把变量组织成请求消息。

### 2. JSON 不等于结构化结果

JSON 只是模型生成的文本格式。只有经过解析和 schema 校验后，应用才得到可以继续传递的 `ResearchResponse`。

### 3. 模型输出是不可信输入

模型可能缺字段、返回错误类型、输出非法 JSON 或违反业务约束。Pydantic 模型是应用与模型之间的校验边界。

## 调用链练习

```text
ResearchRequest(topic)
  ->
Agent messages
  ->
LLM response
  ->
parse_opportunity_report()
  ->
ResearchResponse
```

## 已有代码实践

- 使用环境变量配置 provider、model 和 API key。
- 使用 fake client 测试 Agent，不让测试依赖真实付费 API。
- 对 LLM 调用错误、非法 JSON 和 schema 校验错误使用独立错误路径。

## 尚未确认的理解

以下内容需要学习者自己用话解释，不能只根据代码存在就标记为掌握：

- 为什么 system message 和 user message 要分开。
- `json.loads()` 与 `ResearchResponse.model_validate()` 的边界。
- 结构化输出失败时，错误应该在哪一层处理。

## Day01 验收问题

1. 用户输入在哪里进入系统？
2. LLM 请求具体在哪一行发起？
3. 模型结果怎样成为 `ResearchResponse`？
4. 为什么不能直接相信模型返回的 JSON？

