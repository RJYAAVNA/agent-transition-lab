import pytest

from app.schemas.research import ResearchRequest
from app.services.research_service import ResearchService, ResearchServiceError
from app.tools.rss_tool import RSSFetchError, RSSItem
from app.tools.search_tool import SearchResult


class FakeRSSFeedTool:
    def __init__(self, items: list[RSSItem] | None = None) -> None:
        self.items = items or []

    def fetch(self) -> list[RSSItem]:
        return self.items


class FakeSearchTool:
    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self.results = results or []
        self.queries: list[str] = []

    def search(self, query: str) -> list[SearchResult]:
        self.queries.append(query)
        return self.results


def test_research_service_maps_rss_items_to_evidence() -> None:
    service = ResearchService(
        rss_tool=FakeRSSFeedTool(
            [
                RSSItem(
                    title="AI Agent platforms gain enterprise adoption",
                    link="https://example.com/ai-agent-platforms",
                    summary="Enterprise teams are testing agent tools.",
                    source="Example Research Feed",
                )
            ]
        ),
        search_tool=FakeSearchTool(),
    )

    response = service.research(ResearchRequest(topic="AI Agent"))

    assert response.evidence[0].title == "AI Agent platforms gain enterprise adoption"
    assert str(response.evidence[0].url) == "https://example.com/ai-agent-platforms"
    assert response.evidence[0].source == "Example Research Feed"
    assert response.evidence[0].excerpt == "Enterprise teams are testing agent tools."


def test_research_service_maps_search_results_to_evidence() -> None:
    search_tool = FakeSearchTool(
        [
            SearchResult(
                title="Software agent",
                url="https://en.wikipedia.org/?curid=12345",
                snippet="A software agent acts for a user.",
                source="Wikipedia Search",
            )
        ]
    )
    service = ResearchService(
        rss_tool=FakeRSSFeedTool(),
        search_tool=search_tool,
    )

    response = service.research(ResearchRequest(topic="AI Agent"))

    assert search_tool.queries == ["AI Agent"]
    assert response.evidence[0].title == "Software agent"
    assert str(response.evidence[0].url) == "https://en.wikipedia.org/?curid=12345"
    assert response.evidence[0].source == "Wikipedia Search"
    assert response.evidence[0].excerpt == "A software agent acts for a user."


def test_research_service_raises_locatable_error_when_tool_fails() -> None:
    class BrokenRSSFeedTool:
        def fetch(self) -> list[RSSItem]:
            raise RSSFetchError("RSS request failed with HTTP status 503.")

    service = ResearchService(rss_tool=BrokenRSSFeedTool(), search_tool=FakeSearchTool())

    with pytest.raises(ResearchServiceError) as exc_info:
        service.research(ResearchRequest(topic="AI Agent"))

    assert "RSS data source failed" in str(exc_info.value)
    assert "503" in str(exc_info.value)
