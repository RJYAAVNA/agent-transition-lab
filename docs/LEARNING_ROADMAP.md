# Agent Engineer Transition Roadmap

## 1. Goal

在约 3 个月内，从当前 Java Backend Engineer 能力基础，转向具备实际项目开发与面试能力的：

**Agent / LLM Application Engineer**

本路线不以训练模型、算法研究或深度学习理论为主要目标，而以：

* LLM Application
* Agent Engineering
* RAG
* Tool Calling
* Workflow
* MCP
* Memory
* Evaluation
* Observability
* Engineering
* Deployment

为核心。

Java 不放弃，Python 作为 Agent/LLM 主开发语言进行补充。

---

# 2. Learning Principles

整个学习过程遵循：

## 2.1 Project Driven

所有核心知识尽量进入主项目：

**Opportunity Research Agent**

避免长期停留在脱离项目的 Demo。

---

## 2.2 Just Enough Learning

只学习当前项目马上需要的知识。

避免：

* 为学 Python 而系统学习整本 Python
* 为学 Agent 而提前研究所有框架
* 为“最佳实践”增加当前不需要的抽象

遵循：

* YAGNI
* KISS
* Learning by Building

---

## 2.3 Understand Before Expanding

一个模块只有满足：

1. 能解释为什么存在
2. 能解释调用链
3. 能解释输入输出
4. 能理解主要代码
5. 能解释异常情况下发生什么

之后，才进入下一层。

“Codex 已经写出来”不等于“已经掌握”。

---

# 3. Main Project

## Opportunity Research Agent

长期目标：

用户提出一个研究目标后，Agent 能够：

```text
User Goal
    ↓
Planning
    ↓
Tool Selection
    ↓
Information Retrieval
    ↓
Evidence Normalization
    ↓
Analysis
    ↓
Structured Result
```

后续逐步增加：

```text
RAG
Memory
MCP
Workflow
Evaluation
Observability
Deployment
```

最终可与 OpenRadar 项目产生结合。

---

# 4. Phase 1 — Agent Foundation

## Week 1–2

### Goal

建立 Agent 最核心的工程认知：

```text
LLM
Tool
Service
Workflow
Structured Output
Error Handling
```

暂时不引入复杂 Agent Framework。

---

## Day 1 — LLM Minimum Loop

### Learning Goal

理解：

* Python Agent 项目基本结构
* LLM API 调用
* Prompt / Message
* Structured Output
* 用户输入如何进入 LLM

### Practice

完成：

```text
User Input
    ↓
LLM
    ↓
Structured Result
```

### Acceptance

能够独立解释：

* 输入在哪里进入系统
* LLM 在哪里调用
* 返回结果如何转换
* 为什么使用结构化输出

---

## Day 2 — Tool Calling Foundation

### Learning Goal

理解：

* Tool 是什么
* Tool schema
* LLM 为什么可以调用 Tool
* Tool 与普通函数的区别
* Tool Calling 基本协议

### Practice

完成最小 Tool Calling。

### Acceptance

能够解释：

```text
User
 ↓
LLM
 ↓
Tool Call
 ↓
Application
 ↓
Tool Result
 ↓
LLM
```

---

## Day 3 — Real Tool Integration

### Learning Goal

理解：

* Agent Tool 和外部数据源之间的关系
* Source-driven Tool
* Query-driven Tool
* External API Adapter

### Practice

接入真实：

* RSS
* Search

形成多个 Tool。

### Key Concepts

RSS：

```text
Source Driven
```

Search：

```text
Query Driven
```

---

## Day 4 — Layering & Domain Model

### Learning Goal

理解：

* Tool
* Service
* Client
* DTO
* Domain Model
* Dependency Injection
* Exception Boundary

### Practice

理解并实现：

```text
Third Party JSON
        ↓
SearchResult
        ↓
Evidence
```

理解：

第三方数据模型与 Agent 内部业务模型不能完全耦合。

### Acceptance

能够解释：

* 为什么有 SearchResult
* 为什么还需要 Evidence
* Tool 与 Service 的职责
* Tool 异常与 Service 异常边界

---

## Day 5 — Research Workflow

### Learning Goal

第一次建立真正的业务编排层。

理解：

* Workflow
* Orchestration
* Use Case Boundary
* Step
* Execution Flow

### Practice

实现：

```text
Input
 ↓
Plan
 ↓
Tool
 ↓
Analyze
 ↓
Output
```

当前阶段使用确定性 Workflow。

暂时不引入：

