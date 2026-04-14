from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from .account import router as account_router
from .apps import router as apps_router
from .dashboard import router as dashboard_router
from .diagnostics import router as diagnostics_router
from .idle_jobs import router as idle_jobs_router
from .nodes import router as nodes_router
from .services import router as services_router
from .sessions import router as sessions_router
from .settings import router as settings_router

router = APIRouter()

# Redirect roots to dashboard
@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/playground/dashboard", status_code=303)

@router.get("/playground", include_in_schema=False)
def playground_root() -> RedirectResponse:
    return RedirectResponse("/playground/dashboard", status_code=303)

router.include_router(dashboard_router)
router.include_router(account_router)
router.include_router(apps_router)
router.include_router(nodes_router)
router.include_router(sessions_router)
router.include_router(services_router)
router.include_router(idle_jobs_router)
router.include_router(diagnostics_router)
router.include_router(settings_router)

__all__ = ["router"]
