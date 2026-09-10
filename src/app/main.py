from __future__ import annotations

import logging

if __name__ == "__main__" and not __package__:
    import sys
    from pathlib import Path

    # Direct script execution needs the project root to resolve app imports.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI

from app.api.research import router as research_router
from app.core.config import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(research_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
