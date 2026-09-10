from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if not value:
        return None
    return value.strip()


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    return float(value)


_load_env_file()


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Opportunity Research Agent")
    app_version: str = "0.1.0"
    app_env: str = os.getenv("APP_ENV", "development")
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: str | None = _optional_env("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    deepseek_api_key: str | None = _optional_env("DEEPSEEK_API_KEY")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    search_web_provider: str = os.getenv("SEARCH_WEB_PROVIDER", "mock")
    rss_feed_url: str = os.getenv(
        "RSS_FEED_URL",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
    )
    rss_source_name: str | None = _optional_env("RSS_SOURCE_NAME")
    rss_user_agent: str = os.getenv(
        "RSS_USER_AGENT",
        "OpportunityResearchAgent/0.1 (+https://local.dev)",
    )
    rss_timeout_seconds: float = _float_env("RSS_TIMEOUT_SECONDS", 8.0)
    rss_max_items: int = _int_env("RSS_MAX_ITEMS", 10)
    search_base_url: str = os.getenv(
        "SEARCH_BASE_URL",
        "https://en.wikipedia.org/w/api.php",
    )
    search_source_name: str = os.getenv("SEARCH_SOURCE_NAME", "Wikipedia Search")
    search_user_agent: str = os.getenv(
        "SEARCH_USER_AGENT",
        "OpportunityResearchAgent/0.1 (+https://local.dev)",
    )
    search_timeout_seconds: float = _float_env("SEARCH_TIMEOUT_SECONDS", 8.0)
    search_max_results: int = _int_env("SEARCH_MAX_RESULTS", 5)


settings = Settings()
