# Backend API Plan — DMFlow (FastAPI)

Source of truth for the backend team. Frontend is a TanStack Start SPA that currently runs on mock data; this document defines the HTTP contract the FastAPI service must implement so the frontend can be wired to real data with minimal churn.

Cross-reference these existing product briefs before changing behavior:
- `doc/onboarding-workspace-flow.md` — signup → Connect Instagram → auto-create workspace
- `doc/billing.md` — per-workspace plans, INR pricing, monthly/yearly

---

## 1. Tech & conventions

- **Framework:** FastAPI (Python 3.11+), `uvicorn` in dev, `gunicorn -k uvicorn.workers.UvicornWorker` in prod.
- **DB:** Supabase Postgres. Backend uses the **service role key** server-side; RLS still enforced for any Supabase JS calls made from the browser. See `database-plan.md`.
- **Auth:** Supabase Auth JWT (HS256). FastAPI verifies the JWT on every protected request via dependency `get_current_user`. No session cookies; bearer tokens only.
- **Base URL:** `/api/v1`
- **Content type:** `application/json` everywhere except file uploads (`multipart/form-data`).
- **IDs:** UUID v4 (string in JSON).
- **Timestamps:** ISO-8601 UTC (`2026-05-26T10:00:00Z`).
- **Money:** integer **paise** (INR) on the wire; format on the client. `amount: 9900` = ₹99.
- **Pagination:** cursor-based. Query: `?limit=25&cursor=<opaque>`. Response: `{ items, next_cursor }`.
- **Filtering:** documented per endpoint; always validated with Pydantic.
- **Errors:** RFC 7807-ish envelope:
  ```json
  { "error": { "code": "workspace_not_found", "message": "...", "details": {} } }
  ```
  HTTP status reflects category (400/401/403/404/409/422/429/5xx).
- **Idempotency:** mutating endpoints that may be retried (checkout, webhook handlers) accept `Idempotency-Key` header.
- **Rate limiting:** per-user + per-IP token bucket (e.g. `slowapi` or Redis). Suggested 60 req/min default, tighter on auth + checkout.
- **CORS:** allow the frontend origin(s) only; `Authorization`, `Content-Type`, `Idempotency-Key` headers; methods `GET,POST,PATCH,DELETE,OPTIONS`.
- **Workspace scoping:** every business resource is scoped to a workspace. Pass workspace via header `X-Workspace-Id: <uuid>` **or** path prefix `/workspaces/{workspace_id}/...`. Pick one and stay consistent — recommendation below uses the header pattern to keep URLs short and matches how the sidebar workspace switcher works.

### Standard request headers
```
Authorization: Bearer <supabase_jwt>
X-Workspace-Id: <uuid>          # required for workspace-scoped routes
Idempotency-Key: <uuid>         # optional, for retry-safe mutations
```

### Standard response envelope
List endpoints:
```json
{ "items": [...], "next_cursor": "eyJ..." | null }
```
Single resource: returned as a bare object. Mutations return the updated resource.

---

## 2. Auth & sessions

Supabase Auth handles email/password, Google OAuth, and password reset directly from the browser (frontend talks to Supabase JS). FastAPI only needs to **verify** the resulting JWT and mirror user state.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/sync` | Called by the frontend right after Supabase signup/login. Backend upserts a `users` row from JWT claims and returns the merged profile. |
| GET  | `/api/v1/auth/me` | Returns current user + memberships + active workspace summary. |
| POST | `/api/v1/auth/logout` | Optional. Revokes refresh token server-side (calls Supabase admin API). |

`/auth/me` response:
```json
{
  "user": { "id": "...", "email": "...", "first_name": "Alex", "last_name": "Morgan", "phone": null, "avatar_url": null },
  "workspaces": [
    { "id": "w1", "name": "Alex Morgan", "role": "owner", "ig_username": "alex.creates", "plan": "free", "active": true }
  ]
}
```

---

## 3. Onboarding → Instagram → Workspace

Implements `doc/onboarding-workspace-flow.md`. The user never types a workspace name or IG handle.

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/v1/instagram/oauth/start` | Returns the IG OAuth authorize URL (`{ url, state }`). State is signed + short-TTL. |
| POST | `/api/v1/instagram/oauth/callback` | Body: `{ code, state }`. Exchanges code for long-lived token, fetches IG profile, **creates the workspace**, marks it active, returns the new workspace. |
| POST | `/api/v1/workspaces/connect-instagram` | Same callback flow but for "Add workspace" from Settings (`doc/onboarding-workspace-flow.md`). |
| DELETE | `/api/v1/instagram/connection` | Disconnects IG from the current workspace. |

Callback response:
```json
{
  "workspace": { "id": "...", "name": "alex.creates", "ig_username": "alex.creates", "ig_user_id": "178...", "plan": "free", "active": true },
  "redirect_to": "/dashboard"
}
```

Rules enforced server-side:
- Workspace `name` defaults to the IG username (or display name) — never user-supplied at this step.
- New workspace is inserted with `plan = 'free'` and `active = true`; the previously active workspace flips to `active = false` for this user.
- One IG account ↔ one workspace per user. If the IG `ig_user_id` is already connected to another workspace owned by this user, return `409 ig_already_connected`.

