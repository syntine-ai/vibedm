from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.core.errors import (
    ApiError,
    api_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.modules.auth.routers.auth import router as auth_router
from app.modules.automations.routers.automations import router as automations_router
from app.modules.billing.routers.billing import router as billing_router
from app.modules.contacts.routers.contacts import router as contacts_router
from app.modules.dashboard.routers.dashboard import router as dashboard_router
from app.modules.instagram.routers.instagram import router as instagram_router
from app.modules.webhooks.routers.webhooks import router as webhooks_router
from app.modules.workspaces.routers.workspaces import router as workspaces_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_exception_handler(ApiError, cast(Any, api_error_handler))
    app.add_exception_handler(StarletteHTTPException, cast(Any, http_error_handler))
    app.add_exception_handler(RequestValidationError, cast(Any, validation_error_handler))
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Workspace-Id"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get(settings.request_id_header) or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[settings.request_id_header.lower()] = request_id
        return response

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(workspaces_router)
    app.include_router(instagram_router)
    app.include_router(automations_router)
    app.include_router(contacts_router)
    app.include_router(dashboard_router)
    app.include_router(billing_router)
    app.include_router(webhooks_router)
    return app


app = create_app()
