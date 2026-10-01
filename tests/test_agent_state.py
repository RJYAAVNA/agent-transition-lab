from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agents.research_agent import AgentMaxStepsExceeded, ResearchAgent
from app.agents.runtime import AgentRuntime, ToolExecutor
from app.agents.state import AgentState, AgentStatus


FINAL_JSON = """
{
  "topic": "Agent state",
  "summary": "State tracks an observable agent run.",
  "signals": [{"title": "Signal", "description": "A signal."}],
  "opportunities": [{"title": "Opportunity", "description": "An opportunity."}],
  "risks": [{"title": "Risk", "description": "A risk."}],
  "evidence": [{"title": "Evidence", "source": "Test", "url": null, "excerpt": "Observed."}],
  "confidence": 0.8
}
""".strip()


def _message(content: str | None = None, tool_calls: list[object] | None = None) -> object:
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def _tool_call(name: str, query: str) -> object:
    return SimpleNamespace(
        id=f"call_{query}",
        type="function",
        function=SimpleNamespace(name=name, arguments=f'{{"query": "{query}"}}'),
    )


def _response(message: object) -> object:
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses

    def create(self, **_: object) -> object:
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


class FakeSearchTool:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str) -> list[dict[str, str]]:
        self.queries.append(query)
        return [{"title": f"Result for {query}", "source": "test"}]


class FakeRSSTool:
    def fetch(self) -> list[dict[str, str]]:
        return []


def _agent(
    responses: list[object],
    max_steps: int = 5,
    search_tool: FakeSearchTool | None = None,
) -> ResearchAgent:
    return ResearchAgent(
        client=FakeClient(responses),
        model="test-model",
        search_tool=search_tool or FakeSearchTool(),  # type: ignore[arg-type]
        rss_tool=FakeRSSTool(),  # type: ignore[arg-type]
        max_steps=max_steps,
    )


def test_agent_state_starts_pending_and_empty() -> None:
    state = AgentState(goal="Research agent state")

    assert state.goal == "Research agent state"
    assert state.current_step == 0
    assert state.status == AgentStatus.PENDING
    assert state.messages == []
    assert state.observations == []
    assert state.final_result is None


def test_runtime_accepts_state_as_first_argument() -> None:
    state = AgentState(goal="State-first runtime", messages=[{"role": "user", "content": "goal"}])
    runtime = AgentRuntime(tool_executor=ToolExecutor([]), max_steps=1)

    result = runtime.run(
        state,
        lambda messages: _response(_message(content=FINAL_JSON)),
        lambda content: ResearchAgent._parse_final_response(content),
    )

    assert result.state is state
    assert state.status == AgentStatus.COMPLETED
    assert state.current_step == 1


def test_state_records_single_tool_observation() -> None:
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", "one")])),
            _response(_message(content=FINAL_JSON)),
        ]
    )

    run = agent.research_with_trace("Research one")
    state = run.state

    assert state.goal == "Research one"
    assert state.current_step == 2
    assert state.status == AgentStatus.COMPLETED
    assert len(state.observations) == 1
    assert state.observations[0].ok is True
    assert state.observations[0].tool == "search_web"
    assert state.final_result is run.final_result
    assert state.messages[-1]["role"] == "tool"
    assert run.trace.total_steps == 2


def test_state_records_complete_multi_step_execution() -> None:
    search_tool = FakeSearchTool()
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", "first")])),
            _response(_message(tool_calls=[_tool_call("search_web", "second")])),
            _response(_message(content=FINAL_JSON)),
        ],
        search_tool=search_tool,
    )
    run = agent.research_with_trace("Research several steps")

    assert search_tool.queries == ["first", "second"]
    assert run.state.current_step == 3
    assert run.state.status == AgentStatus.COMPLETED
    assert len(run.state.observations) == 2
    assert [observation.arguments["query"] for observation in run.state.observations] == [
        "first",
        "second",
    ]
    assert run.state.final_result is run.final_result
    assert run.trace.total_steps == 3


def test_state_is_max_steps_without_a_final_result() -> None:
    agent = _agent(
        [
            _response(_message(tool_calls=[_tool_call("search_web", "one")])),
            _response(_message(tool_calls=[_tool_call("search_web", "two")])),
        ],
        max_steps=2,
    )

    with pytest.raises(AgentMaxStepsExceeded):
        agent.research("Research with a limit")

    assert agent.last_state is not None
    assert agent.last_state.current_step == 2
    assert agent.last_state.status == AgentStatus.MAX_STEPS
    assert agent.last_state.final_result is None
    assert len(agent.last_state.observations) == 2


def test_state_becomes_error_when_llm_call_fails() -> None:
    agent = _agent([])

    def fail_call(**_: object) -> object:
        raise RuntimeError("LLM unavailable")

    agent.client.chat.completions.create = fail_call  # type: ignore[method-assign]

    with pytest.raises(Exception, match="LLM API call failed"):
        agent.research("Research with an LLM failure")

    assert agent.last_state is not None
    assert agent.last_state.current_step == 1
    assert agent.last_state.status == AgentStatus.ERROR
    assert agent.last_state.final_result is None
