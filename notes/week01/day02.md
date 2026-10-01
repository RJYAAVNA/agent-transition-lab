# Day02 - Tool Calling Foundation

## 今日目标

理解模型如何请求应用能力，以及应用如何执行这个请求：

```text
用户目标
  ->
LLM + Tool Schema
  ->
tool_call
  ->
Tool Registry / Dispatcher
  ->
Python Tool
  ->
Tool Observation
  ->
LLM
```

## 三个容易混淆的对象

### Tool Implementation

真实可执行的 Python 代码，例如 `search_web(query)`。它可以访问搜索服务，也可以在测试中由 fake tool 替代。

### Tool Schema

提供给 LLM 的名称、描述和参数结构。Schema 只描述“有哪些能力”和“如何请求”，不会自己执行 Python 函数。

### Tool Call

模型输出的结构化动作请求，例如：

```json
{
  "name": "search_web",
  "arguments": {
    "query": "AI Agent Java backend"
  }
}
```

这个对象仍然只是数据。应用必须解析、校验、查找工具并执行。

## 当前代码对应关系

- `src/app/agent.py` 定义 `SEARCH_WEB_TOOL_SCHEMA`。
- `src/app/tools/__init__.py` 定义 legacy `TOOL_REGISTRY` 和 `execute_tool()`。
- `tests/test_agent_loop.py` 验证 tool call、tool result 回填和最终结果。
- `tests/test_tools.py` 验证未知工具、非法 JSON 和注册工具执行。

Day05/Day06 后来增加了 `ToolExecutor`，但 Day02 的 dispatcher 仍然适合作为最小实现来阅读。

## messages 如何形成状态

模型请求工具时，Agent 需要保留 assistant 的 tool call，再追加：

```python
{
    "role": "tool",
    "tool_call_id": "...",
    "content": "serialized result"
}
```

下一轮 LLM 读取的上下文才包含：

- 用户想做什么。
- 模型上一轮选择了哪个工具。
- 工具真实返回了什么。

## 与普通函数调用的区别

普通函数调用由代码直接决定函数和参数。Tool Calling 中，模型先输出一个动作请求，应用再决定是否接受、如何校验和如何执行。模型不能越过应用的执行边界直接调用 Python。

## 已有代码实践

- 一个最小 Tool Schema。
- Tool name 到 Python function 的 registry 映射。
- 参数 JSON 解析。
- 工具结果 JSON 序列化。
- `max_steps` 防止工具调用循环没有边界。

## 尚未确认的理解

- Tool Schema、Tool Call、Tool Result 三者在一次请求中的先后关系。
- 为什么 tool result 必须带 `tool_call_id`。
- dispatcher 与 Agent 主循环为什么应该分开。

## Day02 验收问题

1. LLM 为什么不能直接执行 `search_web(query)`？
2. `tool_call.name` 如何找到真实 Python 工具？
3. assistant tool call message 和 tool message 的区别是什么？
4. 不回填 tool result 会造成什么问题？

