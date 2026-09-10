import pytest

from app.tools import ToolArgumentsError, ToolNotFoundError, execute_tool


def test_execute_tool_rejects_unknown_tool() -> None:
    with pytest.raises(ToolNotFoundError):
        execute_tool("missing_tool", "{}")


def test_execute_tool_rejects_invalid_json_arguments() -> None:
    with pytest.raises(ToolArgumentsError):
        execute_tool("search_web", "{not-json")


def test_execute_tool_runs_registered_search_web() -> None:
    result = execute_tool("search_web", '{"query": "AI Agent for Java backend"}')

    assert "AI Agent for Java backend" in result
    assert "MockSearch" in result
