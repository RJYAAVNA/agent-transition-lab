from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.agents.research_agent import (
    AgentMaxStepsExceeded,
    AgentResponseError,
    ResearchAgent,
)
from app.tools.rss_tool import RSSItem
from app.tools.search_tool import SearchResult


FINAL_JSON = """
{
  "topic": "AI Agent engineering",
  "summary": "Agent engineering connects LLM decisions with real tools and structured output.",
  "signals": [{"title": "Tool calling is common", "description": "Teams are using LLMs to select tools and inspect observations."}],
  "opportunities": [{"title": "Backend integration", "description": "Backend engineers can apply API and service design skills to agent runtimes."}],
  "risks": [{"title": "Unbounded loops", "description": "Agents need iteration limits so they do not keep calling tools forever."}],
  "evidence": [{"title": "Test evidence", "source": "Test", "url": null, "excerpt": "Tool results were observed by the model."}],
  "confidence": 0.7
}
""".strip()


def _message(content: str | None = None, tool_calls: list[object] | None = None) -> object:
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def _tool_call(name: str, arguments: str = "{}") -> object:
    return SimpleNamespace(
        id=f"call_{name}",
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
        self.calls.append(deepcopy(kwargs))
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


class FakeSearchTool:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str) -> list[SearchResult]:
        self.queries.append(query)
        if query == "explode":
            raise RuntimeError("search provider timeout")
        return [
            SearchResult(
                title="Agent Runtime",
                url="https://example.com/agent-runtime",
                snippet="The runtime executes tool calls requested by the LLM.",
                source="FakeSearch",
            )
        ]


class FakeRSSTool:
    def __init__(self) -> None:
        self.fetch_count = 0

    def fetch(self) -> list[RSSItem]:
        self.fetch_count += 1
        return [
            RSSItem(
                title="Agent loop update",
                link="https://example.com/rss",
                summary="A feed item used as an agent observation.",
                published_at=datetime(2026, 9, 10, tzinfo=UTC),
                source="FakeRSS",
            )
        ]


def _agent(
    responses: list[object],
    search_tool: FakeSearchTool | None = None,
    rss_tool: FakeRSSTool | None = None,
    max_iterations: int = 5,
) -> ResearchAgent:
    return ResearchAgent(
        client=FakeClient(responses),
        model="test-model",
        search_tool=search_tool or FakeSearchTool(),  # type: ignore[arg-type]
        rss_tool=rss_tool or FakeRSSTool(),  # type: ignore[arg-type]
        max_iterations=max_iterations,
    )


def test_agent_returns_final_response_without_tool_call() -> None:
    agent = _agent([_response(_message(content=FINAL_JSON))])

    run = agent.research_with_trace("AI Agent engineering")
    result = run.final_result

    assert result.topic == "AI Agent engineering"
    assert result.confidence == 0.7
    assert run.trace.total_steps == 1
    assert run.trace.stop_reason == "completed"
    assert run.trace.steps[0].tool_calls == []
    assert agent.last_trace == run.trace
    call = agent.client.chat.completions.calls[0]
    tool_names = [tool["function"]["name"] for tool in call["tools"]]
    assert tool_names == ["search_web", "rss_feed"]


def test_agent_executes_search_tool_call() -> None:
    search_tool = FakeSearchTool()
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", '{"query": "agent loop"}')])),
            _response(_message(content=FINAL_JSON)),
        ],
        search_tool=search_tool,
    )

    run = agent.research_with_trace("AI Agent engineering")

    assert search_tool.queries == ["agent loop"]
    assert run.trace.total_steps == 2
    assert run.trace.steps[0].tool_calls == ["search_web"]
    assert run.trace.steps[0].calls[0].ok is True
    assert run.trace.steps[1].status == "completed"


def test_agent_executes_rss_tool_call() -> None:
    rss_tool = FakeRSSTool()
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("rss_feed")])),
            _response(_message(content=FINAL_JSON)),
        ],
        rss_tool=rss_tool,
    )

    run = agent.research_with_trace("AI Agent engineering")

    assert rss_tool.fetch_count == 1
    assert run.trace.steps[0].tool_calls == ["rss_feed"]


def test_agent_appends_tool_observation_to_messages() -> None:
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", '{"query": "agent loop"}')])),
            _response(_message(content=FINAL_JSON)),
        ]
    )

    agent.research("AI Agent engineering")

    second_call_messages = agent.client.chat.completions.calls[1]["messages"]
    tool_messages = [
        message for message in second_call_messages if message["role"] == "tool"
    ]
    assert tool_messages[0]["tool_call_id"] == "call_search_web"
    assert '"ok": true' in tool_messages[0]["content"]
    assert "Agent Runtime" in tool_messages[0]["content"]


