# Vibedm Backend

FastAPI backend for the Vibedm/DMFlow app.

## Local setup

```powershell
uv sync
Copy-Item .env.example .env
uv run uvicorn app.main:app --reload
```

Run the background worker in a separate terminal:

```powershell
uv run python -m app.worker
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

OpenAPI:

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```

## Scope

Implemented module surface:

- `auth`
- `workspaces`
- `instagram`
- `automations`
- `contacts`
- `dashboard`
- `billing`
- `webhooks`

Excluded from this phase:

- `products`
- `orders`
- `referrals`

The database migrations remain in `D:\Code\vibedm\vibedm_frontend\supabase\migrations`.

## Verification

```powershell
uv run pytest
uv run ruff check .
uv run mypy app
```

Frontend client generation can be added later from `/openapi.json`.
