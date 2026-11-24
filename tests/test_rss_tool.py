from datetime import UTC, datetime
from io import BytesIO
from urllib.request import Request

import pytest

from app.tools import rss_tool
from app.tools.rss_tool import RSSFeedTool, RSSParseError


SAMPLE_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Research Feed</title>
    <item>
      <title>AI Agent platforms gain enterprise adoption</title>
      <link>https://example.com/ai-agent-platforms</link>
      <description><![CDATA[<p>Enterprise teams are testing agent tools.</p>]]></description>
      <pubDate>Tue, 08 Sep 2026 10:30:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_rss_tool_parses_sample_feed_into_items() -> None:
    tool = RSSFeedTool(
        feed_url="https://example.com/feed.xml",
        source_name=None,
        max_items=10,
    )

    items = tool.parse(SAMPLE_FEED)

    assert len(items) == 1
    assert items[0].title == "AI Agent platforms gain enterprise adoption"
    assert items[0].link == "https://example.com/ai-agent-platforms"
    assert items[0].summary == "Enterprise teams are testing agent tools."
    assert items[0].published_at == datetime(2026, 9, 8, 10, 30, tzinfo=UTC)
    assert items[0].source == "Example Research Feed"


def test_rss_tool_rejects_empty_feed() -> None:
    tool = RSSFeedTool(feed_url="https://example.com/feed.xml")

    with pytest.raises(RSSParseError):
        tool.parse(b"<rss><channel><title>Empty</title></channel></rss>")


def test_fetch_requests_configured_feed(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = RSSFeedTool(
        feed_url="https://example.com/feed.xml",
        source_name="Test feed",
        timeout_seconds=3,
    )

    class FakeResponse(BytesIO):
        def getcode(self) -> int:
            return 200

    def fake_urlopen(request: Request, *, timeout: float) -> FakeResponse:
        assert request.full_url == "https://example.com/feed.xml"
        assert request.get_header("User-agent") == "ExampleAgent"
        assert timeout == 3
        return FakeResponse(SAMPLE_FEED)

    monkeypatch.setattr(rss_tool.settings, "rss_user_agent", "ExampleAgent")
    monkeypatch.setattr(rss_tool, "urlopen", fake_urlopen)
    assert tool.fetch()[0].source == "Test feed"
