from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from app.agents.runtime import (
    DEFAULT_MAX_STEPS,
    AgentError,
    AgentLLMError,
    AgentMaxStepsExceeded,
    AgentResponseError,
    AgentRunResult,
    AgentRunTrace,
    AgentRuntime,
    ToolExecutor,
    ToolSpec,
)
from app.core.config import settings
from app.schemas.research import ResearchResponse
from app.tools.rss_tool import RSSFeedTool
from app.tools.search_tool import SearchTool


logger = logging.getLogger(__name__)

DEFAULT_MAX_ITERATIONS = DEFAULT_MAX_STEPS
PLACEHOLDER_KEYS = {"", "your_openai_api_key_here", "your_deepseek_api_key_here"}


SEARCH_WEB_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search external information for the given query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The concrete search query.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

RSS_FEED_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "rss_feed",
        "description": "Fetch recent items from the configured RSS or Atom feed.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}

TOOL_SCHEMAS = [SEARCH_WEB_TOOL_SCHEMA, RSS_FEED_TOOL_SCHEMA]


class SearchWebArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RSSFeedArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentConfigError(AgentError):
    """Raised when required LLM configuration is missing or invalid."""


class AgentInvalidToolArgumentsError(AgentError):
    """Backward-compatible name from TASK-005.

    TASK-006 converts invalid tool arguments into tool observations instead of
    raising this error from the main loop.
    """


class AgentUnknownToolError(AgentError):
    """Backward-compatible name from TASK-005.

    TASK-006 converts unknown tools into tool observations instead of raising
    this error from the main loop.
    """


class AgentToolExecutionError(AgentError):
    """Backward-compatible name from TASK-005.

    TASK-006 converts tool execution failures into observations instead of
    raising this error from the main loop.
    """


AgentMaxIterationsError = AgentMaxStepsExceeded


class ResearchAgent:
    def __init__(
        self,
        client: Any | None = None,
        model: str | None = None,
        search_tool: SearchTool | None = None,
        rss_tool: RSSFeedTool | None = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        max_steps: int | None = None,
    ) -> None:
        self.max_steps = max_steps if max_steps is not None else max_iterations
        self.search_tool = search_tool or SearchTool()
        self.rss_tool = rss_tool or RSSFeedTool()
        self.tool_executor = ToolExecutor(
            [
                ToolSpec(
                    name="search_web",
                    func=self._execute_search_web,
                    arguments_model=SearchWebArguments,
                ),
                ToolSpec(
                    name="rss_feed",
                    func=self._execute_rss_feed,
                    arguments_model=RSSFeedArguments,
                ),
            ]
        )
        self.runtime = AgentRuntime(
            tool_executor=self.tool_executor,
            max_steps=self.max_steps,
        )
        self.last_trace: AgentRunTrace | None = None

        if client is not None:
            self.client = client
            self.model = model or "test-model"
            return

        self.client, default_model = self._build_openai_client()
        self.model = model or default_model

    def research(self, goal: str) -> ResearchResponse:
        result = self.research_with_trace(goal)
        return result.final_result

    def research_with_trace(self, goal: str) -> AgentRunResult:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": f"Research goal: {goal}"},
        ]

        try:
            result = self.runtime.run(
                messages=messages,
                call_llm=self._call_llm,
                parse_final_response=self._parse_final_response,
            )
        finally:
            self.last_trace = self.runtime.last_trace

        return result

    def _execute_search_web(self, arguments: dict[str, Any]) -> Any:
        return self.search_tool.search(arguments["query"])

    def _execute_rss_feed(self, arguments: dict[str, Any]) -> Any:
        return self.rss_tool.fetch()

    def _call_llm(self, messages: list[dict[str, Any]]) -> Any:
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except OpenAIError as exc:
            raise AgentLLMError("LLM API call failed.") from exc
        except Exception as exc:
            raise AgentLLMError("LLM API call failed.") from exc

    @staticmethod
    def _parse_final_response(content: str) -> ResearchResponse:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AgentResponseError("Final LLM response is not valid JSON.") from exc

        try:
            return ResearchResponse.model_validate(payload)
        except ValidationError as exc:
            raise AgentResponseError(
                "Final LLM response does not match ResearchResponse."
            ) from exc

    def _build_openai_client(self) -> tuple[OpenAI, str]:
        provider = settings.llm_provider.lower().strip()

        if provider == "openai":
            api_key = settings.openai_api_key
            if api_key in PLACEHOLDER_KEYS or api_key is None:
                raise AgentConfigError("OPENAI_API_KEY is missing.")
            return OpenAI(api_key=api_key), settings.openai_model

        if provider == "deepseek":
            api_key = settings.deepseek_api_key
            if api_key in PLACEHOLDER_KEYS or api_key is None:
                raise AgentConfigError("DEEPSEEK_API_KEY is missing.")
            return (
                OpenAI(api_key=api_key, base_url=settings.deepseek_base_url),
                settings.deepseek_model,
            )

        raise AgentConfigError(f"Unsupported LLM_PROVIDER={settings.llm_provider!r}.")

    @staticmethod
    def _system_prompt() -> str:
        return """
You are a minimal opportunity research agent.

You can decide whether to call tools. If you call a tool, wait for the tool
observation before deciding whether to call another tool or finish.

Return final output as JSON only. It must match this schema:
{
  "topic": "string",
  "summary": "string",
  "signals": [{"title": "string", "description": "string"}],
  "opportunities": [{"title": "string", "description": "string"}],
  "risks": [{"title": "string", "description": "string"}],
  "evidence": [
    {
      "title": "string",
      "source": "string",
      "url": null,
      "excerpt": "string"
    }
  ],
  "confidence": 0.0
}

Do not wrap the JSON in markdown.
""".strip()