* LLM 自动 Tool Selection
* LangGraph
* RAG
* Memory
* MCP
* Multi-Agent

### Acceptance

能够解释：

为什么：

```text
Service ≠ Workflow
Tool ≠ Workflow
```

以及 Workflow 为什么负责多个能力之间的编排。

---

## Day 6–10 — Agent Core Loop

具体 Daily Task 根据实际学习状态动态生成。

本阶段需要依次掌握：

### Agent Loop

理解：

```text
Goal
 ↓
Think / Decide
 ↓
Act
 ↓
Observe
 ↓
Continue / Finish
```

### Tool Selection

从：

```text
代码决定调用哪个 Tool
```

逐步过渡到：

```text
LLM 根据 Tool 描述选择能力
```

### Structured Agent State

理解 Agent 执行过程中：

* Input
* State
* Evidence
* Intermediate Result
* Final Result

之间的关系。

### Failure Handling

理解：

* Tool failure
* timeout
* retry
* fallback
* partial result

注意：

本阶段重点是自己理解 Agent Loop。

不要急于通过 LangGraph 隐藏这些机制。

---

# 5. Phase 2 — RAG

## Week 3–4

### Goal

让 Agent 从：

```text
只获取实时外部信息
```

发展到：

```text
能够获取并使用私有知识
```

---

## Core Topics

### Documents

理解：

* Document
* Metadata
* Chunk

---

### Chunking

掌握：

* Fixed Size
* Recursive Split
* Semantic Boundary

重点理解：

为什么 chunk 策略会影响 retrieval。

---

### Embedding

理解：

```text
Text
 ↓
Embedding Model
 ↓
Vector
```

不要求深入神经网络数学。

---

### Vector Database

理解：

* Vector
* Similarity
* Top-K
* Metadata Filter

---

### Retrieval

理解：

```text
Query
 ↓
Embedding
 ↓
Search
 ↓
Relevant Chunks
```

---

### Complete RAG

实现：

```text
Question
 ↓
Retrieve
 ↓
Context
 ↓
LLM
 ↓
Answer
```

---

### RAG Quality

开始理解：

* Recall
* Precision
* Chunk Quality
* Retrieval Quality
* Hallucination

---

## Project Deliverable

Opportunity Research Agent 增加 Knowledge Tool：

```text
ResearchWorkflow
      │
      ├── SearchTool
      ├── RSSTool
      └── KnowledgeTool
```

---

## Acceptance

能够从零解释：

```text
为什么需要 Embedding
为什么需要 Chunk
为什么需要 Retrieval
为什么不是把整个文档直接给 LLM
```

并能够独立实现基础 RAG。

---

# 6. Phase 3 — Workflow & LangGraph

## Week 5–6

### Goal

在已经理解手工 Agent Loop 后，再学习 Agent Workflow Framework。

重点：

**LangGraph**

而不是大量横向学习框架。

---

## Core Topics

### State

理解：

Agent State 是什么。

---

### Node

一个 Node 应该承担什么职责。

---

### Edge

理解：

* Fixed Edge
* Conditional Edge

---

### Graph

把之前自己实现的：

```text
Plan
 ↓
Search
 ↓
Analyze
 ↓
Output
```

迁移为 Graph。

---

### Conditional Routing

例如：

```text
Need Web?
 ├─ Yes → Search
 └─ No
```

以及：

```text
Enough Evidence?
 ├─ Yes → Analyze
 └─ No  → Search Again
```

---

### Human In The Loop

理解需要人工确认的 Agent Workflow。

---

## Project Deliverable

Opportunity Research Agent Workflow Graph。

目标：

```text
START
 ↓
PLAN
 ↓
ROUTE
 ├── RSS
 ├── SEARCH
 └── RAG
 ↓
EVALUATE EVIDENCE
 ↓
ANALYZE
 ↓
OUTPUT
 ↓
END
```

---

## Acceptance

能够解释：

为什么需要 LangGraph，而不是：

“因为 Agent 项目都在用 LangGraph。”

---

# 7. Phase 4 — MCP & Tool System

## Week 7–8

### Goal

从“项目内部 Tool”进一步理解标准化 Agent Tool Protocol。

---

## Core Topics

### MCP Fundamentals

理解：

* MCP Host
* MCP Client
* MCP Server
* Tool
* Resource
* Prompt

---

### Compare

能够解释：

```text
普通 Function
vs
Tool Calling
vs
MCP Tool
```

---

### MCP Server

自己实现至少一个 MCP Server。

例如：

```text
OpenRadar MCP Server
```

暴露：

