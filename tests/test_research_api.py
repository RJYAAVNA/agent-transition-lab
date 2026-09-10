import anyio
import httpx2
import pytest

from app.main import app
from app.schemas.research import Evidence, Opportunity, ResearchResponse, Risk, Signal
from app.services.research_service import ResearchService
from app.tools.rss_tool import RSSFetchError


def _fake_research_response(topic: str) -> ResearchResponse:
    return ResearchResponse(
        topic=topic,
        summary=f"Mock research result for {topic}.",
        signals=[
            Signal(
                title="Growing interest",
                description=f"Mock signal indicating visible attention around {topic}.",
            )
        ],
        opportunities=[
            Opportunity(
                title="Focused portfolio project",
                description=f"Mock opportunity to present structured research about {topic}.",
            )
        ],
        risks=[
            Risk(
                title="Fixture risk",
                description="Fixture risk because the API unit test does not call external services.",
            )
        ],
        evidence=[
            Evidence(
                title="Fixture evidence item",
                source="Fixture source",
                url="https://example.com/research",
                excerpt="Fixture evidence used only to validate the API contract.",
            )
        ],
        confidence=0.5,
    )


async def _post_research(payload: dict[str, object]) -> httpx2.Response:
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post("/research", json=payload)


def post_research(payload: dict[str, object]) -> httpx2.Response:
    return anyio.run(_post_research, payload)


def test_post_research_returns_structured_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ResearchService,
        "research",
        lambda self, request: _fake_research_response(request.topic),
    )

    response = post_research({"topic": "AI Agent market"})

    assert response.status_code == 200

    data = response.json()
    assert data["topic"] == "AI Agent market"
    assert "summary" in data
    assert "signals" in data
    assert "opportunities" in data
    assert "risks" in data
    assert "evidence" in data
    assert "confidence" in data


def test_post_research_rejects_empty_topic() -> None:
    response = post_research({"topic": "   "})

    assert 400 <= response.status_code < 500


def test_post_research_confidence_is_between_zero_and_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ResearchService,
        "research",
        lambda self, request: _fake_research_response(request.topic),
    )

    response = post_research({"topic": "AI Agent market"})

    assert response.status_code == 200
    confidence = response.json()["confidence"]
    assert 0 <= confidence <= 1


def test_post_research_returns_data_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenRSSFeedTool:
        def fetch(self) -> list[object]:
            raise RSSFetchError("RSS request failed with HTTP status 503.")

    monkeypatch.setattr(
        "app.services.research_service.RSSFeedTool",
        lambda: BrokenRSSFeedTool(),
    )

    response = post_research({"topic": "AI Agent market"})

    assert response.status_code == 502
    assert "RSS data source failed" in response.json()["detail"]
    assert "503" in response.json()["detail"]
