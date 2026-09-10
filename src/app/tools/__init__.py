from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from app.core.config import settings


logger = logging.getLogger(__name__)


class AgentToolError(Exception):
    """Base exception for tool dispatch failures in the Agent layer."""


class ToolNotFoundError(AgentToolError):
    """Raised when the LLM asks for a tool that is not registered."""


class ToolArgumentsError(AgentToolError):
    """Raised when the LLM sends invalid tool arguments."""


class ToolExecutionError(AgentToolError):
    """Raised when a registered Python tool fails while running."""


def search_web(query: str) -> dict[str, Any]:
    """Search for information related to the research goal.

    This mock tool remains only for the existing Agent Loop tests. The /research
    path uses dedicated RSS and search tools for real evidence instead.
    """
    query = query.strip()
    if not query:
        raise ValueError("search_web requires a non-empty query.")

    provider = settings.search_web_provider.lower().strip()
    if provider != "mock":
        raise RuntimeError(
            f"Unsupported SEARCH_WEB_PROVIDER={settings.search_web_provider!r}. "
            "The legacy Agent Loop currently supports SEARCH_WEB_PROVIDER=mock."
        )

    return {
        "query": query,
        "provider": "mock",
        "results": [
            {
                "title": "AI agents are changing backend engineering work",
                "source": "MockSearch",
                "url": None,
                "excerpt": (
                    "Backend engineers can use agent architectures to automate "
                    "research, coding support, workflow orchestration, and internal tools."
                ),
            },
            {
                "title": "Java teams need agent-ready integration skills",
                "source": "MockSearch",
                "url": None,
                "excerpt": (
                    "Spring developers can transfer skills in APIs, DTOs, validation, "
                    "observability, and service boundaries into LLM tool-calling systems."
                ),
            },
            {
                "title": "New opportunities center on workflow ownership",
                "source": "MockSearch",
                "url": None,
                "excerpt": (
                    "The strongest career opportunities are in designing reliable loops "
                    "that connect LLM decisions to business tools and structured outputs."
                ),
            },
        ],
    }


TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "search_web": search_web,
}


def execute_tool(tool_name: str, arguments: str) -> str:
    """Find and run a registered Python tool.

    This dispatcher is the only place that maps an LLM tool name to executable
    Python code. Keeping the registry explicit makes the Agent Loop readable
    without filling it with if/elif branches for every tool.
    """
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        raise ToolNotFoundError(f"Tool {tool_name!r} is not registered.")

    try:
        parsed_arguments = json.loads(arguments or "{}")
    except json.JSONDecodeError as exc:
        raise ToolArgumentsError(
            f"Tool {tool_name!r} received invalid JSON arguments."
        ) from exc

    if not isinstance(parsed_arguments, dict):
        raise ToolArgumentsError(
            f"Tool {tool_name!r} arguments must be a JSON object."
        )

    logger.info("Tool execution start: %s", tool_name)
    try:
        result = tool(**parsed_arguments)
    except TypeError as exc:
        raise ToolArgumentsError(
            f"Tool {tool_name!r} received arguments that do not match its function signature."
        ) from exc
    except Exception as exc:
        raise ToolExecutionError(f"Tool {tool_name!r} failed: {exc}") from exc

    serialized_result = json.dumps(result, ensure_ascii=False)
    logger.info("Tool execution result: %s", serialized_result)
    return serialized_result
