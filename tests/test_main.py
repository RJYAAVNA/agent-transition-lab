from fastapi import FastAPI

from app.main import create_app


def test_create_app_registers_research_route() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "Opportunity Research Agent"
    assert "/research" in app.openapi()["paths"]
