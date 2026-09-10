import pytest
from pydantic import ValidationError

from app.schemas.research import (
    Evidence,
    Opportunity,
    ResearchResponse,
    Risk,
    Signal,
)


def test_research_response_rejects_confidence_outside_allowed_range() -> None:
    with pytest.raises(ValidationError):
        ResearchResponse(
            topic="AI Agent market",
            summary="Mock summary.",
            signals=[Signal(title="Signal", description="Signal description.")],
            opportunities=[
                Opportunity(title="Opportunity", description="Opportunity description.")
            ],
            risks=[Risk(title="Risk", description="Risk description.")],
            evidence=[Evidence(title="Evidence", source="Stub")],
            confidence=1.1,
        )