* Search
* RSS
* Opportunity

等能力。

---

### MCP Client

Agent 通过 MCP 使用外部能力。

---

## Project Deliverable

将至少一个原有 Tool：

```text
Internal Tool
```

改造成：

```text
MCP Tool
```

理解这种变化解决了什么工程问题。

---

# 8. Phase 5 — Memory / Reliability / Evaluation

## Week 9–10

### Goal

从：

```text
Agent 可以运行
```

进入：

```text
Agent 可以可靠运行
```

这是 Agent Engineer 和 Demo Developer 的重要分界线。

---

# Memory

理解不同 Memory：

* Conversation Memory
* Working Memory
* Long-term Memory
* User Memory

重点理解：

Memory ≠ 简单保存所有历史对话。

---

# Reliability

掌握：

* Timeout
* Retry
* Fallback
* Idempotency
* Rate Limit
* Partial Failure

---

# Evaluation

理解 Agent Evaluation。

建立基础测试集：

```text
Input
Expected Behavior
Actual Behavior
Score
```

评估：

* Tool Selection
* Retrieval
* Answer Quality
* Evidence Quality

---

# Observability

理解：

一次 Agent Run 需要观察：

```text
Trace
Step
Tool Call
Latency
Token
Error
Cost
```

---

## Project Deliverable

Opportunity Research Agent 增加：

```text
Evaluation
Tracing
Logging
Failure Handling
```

能够观察完整 Agent Execution。

---

# 9. Phase 6 — Production & Interview

## Week 11–12

### Goal

将学习项目转变为：

**可以展示、部署、写进简历、用于面试的 Agent 项目。**

---

# Deployment

掌握：

* Environment Variables
* Docker
* API Deployment
* Logging
* Health Check
* Basic Security

完成线上部署。

---

# Architecture Review

能够完整解释：

```text
API
 ↓
Application
 ↓
Workflow
 ↓
Agent
 ↓
Tools
 ├── Search
 ├── RSS
 ├── RAG
 └── MCP
 ↓
External Systems
```

---

# Java Integration

利用已有 Java Backend 优势。

理解：

* Java Business Service
* Python Agent Service
* HTTP / RPC Boundary
* Existing Enterprise System Integration

目标不是放弃 Java，而是形成：

```text
Java Engineering
+
Python Agent Engineering
```

差异化能力。

---

# Interview Preparation

准备以下主题：

### LLM

* Token
* Context Window
* Temperature
* Structured Output

### Agent

* Tool Calling
* Agent Loop
* Planning
* Workflow
* Memory

### RAG

* Chunking
* Embedding
* Retrieval
* Reranking
* Evaluation

### MCP

* Architecture
* Tool
* Resource
* Protocol

### Engineering

* Reliability
* Evaluation
* Observability
* Deployment

---

# Project Story

能够在面试中完整描述：

1. 为什么做 Opportunity Research Agent
2. 第一版是什么
3. 遇到什么问题
4. 为什么引入 Tool
5. 为什么设计 Evidence
6. 为什么增加 Workflow
7. 为什么增加 RAG
8. 为什么使用 LangGraph
9. 为什么引入 MCP
10. 如何做 Evaluation
11. 如何处理失败
12. 如何部署

重点不是：

“我用了哪些框架。”

重点是：

“系统为什么一步步演进成现在这样。”

---

# 10. Capability Levels

所有能力统一使用：

## 未学习

尚未系统接触。

## 学习中

正在学习，但不能独立解释或实现。

## 基本掌握

能够：

* 解释原理
* 阅读代码
* 修改代码
* 在提示下实现

## 可独立实现

能够：

* 自己设计
* 自己实现
* 自己排查问题
* 解释设计取舍

---

# 11. Daily Execution Rule

Roadmap 不直接等于每日 Codex Task。

每天开始时：

```text
LEARNING_ROADMAP
        +
LEARNING_STATE
        +
昨天完成情况
        ↓
ChatGPT
        ↓
Today's Learning Goal
        ↓
TASK-XXX.md
        ↓
Codex
```

原因：

Roadmap 是长期规划。

TASK 是根据实际学习状态动态产生的最小执行单元。

---

# 12. Current Status

当前已完成：

```text
Day 1
Day 2
Day 3
Day 4
```

目前进入：

```text
Day 5 — Research Workflow
```

当前重点：

```text
Input
 ↓
Plan
 ↓
Tool
 ↓
Analyze
 ↓
Output
```

现阶段继续坚持：

**先理解 Agent 的底层工程机制，再逐渐引入框架。**
