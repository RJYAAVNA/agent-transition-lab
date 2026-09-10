from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import feedparser
from pydantic import BaseModel, Field

from app.core.config import settings


class RSSItem(BaseModel):
    title: str = Field(min_length=1)
    link: str | None = None
    summary: str | None = None
    published_at: datetime | None = None
    source: str = Field(min_length=1)


class RSSToolError(Exception):
    """Base exception for RSS data source failures."""


class RSSFetchError(RSSToolError):
    """Raised when the RSS feed cannot be fetched."""


class RSSParseError(RSSToolError):
    """Raised when the RSS feed cannot be parsed into usable items."""


class RSSFeedTool:
    """Fetch an RSS/Atom feed and convert entries into internal RSSItem objects."""

    def __init__(
        self,
        feed_url: str | None = None,
        timeout_seconds: float | None = None,
        max_items: int | None = None,
        source_name: str | None = None,
    ) -> None:
        self.feed_url = feed_url or settings.rss_feed_url
        self.timeout_seconds = timeout_seconds or settings.rss_timeout_seconds
        self.max_items = max_items or settings.rss_max_items
        self.source_name = source_name or settings.rss_source_name

    def fetch(self) -> list[RSSItem]:
        content = self._request_feed()
        return self.parse(content)

    def parse(self, content: bytes | str) -> list[RSSItem]:
        parsed_feed = feedparser.parse(content)
        entries = list(parsed_feed.get("entries", []))

        if parsed_feed.get("bozo") and not entries:
            reason = parsed_feed.get("bozo_exception")
            raise RSSParseError(f"RSS parsing failed: {reason}")

        if not entries:
            raise RSSParseError("RSS feed did not contain any entries.")

        source = self._clean_text(
            self.source_name
            or parsed_feed.get("feed", {}).get("title")
            or self.feed_url
        )

        items: list[RSSItem] = []
        for entry in entries[: self.max_items]:
            title = self._clean_text(entry.get("title") or "Untitled RSS item")
            link = self._clean_text(entry.get("link")) or None
            summary = self._clean_text(
                entry.get("summary") or entry.get("description") or entry.get("subtitle")
            )
            published_at = self._published_at(entry)

            items.append(
                RSSItem(
                    title=title,
                    link=link,
                    summary=summary or None,
                    published_at=published_at,
                    source=source,
                )
            )

        return items

    def _request_feed(self) -> bytes:
        if not self.feed_url.startswith(("http://", "https://")):
            raise RSSFetchError("RSS_FEED_URL must be an HTTP or HTTPS URL.")

        request = Request(
            self.feed_url,
            headers={"User-Agent": settings.rss_user_agent},
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status_code = response.getcode()
                if status_code < 200 or status_code >= 300:
                    raise RSSFetchError(
                        f"RSS request failed with HTTP status {status_code}."
                    )
                return response.read()
        except HTTPError as exc:
            raise RSSFetchError(
                f"RSS request failed with HTTP status {exc.code}."
            ) from exc
        except (TimeoutError, URLError) as exc:
            reason = getattr(exc, "reason", exc)
            raise RSSFetchError(f"RSS request failed: {reason}") from exc

    @staticmethod
    def _published_at(entry: Any) -> datetime | None:
        parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed_time:
            return datetime(*parsed_time[:6], tzinfo=UTC)

        raw_time = entry.get("published") or entry.get("updated")
        if not raw_time:
            return None

        try:
            parsed = parsedate_to_datetime(raw_time)
        except (TypeError, ValueError):
            return None

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""
        text = html.unescape(str(value))
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
