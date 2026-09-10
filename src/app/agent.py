from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.research import ResearchResponse
from app.tools import AgentToolError, execute_tool


logger = logging.getLogger(__name__)

MAX_STEPS = 5
PLACEHOLDER_KEYS = {"", "your_openai_api_key_here", "your_deepseek_api_key_here"}


# Tool Schema does not execute Python code.
# It only tells the LLM what tools are available and what JSON arguments each
# tool expects. The actual Python function is called later by execute_tool().
SEARCH_WEB_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "根据 query 搜索与研究目标相关的信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用于搜索的具体查询语句。",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

TOOLS = [SEARCH_WEB_TOOL_SCHEMA]


class AgentError(Exception):
    """Base exception for the opportunity research agent."""


class AgentConfigError(AgentError):
    """Raised when required LLM configuration is missing or invalid."""


class AgentLLMError(AgentError):
    """Raised when the LLM API call fails."""


class AgentResponseError(AgentError):
    """Raised when the final LLM response cannot become ResearchResponse."""


class AgentMaxStepsExceeded(AgentError):
    """Raised when the Agent Loop reaches its safety limit."""


def parse_opportunity_report(content: str) -> ResearchResponse:
    """Parse the final LLM JSON into the public response DTO."""
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


class OpportunityResearchAgent:
    def __init__(
        self,
        client: Any | None = None,
        model: str | None = None,
        max_steps: int = MAX_STEPS,
    ) -> None:
        self.max_steps = max_steps

        if client is not None:
            self.client = client
            self.model = model or "test-model"
            return

        self.client, default_model = self._build_openai_client()
        self.model = model or default_model

    def research(self, topic: str) -> ResearchResponse:
        logger.info("Agent start: topic=%s", topic)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": f"Research goal: {topic}"},
        ]

        for step in range(1, self.max_steps + 1):
            logger.info("Agent step: %s", step)
            response = self._call_llm(messages)
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)

            if tool_calls:
                messages.append(self._assistant_message_with_tool_calls(message))

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    arguments = tool_call.function.arguments or "{}"
                    logger.info("LLM requested tool: %s args=%s", tool_name, arguments)

                    try:
                        tool_result = execute_tool(tool_name, arguments)
                    except AgentToolError as exc:
                        tool_result = json.dumps(
                            {
                                "error": "tool_error",
                                "message": str(exc),
                            },
                            ensure_ascii=False,
                        )
                        logger.exception("Agent tool failed: %s", tool_name)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result,
                        }
                    )

                continue

            final_content = message.content or ""
            logger.info("Agent final answer: %s", final_content)
            try:
                result = parse_opportunity_report(final_content)
            except AgentResponseError:
                logger.exception("Agent failed: invalid final response")
                raise

            logger.info("Agent finished")
            return result

        # max_steps is a critical safety boundary in Agent systems. Without it,
        # a model can accidentally loop forever: LLM -> Tool -> LLM -> Tool...
        logger.error("Agent failed: max steps exceeded")
        raise AgentMaxStepsExceeded(
            f"Agent exceeded max_steps={self.max_steps} before producing a final answer."
        )

    def _call_llm(self, messages: list[dict[str, Any]]) -> Any:
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except OpenAIError as exc:
            logger.exception("Agent failed: LLM call failed")
            raise AgentLLMError("LLM call failed.") from exc
        except Exception as exc:
            logger.exception("Agent failed: unexpected LLM client error")
            raise AgentLLMError("LLM call failed.") from exc

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
    def _assistant_message_with_tool_calls(message: Any) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": message.content,
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
    def _system_prompt() -> str:
        return """
You are an opportunity research agent.

You must follow this process:
1. Use search_web when external research context is useful.
2. Read tool results carefully.
3. When you have enough context, stop calling tools and return final JSON only.

The final JSON must match this schema exactly:
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