---

## 4. Workspaces

| Method | Path | Purpose |
|---|---|---|
| GET    | `/api/v1/workspaces` | List workspaces the current user belongs to. |
| GET    | `/api/v1/workspaces/{id}` | Workspace detail (members, plan, IG connection, usage counters). |
| PATCH  | `/api/v1/workspaces/{id}` | Update `name` only. |
| POST   | `/api/v1/workspaces/{id}/activate` | Switch the user's active workspace. |
| DELETE | `/api/v1/workspaces/{id}` | Owner only. Soft-delete; cancels paid subscription. |
| GET    | `/api/v1/workspaces/{id}/members` | List members. |
| POST   | `/api/v1/workspaces/{id}/members` | Invite (`email`, `role`). Sends email via Supabase or Resend. |
| PATCH  | `/api/v1/workspaces/{id}/members/{user_id}` | Change role. |
| DELETE | `/api/v1/workspaces/{id}/members/{user_id}` | Remove member. |

Roles: `owner`, `admin`, `member`. Only `owner` can delete the workspace or transfer ownership.

---

## 5. Automations

The editor (`src/routes/automations.$id.edit.tsx`) drives this shape. An automation = one trigger + one or more action steps.

Triggers (enum `trigger_type`):
- `comment_post` — user comments on a post or reel
- `dm` — user DMs you
- `live_comment` — user comments on a LIVE
- `story_reply` — user replies to a story
- `story_mention` — (coming soon, accept value but reject activation)

Actions (enum `action_type`): `send_dm`, `send_comment_reply`, `ask_for_email`, `ask_for_phone`, `send_link`, `tag_contact`.

| Method | Path | Purpose |
|---|---|---|
| GET    | `/api/v1/automations` | List. Filters: `status`, `trigger_type`, `q`. |
| POST   | `/api/v1/automations` | Create draft (`name`, optional `trigger_type`). |
| GET    | `/api/v1/automations/{id}` | Detail incl. nested `trigger_config` and `steps[]`. |
| PATCH  | `/api/v1/automations/{id}` | Update `name`, `trigger_type`, `trigger_config`, `steps`. |
| POST   | `/api/v1/automations/{id}/activate` | Validates the automation is complete; flips `status` to `active`. |
| POST   | `/api/v1/automations/{id}/deactivate` | |
| DELETE | `/api/v1/automations/{id}` | |
| POST   | `/api/v1/automations/{id}/test-trigger` | Dry-run with a synthetic event. Returns the executed step trace. |
| GET    | `/api/v1/automations/{id}/runs` | Paginated execution log. |

Activation rules (return `422 automation_incomplete` with `details.missing: []`):
- `trigger_type` set
- `trigger_config` valid for that type (e.g. `comment_post` requires `post_id` + at least one keyword)
- `steps` length ≥ 1

`trigger_config` examples:
```json
// comment_post
{ "post_id": "17841...", "keywords": ["GIVEAWAY", "DROP"], "match": "any" }
// dm
{ "keywords": ["price", "buy"], "match": "any" }
// story_reply
{ "story_ids": ["..."], "keywords": [] }
```

`steps[]` shape:
```json
[
  { "order": 1, "action_type": "send_dm", "config": { "message": "Hey!", "buttons": [{ "label": "Shop", "url": "..." }] } },
  { "order": 2, "action_type": "ask_for_email", "config": { "prompt": "Drop your email" } }
]
```

---

## 6. Contacts

| Method | Path | Purpose |
|---|---|---|
| GET    | `/api/v1/contacts` | List. Filters: `q` (matches username/name/email/phone), `source_automation_id`, `tag`. |
| GET    | `/api/v1/contacts/{id}` | Detail incl. interaction history. |
| POST   | `/api/v1/contacts` | Manual create. |
| PATCH  | `/api/v1/contacts/{id}` | Update editable fields (`name`, `email`, `phone`, `notes`, `tags`). |
| DELETE | `/api/v1/contacts/{id}` | |
| GET    | `/api/v1/contacts/export.csv` | Streaming CSV download. |
| POST   | `/api/v1/contacts/import` | Multipart CSV upload, returns `{ imported, skipped, errors[] }`. |

---

## 7. Products & Orders

| Method | Path | Purpose |
|---|---|---|
| GET    | `/api/v1/products` | List. |
| POST   | `/api/v1/products` | Create. Body: `name`, `price` (paise), `link`, `image_url?`, `description?`. |
| GET    | `/api/v1/products/{id}` | |
| PATCH  | `/api/v1/products/{id}` | |
| DELETE | `/api/v1/products/{id}` | |
| GET    | `/api/v1/orders` | List. Filters: `status` (`pending|completed|cancelled|refunded`), `contact_id`, `product_id`, date range. |
| POST   | `/api/v1/orders` | Create. Body: `contact_id`, `product_id`, `amount` (paise), `status?`. |
| GET    | `/api/v1/orders/{id}` | |
| PATCH  | `/api/v1/orders/{id}` | Update `status` only (state machine: `pending → completed | cancelled`, `completed → refunded`). |

