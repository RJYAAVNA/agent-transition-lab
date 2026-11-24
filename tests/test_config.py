from app.core import config


def test_env_file_precedence_and_legacy_fallback(tmp_path, monkeypatch) -> None:
    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.setattr(config, "__file__", str(src / "app/core/config.py"))
    monkeypatch.setenv("APP_ENV", "process")
    # Restore keys inserted directly into os.environ by the loader.
    for name in ("RSS_SOURCE_NAME", "SEARCH_SOURCE_NAME"):
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)
    (tmp_path / ".env").write_text(
        'APP_ENV=root\nRSS_SOURCE_NAME="Root feed"\n', encoding="utf-8-sig"
    )
    (src / ".env").write_text(
        'RSS_SOURCE_NAME=Legacy\nSEARCH_SOURCE_NAME=Legacy\n', encoding="utf-8"
    )

    config._load_env_file()

    assert config.os.environ["APP_ENV"] == "process"
    assert config.os.environ["RSS_SOURCE_NAME"] == "Root feed"
    assert config.os.environ["SEARCH_SOURCE_NAME"] == "Legacy"
