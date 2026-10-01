from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from pydantic import BaseModel, ValidationError

from app.agents.state import AgentState, AgentStatus


DEFAULT_MAX_STEPS = 5


class AgentError(Exception):
    """Base exception for agent runtime failures."""


class AgentLLMError(AgentError):
    """Raised when the LLM call fails or returns an unusable envelope."""


class AgentResponseError(AgentError):
    """Raised when the final LLM response cannot become the expected schema."""


class AgentMaxStepsExceeded(AgentError):
    """Raised when the agent reaches its loop safety limit."""


class AgentRuntimeError(AgentError):
    """Raised when the runtime cannot interpret the model response shape."""


@dataclass
class ToolSpec:
    name: str
    func: Callable[[dict[str, Any]], Any]
    arguments_model: type[BaseModel] | None = None


@dataclass
class ToolObservation:
    ok: bool
    tool: str
    result: Any | None = None
    error: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_message_content(self) -> str:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "tool": self.tool,
        }
        if self.ok:
            payload["result"] = self.result
        else:
            payload["error"] = self.error or "tool execution failed"
        return json.dumps(payload, ensure_ascii=False)


@dataclass
class ToolCallTrace:
    tool: str
    arguments: dict[str, Any]
    ok: bool
    error: str | None = None


@dataclass
class AgentStepTrace:
    step: int
    tool_calls: list[str]
    tool_results: list[str]
    status: str
    duration_ms: float
    calls: list[ToolCallTrace] = field(default_factory=list)


@dataclass
class AgentRunTrace:
    steps: list[AgentStepTrace] = field(default_factory=list)
    total_steps: int = 0
    stop_reason: str = "runtime_error"

    def last_status_summary(self) -> str:
        if not self.steps:
            return "no steps executed"

        last_step = self.steps[-1]
        if not last_step.tool_calls:
            return f"step={last_step.step} status={last_step.status} tool_calls=[]"

        tool_summary = ", ".join(
            f"{call.tool}:{'ok' if call.ok else 'error'}" for call in last_step.calls
        )
        return (
            f"step={last_step.step} status={last_step.status} "
            f"tool_calls=[{tool_summary}]"
        )


@dataclass
class AgentRunResult:
    final_result: Any
    trace: AgentRunTrace
    state: AgentState


class ToolExecutor:
    """Execute registered tools and convert failures into observations."""

    def __init__(self, tools: list[ToolSpec]) -> None:
        self._registry = {tool.name: tool for tool in tools}

    def execute_tool(self, name: str, raw_arguments: str) -> ToolObservation:
        tool = self._registry.get(name)
        if tool is None:
            return ToolObservation(
                ok=False,
                tool=name,
                error=f"Tool {name!r} is not registered.",
            )

        arguments = self._parse_arguments(name, raw_arguments, tool.arguments_model)
        if isinstance(arguments, ToolObservation):
            return arguments

        try:
            result = tool.func(arguments)
        except Exception as exc:
            return ToolObservation(
                ok=False,
                tool=name,
                arguments=arguments,
                error=f"Tool {name!r} failed: {exc}",
            )

        return ToolObservation(
            ok=True,
            tool=name,
            arguments=arguments,
            result=self._to_jsonable(result),
        )

    @staticmethod
    def _parse_arguments(
        name: str,
        raw_arguments: str,
        arguments_model: type[BaseModel] | None,
    ) -> dict[str, Any] | ToolObservation:
        try:
            payload = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError:
            return ToolObservation(
                ok=False,
                tool=name,
                error=f"Tool {name!r} received invalid JSON arguments.",
            )

        if not isinstance(payload, dict):
            return ToolObservation(
                ok=False,
                tool=name,
                error=f"Tool {name!r} arguments must be a JSON object.",
            )

        if arguments_model is None:
            return payload

        try:
            return arguments_model.model_validate(payload).model_dump()
        except ValidationError:
            return ToolObservation(
                ok=False,
                tool=name,
                error=f"Tool {name!r} arguments do not match its schema.",
            )

    @classmethod
    def _to_jsonable(cls, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, list):
            return [cls._to_jsonable(item) for item in value]
        if isinstance(value, dict):
            return {key: cls._to_jsonable(item) for key, item in value.items()}
        return value


