from datetime import UTC, datetime

import pytest

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
