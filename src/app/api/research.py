from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.research_service import ResearchService, ResearchServiceError


router = APIRouter(tags=["research"])


@router.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest) -> ResearchResponse:
    service = ResearchService()

    try:
        return service.research(request)
    except ResearchServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Research service failed.",
        ) from exc
