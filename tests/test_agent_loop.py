from types import SimpleNamespace

import pytest

from app.agent import (
    AgentMaxStepsExceeded,
    AgentResponseError,
    OpportunityResearchAgent,
)


def _message(content: str | None = None, tool_calls: list[object] | None = None) -> object:
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def _tool_call(name: str = "search_web", arguments: str = '{"query": "AI Agent Java"}') -> object:
    return SimpleNamespace(
        id="call_1",
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _response(message: object) -> object:
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


def test_agent_loop_runs_tool_then_returns_structured_response() -> None:
    final_json = """
{
  "topic": "AI Agent 对 Java 后端工程师未来职业机会的影响",
  "summary": "AI Agent 会提升 Java 后端工程师在工具集成、业务流程自动化和平台工程方向的机会。",
  "signals": [{"title": "Agent 架构进入业务系统", "description": "企业开始把 LLM 接入内部 API、搜索和工作流，后端工程师的系统集成能力更重要。"}],
  "opportunities": [{"title": "Agent 平台后端工程师", "description": "Java Spring 经验可以迁移到工具接口、权限、日志、队列和可靠性建设。"}],
  "risks": [{"title": "只会调用模型 API 不够", "description": "机会会偏向理解业务边界、数据质量和工程可靠性的人。"}],
  "evidence": [{"title": "Mock evidence", "source": "MockSearch", "url": null, "excerpt": "Backend engineers can transfer API and service boundary skills into LLM tool-calling systems."}],
  "confidence": 0.72
}
""".strip()
    client = FakeClient(
        [
            _response(_message(tool_calls=[_tool_call()])),
            _response(_message(content=final_json)),
        ]
    )
    agent = OpportunityResearchAgent(client=client, model="test-model", max_steps=3)

    result = agent.research("AI Agent 对 Java 后端工程师未来职业机会的影响")

    assert result.topic == "AI Agent 对 Java 后端工程师未来职业机会的影响"
    assert result.confidence == 0.72
    assert len(client.chat.completions.calls) == 2
    assert client.chat.completions.calls[0]["tools"][0]["function"]["name"] == "search_web"


def test_agent_rejects_invalid_final_json() -> None:
    client = FakeClient([_response(_message(content="not-json"))])
    agent = OpportunityResearchAgent(client=client, model="test-model")

    with pytest.raises(AgentResponseError):
        agent.research("AI Agent market")


def test_agent_stops_when_max_steps_is_exceeded() -> None:
    client = FakeClient([_response(_message(tool_calls=[_tool_call()]))])
    agent = OpportunityResearchAgent(client=client, model="test-model", max_steps=1)

    with pytest.raises(AgentMaxStepsExceeded):
        agent.research("AI Agent market")