class AgentRuntime:
    """Small, explicit Agent Loop with max-step safety and execution trace."""

    def __init__(self, tool_executor: ToolExecutor, max_steps: int = DEFAULT_MAX_STEPS) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1.")
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.last_trace: AgentRunTrace | None = None
        self.last_state: AgentState | None = None

    def run(
        self,
        messages: list[dict[str, Any]] | AgentState | None = None,
        call_llm: Callable[[list[dict[str, Any]]], Any] | None = None,
        parse_final_response: Callable[[str], Any] | None = None,
        *,
        state: AgentState | None = None,
    ) -> AgentRunResult:
        if isinstance(messages, AgentState):
            if state is not None:
                raise ValueError("Provide AgentState either positionally or by keyword.")
            state = messages
            messages = None

        if call_llm is None or parse_final_response is None:
            raise ValueError("call_llm and parse_final_response are required.")

        if state is None:
            if messages is None:
                raise ValueError("messages or state is required.")
            state = AgentState(goal="", messages=messages)
        elif messages is not None and not state.messages:
            state.messages = messages

        self.last_state = state
        state.status = AgentStatus.RUNNING
        state.current_step = 0
        state.final_result = None
        trace = AgentRunTrace()

        try:
            for step in range(1, self.max_steps + 1):
                state.current_step = step
                started_at = perf_counter()

                # 1. Ask the LLM what to do next.
                response = call_llm(state.messages)
                message = self._extract_message(response)

                # 2. Inspect requested tool calls.
                tool_calls = getattr(message, "tool_calls", None)
                if not tool_calls:
                    final_content = getattr(message, "content", None) or ""
                    try:
                        final_result = parse_final_response(final_content)
                    except AgentResponseError:
                        trace.steps.append(
                            AgentStepTrace(
                                step=step,
                                tool_calls=[],
                                tool_results=[],
                                status="invalid_output",
                                duration_ms=self._elapsed_ms(started_at),
                            )
                        )
                        trace.total_steps = step
                        trace.stop_reason = "invalid_output"
                        self.last_trace = trace
                        raise

                    state.status = AgentStatus.COMPLETED
                    state.final_result = final_result
                    trace.steps.append(
                        AgentStepTrace(
                            step=step,
                            tool_calls=[],
                            tool_results=[],
                            status="completed",
                            duration_ms=self._elapsed_ms(started_at),
                        )
                    )
                    trace.total_steps = step
                    trace.stop_reason = "completed"
                    self.last_trace = trace
                    return AgentRunResult(
                        final_result=final_result,
                        trace=trace,
                        state=state,
                    )

                state.messages.append(self._assistant_message_with_tool_calls(message))

                step_trace = AgentStepTrace(
                    step=step,
                    tool_calls=[],
                    tool_results=[],
                    status="tool_called",
                    duration_ms=0.0,
                )

                # 3. Execute all tools requested by the model, sequentially.
                for tool_call in tool_calls:
                    tool_name, raw_arguments, tool_call_id = self._extract_tool_call(tool_call)
                    observation = self.tool_executor.execute_tool(tool_name, raw_arguments)
                    state.observations.append(observation)
                    serialized_observation = observation.to_message_content()

                    step_trace.tool_calls.append(tool_name)
                    step_trace.tool_results.append(serialized_observation)
                    step_trace.calls.append(
                        ToolCallTrace(
                            tool=tool_name,
                            arguments=observation.arguments,
                            ok=observation.ok,
                            error=observation.error,
                        )
                    )

                    # 4. Append the observable tool result to the LLM context.
                    state.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": serialized_observation,
                        }
                    )

                step_trace.duration_ms = self._elapsed_ms(started_at)
                trace.steps.append(step_trace)

                # 5. Continue the loop so the LLM can decide again.

            state.status = AgentStatus.MAX_STEPS
            state.final_result = None
            trace.total_steps = self.max_steps
            trace.stop_reason = "max_steps"
            self.last_trace = trace
            raise AgentMaxStepsExceeded(
                "Agent reached max_steps="
                f"{self.max_steps}; executed_steps={trace.total_steps}; "
                f"last_status={trace.last_status_summary()}"
            )
        except AgentMaxStepsExceeded:
            state.status = AgentStatus.MAX_STEPS
            state.final_result = None
            self.last_trace = trace
            self.last_state = state
            raise
        except Exception:
            state.status = AgentStatus.ERROR
            state.final_result = None
            trace.total_steps = len(trace.steps)
            self.last_trace = trace
            self.last_state = state
            raise

    @staticmethod
    def _extract_message(response: Any) -> Any:
        try:
            return response.choices[0].message
        except (AttributeError, IndexError) as exc:
            raise AgentLLMError("LLM response did not contain a message.") from exc

    @staticmethod
    def _extract_tool_call(tool_call: Any) -> tuple[str, str, str]:
        try:
            return (
                tool_call.function.name,
                tool_call.function.arguments or "{}",
                tool_call.id,
            )
        except AttributeError as exc:
            raise AgentRuntimeError("LLM tool call shape is invalid.") from exc

    @staticmethod
    def _assistant_message_with_tool_calls(message: Any) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": getattr(message, "content", None),
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in message.tool_calls
            ],
        }

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return round((perf_counter() - started_at) * 1000, 3)