def test_agent_runs_multiple_sequential_tool_steps() -> None:
    search_tool = FakeSearchTool()
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", '{"query": "first"}')])),
            _response(_message(tool_calls=[_tool_call("search_web", '{"query": "second"}')])),
            _response(_message(content=FINAL_JSON)),
        ],
        search_tool=search_tool,
    )

    run = agent.research_with_trace("AI Agent engineering")

    assert search_tool.queries == ["first", "second"]
    assert run.trace.total_steps == 3
    assert [step.tool_calls for step in run.trace.steps] == [
        ["search_web"],
        ["search_web"],
        [],
    ]


def test_agent_executes_multiple_tools_in_one_step() -> None:
    search_tool = FakeSearchTool()
    rss_tool = FakeRSSTool()
    agent = _agent(
        [
            _response(
                _message(
                    tool_calls=[
                        _tool_call("search_web", '{"query": "agent loop"}'),
                        _tool_call("rss_feed"),
                    ]
                )
            ),
            _response(_message(content=FINAL_JSON)),
        ],
        search_tool=search_tool,
        rss_tool=rss_tool,
    )

    run = agent.research_with_trace("AI Agent engineering")

    assert search_tool.queries == ["agent loop"]
    assert rss_tool.fetch_count == 1
    assert run.trace.steps[0].tool_calls == ["search_web", "rss_feed"]
    second_call_messages = agent.client.chat.completions.calls[1]["messages"]
    tool_messages = [
        message for message in second_call_messages if message["role"] == "tool"
    ]
    assert len(tool_messages) == 2


def test_agent_turns_tool_failure_into_observation() -> None:
    search_tool = FakeSearchTool()
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", '{"query": "explode"}')])),
            _response(_message(content=FINAL_JSON)),
        ],
        search_tool=search_tool,
    )

    run = agent.research_with_trace("AI Agent engineering")

    assert search_tool.queries == ["explode"]
    assert run.trace.stop_reason == "completed"
    assert run.trace.steps[0].calls[0].ok is False
    second_call_messages = agent.client.chat.completions.calls[1]["messages"]
    tool_messages = [
        message for message in second_call_messages if message["role"] == "tool"
    ]
    assert '"ok": false' in tool_messages[0]["content"]
    assert "search provider timeout" in tool_messages[0]["content"]


def test_agent_turns_unknown_tool_into_observation() -> None:
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("unknown_tool")])),
            _response(_message(content=FINAL_JSON)),
        ]
    )

    run = agent.research_with_trace("AI Agent engineering")

    assert run.trace.steps[0].tool_calls == ["unknown_tool"]
    assert run.trace.steps[0].calls[0].ok is False
    second_call_messages = agent.client.chat.completions.calls[1]["messages"]
    tool_messages = [
        message for message in second_call_messages if message["role"] == "tool"
    ]
    assert "not registered" in tool_messages[0]["content"]


def test_agent_turns_invalid_tool_arguments_into_observation() -> None:
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", "{invalid json")])),
            _response(_message(content=FINAL_JSON)),
        ]
    )

    run = agent.research_with_trace("AI Agent engineering")

    assert run.trace.steps[0].calls[0].ok is False
    second_call_messages = agent.client.chat.completions.calls[1]["messages"]
    tool_messages = [
        message for message in second_call_messages if message["role"] == "tool"
    ]
    assert "invalid JSON arguments" in tool_messages[0]["content"]


def test_agent_stops_at_max_iterations() -> None:
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("rss_feed")])),
            _response(_message(tool_calls=[_tool_call("rss_feed")])),
        ],
        max_iterations=2,
    )

    with pytest.raises(AgentMaxStepsExceeded) as exc_info:
        agent.research("AI Agent engineering")

    assert "max_steps=2" in str(exc_info.value)
    assert "executed_steps=2" in str(exc_info.value)
    assert agent.last_trace is not None
    assert agent.last_trace.stop_reason == "max_steps"


def test_agent_rejects_invalid_final_output() -> None:
    agent = _agent([_response(_message(content="not-json"))])

    with pytest.raises(AgentResponseError):
        agent.research("AI Agent engineering")

    assert agent.last_trace is not None
    assert agent.last_trace.stop_reason == "invalid_output"
    assert agent.last_trace.steps[0].status == "invalid_output"
