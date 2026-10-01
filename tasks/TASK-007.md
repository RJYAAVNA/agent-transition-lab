你现在开始执行 agent-transition-lab 的 TASK-007。
项目：
RJYAAVNA/agent-transition-lab
任务目标：
Day07 — Structured Agent State
核心目标：
把 Day06 中隐含在 messages、局部变量和 trace 中的 Agent 执行上下文，
升级成一个显式、可观察、可测试的 AgentState。
在开始修改代码前，必须先阅读：
1. docs/LEARNING_ROADMAP.md
2. docs/LEARNING_STATE.md
3. docs/AI_CONTEXT.md
4. docs/ARCHITECTURE.md
5. docs/DECISIONS.md
6. tasks/TASK-005.md
7. tasks/TASK-006.md
8. 当前 src/app/agents/runtime.py
9. 当前 src/app/agents/research_agent.py
10. 当前 Agent 相关测试
如果仓库中不存在 TASK-007.md，不要因此停止。
根据下面的任务定义执行。
========================
DAY07 TASK
核心概念：
Message History != Agent State
messages 主要表示：
“LLM 看到了什么上下文？”
AgentState 需要表示：
“Agent 当前执行到了哪里、获得了什么、处于什么状态、最终结果是什么？”
最小 State 至少包含：
- goal
- messages
- current_step
- observations
- status
- final_result
推荐新增：
src/app/agents/state.py
可以使用 dataclass 或 Pydantic。
不要过度设计。
========================
STATE SEMANTICS
Initial：
status = pending
current_step = 0
observations = []
final_result = None
开始运行：
status = running
每进入一个 Runtime step：
current_step 由 Runtime 控制
Tool 执行完成：
observation 写入 State
Final：
status = completed
final_result = ResearchResponse
Max Steps：
status = max_steps
final_result = None
如果存在 Runtime Error：
status 应能表达 error
具体 enum / string / model 形式可以根据当前代码风格决定。
========================
RUNTIME INTEGRATION
修改：
src/app/agents/runtime.py
目标：
AgentRuntime 不再只依赖 messages + 局部变量维护执行上下文。
应该形成：
ResearchAgent
    ↓
AgentState
    ↓
AgentRuntime
    ↓
LLM
    ↓
ToolExecutor
    ↓
Observation
    ↓
AgentState update
    ↓
next step
要求：
1. 每个 step 开始前 State 能表示当前 step。
2. Tool Observation 写入 State。
3. Final Result 写入 State。
4. State 能表达 completed / max_steps / error 等状态。
5. Execution Trace 必须继续保留。
6. ToolExecutor 必须继续保留。
7. 不要重写整个 Runtime。
8. 尽可能保持现有 API 兼容。
9. 先理解现有代码，再做最小修改。
========================
TESTING
新增 State 相关测试。
至少覆盖：
A. Initial State
验证：
- goal
- current_step
- status
- observations
- final_result
B. Single Tool
模拟：
Step 1 → Tool
验证：
- current_step
- observation
- status
C. Multi-step
模拟：
Step 1 → Tool
Step 2 → Tool
Step 3 → Final
验证 State 能表达完整执行过程。
D. Final
验证：
status == completed
final_result != None
E. Max Steps
验证：
status == max_steps
final_result is None
F. Regression
运行全部测试：
pytest
确保 Day01-Day06 测试没有回归。
========================
IMPORTANT DESIGN BOUNDARY
不要把以下内容放进 AgentState：
- hidden Chain-of-Thought
- API Key
- 原始敏感配置
- 不必要 Runtime 内部对象
- 数据库连接
- Tool 实例本身
State 表示：
可观察、可测试、可恢复的 Agent Execution State。
========================
OUT OF SCOPE
本 TASK 禁止主动引入：
- LangChain
- LangGraph
- MCP
- RAG
- Memory
- Multi-Agent
- Database
- Redis
- Vector Database
- Checkpoint Persistence
- Retry Framework
- Observability Platform
- Frontend
- Async Worker
今天只解决：
“State 是什么，以及 State 如何驱动 Agent Runtime。”
========================
IMPLEMENTATION PROCESS
开始修改前：
先输出一个 5~10 行的实施计划。
然后：
1. 检查当前代码是否已经存在部分 State 实现。
2. 如果存在，不重复造轮子。
3. 创建/完善 AgentState。
4. 最小化改造 AgentRuntime。
5. 让 ResearchAgent 正确创建并传递 State。
6. 增加测试。
7. 运行完整 pytest。
8. 修复回归。
9. 更新 docs/LEARNING_STATE.md。
10. 更新 docs/AI_CONTEXT.md。
11. 如有必要更新 docs/ARCHITECTURE.md。
12. 如有重要设计取舍，追加 docs/DECISIONS.md。
13. 不自动开始 TASK-008。
========================
FINAL OUTPUT
最终严格输出：
TASK-007 Result
Changed Files
...
State Model
...
Runtime Changes
...
Tests
...
Key Design Decisions
...
What I Should Study
...
Questions For Me
Q1...
Q2...
Q3...
Q4...
Q5...
不要替我回答 Questions For Me。
========================
IMPORTANT
这是学习项目。
不要为了“代码看起来更完整”而增加抽象。
优先：
简单
显式
可测试
可理解
而不是：
复杂
通用
企业级
过度抽象