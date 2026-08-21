import asyncio
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.core.errors import (
    ApiError,
    api_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.middleware import configure_middlewares
from app.modules.auth.routers.auth import router as auth_router
from app.modules.automations.routers.automations import router as automations_router
from app.modules.billing.routers.billing import router as billing_router
from app.modules.contacts.routers.contacts import router as contacts_router
from app.modules.dashboard.routers.dashboard import router as dashboard_router
from app.modules.instagram.routers.instagram import router as instagram_router
from app.modules.webhooks.routers.webhooks import router as webhooks_router
from app.modules.workspaces.routers.workspaces import router as workspaces_router
from app.worker import run_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    worker_task = None
    if settings.run_worker_in_api:
        print("⚡ [API] Starting background worker in API process...")
        worker_task = asyncio.create_task(run_worker())
    
    yield
    
    if worker_task:
        print("⚡ [API] Stopping background worker...")
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        print("⚡ [API] Background worker stopped successfully.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_exception_handler(ApiError, cast(Any, api_error_handler))
    app.add_exception_handler(StarletteHTTPException, cast(Any, http_error_handler))
    app.add_exception_handler(RequestValidationError, cast(Any, validation_error_handler))
    app.add_exception_handler(Exception, unhandled_error_handler)

    configure_middlewares(app, settings)

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
