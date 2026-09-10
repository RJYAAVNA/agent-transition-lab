from __future__ import annotations

import re

from app.schemas.research import (
    Evidence,
    Opportunity,
    ResearchRequest,
    ResearchResponse,
    Risk,
    Signal,
)
from app.tools.rss_tool import RSSFeedTool, RSSItem, RSSToolError
from app.tools.search_tool import SearchResult, SearchTool, SearchToolError


class ResearchService:
    def __init__(
        self,
        rss_tool: RSSFeedTool | None = None,
        search_tool: SearchTool | None = None,
    ) -> None:
        self.rss_tool = rss_tool or RSSFeedTool()
        self.search_tool = search_tool or SearchTool()

    def research(self, request: ResearchRequest) -> ResearchResponse:
        try:
            rss_items = self.rss_tool.fetch()
        except RSSToolError as exc:
            raise ResearchServiceError(f"RSS data source failed: {exc}") from exc

        try:
            search_results = self.search_tool.search(request.topic)
        except SearchToolError as exc:
            raise ResearchServiceError(f"Search data source failed: {exc}") from exc

        selected_items = self._select_relevant_items(rss_items, request.topic)
        evidence = [self._rss_to_evidence(item) for item in selected_items]
        evidence.extend(
            self._search_to_evidence(result) for result in search_results
        )
        if not evidence:
            raise ResearchServiceError("Evidence data source returned no usable items.")

        return ResearchResponse(
            topic=request.topic,
            summary=(
                f"Initial research snapshot for {request.topic} based on recent RSS "
                "items from a real external data source."
            ),
            signals=[
                Signal(
                    title="Recent external evidence",
                    description=(
                        "The evidence list is populated from live RSS and search "
                        "content rather than internal fixture data."
                    ),
                )
            ],
            opportunities=[
                Opportunity(
                    title="Evidence-backed follow-up",
                    description=(
                        f"Use the linked source items to identify concrete opportunity "
                        f"angles for {request.topic}."
                    ),
                )
            ],
            risks=[
                Risk(
                    title="Broad feed relevance",
                    description=(
                        "The RSS feed may be broad, while the search source is queried "
                        "directly by topic."
                    ),
                )
            ],
            evidence=evidence,
            confidence=0.45,
        )

    @staticmethod
    def _select_relevant_items(items: list[RSSItem], topic: str) -> list[RSSItem]:
        terms = {
            term
            for term in re.split(r"[^a-zA-Z0-9+#.-]+", topic.lower())
            if len(term) >= 2
        }
        if not terms:
            return items

        matched_items = [
            item
            for item in items
            if terms
            & set(
                re.split(
                    r"[^a-zA-Z0-9+#.-]+",
                    f"{item.title} {item.summary or ''}".lower(),
                )
            )
        ]
        return matched_items or items

    @classmethod
    def _rss_to_evidence(cls, item: RSSItem) -> Evidence:
        return Evidence(
            title=cls._truncate(item.title, 200),
            source=cls._truncate(item.source, 200),
            url=item.link if cls._is_http_url(item.link) else None,
            excerpt=cls._truncate(item.summary, 2000) if item.summary else None,
        )

    @classmethod
    def _search_to_evidence(cls, result: SearchResult) -> Evidence:
        return Evidence(
            title=cls._truncate(result.title, 200),
            source=cls._truncate(result.source, 200),
            url=result.url if cls._is_http_url(result.url) else None,
            excerpt=cls._truncate(result.snippet, 2000) if result.snippet else None,
        )

    @staticmethod
    def _is_http_url(value: str | None) -> bool:
        return value is not None and value.startswith(("http://", "https://"))

    @staticmethod
    def _truncate(value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[: max_length - 3].rstrip() + "..."


class ResearchServiceError(Exception):
    """Raised when research cannot be completed from available real evidence."""