---

## 8. Dashboard / Analytics

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/dashboard/stats` | KPIs for the active workspace + range (`?range=7d|30d|90d`). DMs sent, replies, contacts captured, revenue (paise). |
| GET | `/api/v1/dashboard/recent-activity` | Recent automation runs + contact captures + orders, merged + sorted. |
| GET | `/api/v1/usage`        | Returns the workspace's current-period usage vs plan limits (`dm_count`, `dm_limit`, `contact_count`, `contact_limit`). Drives the sidebar meters. |

---

## 9. Billing (implements `doc/billing.md`)

Plans are seeded in the DB (`plans` table) so they can be tweaked without redeploying. INR, paise on the wire. Yearly = monthly × 12 × 0.8 (computed server-side, not client-side).

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/v1/billing/plans` | List plans (`free`, `pro`, `business`, `enterprise`) with monthly + yearly prices and feature bullets. |
| GET  | `/api/v1/billing/subscription` | The active workspace's current plan, cycle, renewal date, status. |
| POST | `/api/v1/billing/checkout` | Body: `{ plan_id, cycle: "monthly"|"yearly" }`. Returns `{ checkout_url }` (Stripe/Razorpay Checkout). Free plan activates instantly and returns `{ activated: true }`. |
| POST | `/api/v1/billing/portal` | Returns Stripe/Razorpay customer portal URL. |
| POST | `/api/v1/billing/cancel` | Schedules cancellation at period end. |
| GET  | `/api/v1/billing/invoices` | Workspace invoice history. |
| GET  | `/api/v1/billing/invoices/{id}.pdf` | PDF download (proxied from provider). |

**Important:** plan changes are persisted only by the webhook handler, never by the checkout response. Frontend must refetch `/billing/subscription` after returning from checkout.

---

## 10. Referral (`/refer` page)

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/v1/referrals/me` | `{ code, share_url, signups, conversions, credit_paise }` |
| GET  | `/api/v1/referrals/history` | Paginated list of referred users + their conversion state. |

---

## 11. Webhooks (public, no auth header)

Mounted under `/api/public/webhooks/*`. Each handler verifies its provider signature before doing anything else.

| Path | Source | Purpose |
|---|---|---|
| `POST /api/public/webhooks/instagram` | Meta Graph API | Inbound comments / DMs / story replies → enqueue automation runs. Also handles GET verification handshake. |
| `POST /api/public/webhooks/stripe`    | Stripe | `checkout.session.completed`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted` → update workspace plan & invoices. |
| `POST /api/public/webhooks/razorpay`  | Razorpay (alt) | Same intent as Stripe. |

Webhook handlers MUST:
1. Read raw body, verify HMAC signature, reject with 401 if invalid.
2. Be idempotent — dedupe on provider event id.
3. Respond < 3s; offload heavy work to a background task / queue.

---

## 12. Background work

- **Queue:** start with Postgres-backed (e.g. `arq` / `dramatiq` + Redis, or `pgmq`).
- **Jobs:**
  - `automation.run` — execute a triggered automation against an IG event.
  - `instagram.refresh_token` — daily refresh of long-lived IG tokens.
  - `billing.sync_subscription` — reconcile with Stripe/Razorpay nightly.
  - `usage.rollup` — aggregate per-workspace usage counters.

---

## 13. Project layout (suggested)

```
app/
  main.py                  # FastAPI app, middleware, routers include
  config.py                # pydantic-settings, reads env
  deps.py                  # get_current_user, get_workspace, get_db
  db.py                    # async SQLAlchemy / asyncpg + Supabase admin client
  security.py              # JWT verify, signature verify helpers
  routers/
    auth.py
    workspaces.py
    instagram.py
    automations.py
    contacts.py
    products.py
    orders.py
    dashboard.py
    billing.py
    referrals.py
    webhooks.py            # mounted at /api/public/webhooks
  models/                  # SQLAlchemy models
  schemas/                 # Pydantic request/response models
  services/                # business logic (automation runner, billing, ig client)
  workers/                 # background job handlers
  tests/
```

### Required env vars
```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
DATABASE_URL=postgresql+asyncpg://...
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_REDIRECT_URI=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
FRONTEND_ORIGIN=
```

---

## 14. Status codes cheatsheet

| Code | When |
|---|---|
| 200 | Successful GET / PATCH |
| 201 | Resource created |
| 204 | Successful DELETE |
| 400 | Malformed request |
| 401 | Missing/invalid JWT |
| 403 | Authenticated but not allowed (wrong workspace, wrong role) |
| 404 | Resource not found *within accessible scope* |
| 409 | Conflict (e.g. `ig_already_connected`, duplicate invite) |
| 422 | Validation error from Pydantic, or domain validation (`automation_incomplete`) |
| 429 | Rate-limited |
| 5xx | Bug — log with correlation id, return `internal_error` |

---

## 15. OpenAPI

FastAPI generates `/openapi.json` and `/docs` automatically. Keep Pydantic schemas as the contract; the frontend will generate a typed client from this spec. Lock the spec per release tag.
