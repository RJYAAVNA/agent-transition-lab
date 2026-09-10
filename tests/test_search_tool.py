import pytest

from app.tools.search_tool import SearchInputError, SearchParseError, SearchTool


SAMPLE_SEARCH_RESPONSE = b"""{
  "batchcomplete": "",
  "query": {
    "search": [
      {
        "ns": 0,
        "title": "Software agent",
        "pageid": 12345,
        "snippet": "A software agent is a computer program that acts for a user."
      }
    ]
  }
}
"""


def test_search_tool_parses_provider_response_into_results() -> None:
    tool = SearchTool(
        base_url="https://example.com/search",
        source_name="Example Search",
        default_limit=5,
    )

    results = tool.parse(SAMPLE_SEARCH_RESPONSE, limit=5)

    assert len(results) == 1
    assert results[0].title == "Software agent"
    assert results[0].url == "https://en.wikipedia.org/?curid=12345"
    assert results[0].snippet == "A software agent is a computer program that acts for a user."
    assert results[0].source == "Example Search"


def test_search_tool_rejects_empty_query() -> None:
    tool = SearchTool(base_url="https://example.com/search")

    with pytest.raises(SearchInputError):
        tool.search("   ")


def test_search_tool_rejects_invalid_provider_shape() -> None:
    tool = SearchTool(base_url="https://example.com/search")

    with pytest.raises(SearchParseError):
        tool.parse(b'{"query": {"pages": []}}')
