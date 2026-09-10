from __future__ import annotations

import html
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from app.core.config import settings


class SearchResult(BaseModel):
    title: str = Field(min_length=1)
    url: str | None = None
    snippet: str | None = None
    source: str = Field(min_length=1)


class SearchToolError(Exception):
    """Base exception for search data source failures."""


class SearchInputError(SearchToolError):
    """Raised when search input is invalid."""


class SearchFetchError(SearchToolError):
    """Raised when the search provider cannot be reached."""


class SearchParseError(SearchToolError):
    """Raised when the search provider response is not usable."""


class SearchTool:
    """Query a real search provider and normalize results for upper layers."""

    MIN_LIMIT = 1
    MAX_LIMIT = 10

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        default_limit: int | None = None,
        source_name: str | None = None,
    ) -> None:
        self.base_url = base_url or settings.search_base_url
        self.timeout_seconds = timeout_seconds or settings.search_timeout_seconds
        self.default_limit = default_limit or settings.search_max_results
        self.source_name = source_name or settings.search_source_name

    def search(self, query: str, limit: int | None = None) -> list[SearchResult]:
        normalized_query = query.strip()
        if not normalized_query:
            raise SearchInputError("Search query must not be empty.")

        normalized_limit = self._normalize_limit(limit or self.default_limit)
        content = self._request_search(normalized_query, normalized_limit)
        return self.parse(content, limit=normalized_limit)

    def parse(self, content: bytes | str, limit: int | None = None) -> list[SearchResult]:
        normalized_limit = self._normalize_limit(limit or self.default_limit)

        try:
            payload = json.loads(content.decode("utf-8") if isinstance(content, bytes) else content)
        except json.JSONDecodeError as exc:
            raise SearchParseError("Search provider returned invalid JSON.") from exc

        raw_results = payload.get("query", {}).get("search")
        if not isinstance(raw_results, list):
            raise SearchParseError("Search provider response missing query.search list.")

        results: list[SearchResult] = []
        for raw_result in raw_results[:normalized_limit]:
            if not isinstance(raw_result, dict):
                raise SearchParseError("Search provider returned a non-object result.")

            title = self._clean_text(raw_result.get("title"))
            if not title:
                raise SearchParseError("Search provider returned a result without title.")

            page_id = raw_result.get("pageid")
            url = self._page_url(page_id) if page_id is not None else None
            snippet = self._clean_text(raw_result.get("snippet")) or None

            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source=self.source_name,
                )
            )

        if not results:
            raise SearchParseError("Search provider returned no results.")

        return results

    def _request_search(self, query: str, limit: int) -> bytes:
        if not self.base_url.startswith(("http://", "https://")):
            raise SearchFetchError("SEARCH_BASE_URL must be an HTTP or HTTPS URL.")

        params = urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "format": "json",
                "utf8": 1,
            }
        )
        separator = "&" if "?" in self.base_url else "?"
        request = Request(
            f"{self.base_url}{separator}{params}",
            headers={"User-Agent": settings.search_user_agent},
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status_code = response.getcode()
                if status_code < 200 or status_code >= 300:
                    raise SearchFetchError(
                        f"Search request failed with HTTP status {status_code}."
                    )
                return response.read()
        except HTTPError as exc:
            raise SearchFetchError(
                f"Search request failed with HTTP status {exc.code}."
            ) from exc
        except (TimeoutError, URLError) as exc:
            reason = getattr(exc, "reason", exc)
            raise SearchFetchError(f"Search request failed: {reason}") from exc

    @classmethod
    def _normalize_limit(cls, limit: int) -> int:
        if limit < cls.MIN_LIMIT or limit > cls.MAX_LIMIT:
            raise SearchInputError(
                f"Search limit must be between {cls.MIN_LIMIT} and {cls.MAX_LIMIT}."
            )
        return limit

    def _page_url(self, page_id: object) -> str | None:
        try:
            page_id_int = int(page_id)
        except (TypeError, ValueError):
            return None
        return f"https://en.wikipedia.org/?curid={page_id_int}"

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""
        text = html.unescape(str(value))
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
