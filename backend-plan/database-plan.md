# Backend Database Plan — Vibe DM (Supabase Postgres)

Companion to `api-plan.md`. Defines tables, relationships, indexes, enums, and Row-Level Security (RLS) for the Vibe DM product. Aligned with:
- `doc/onboarding-workspace-flow.md` — every user gets a workspace via the IG connect flow
- `doc/billing.md` — per-workspace plan, monthly/yearly, INR

---

## 1. Principles

1. **All business data is workspace-scoped.** Every domain table carries `workspace_id` and is filtered through it in RLS.
2. **Multi-tenancy via membership.** `workspace_members` is the join table between `auth.users` and `workspaces`. Roles live here, never on `auth.users` or `users`.
3. **RLS always on.** No table containing user data ships without `enable row level security` + policies. The FastAPI service uses the service role key and bypasses RLS, so RLS exists to (a) defend the Supabase JS path the frontend uses for auth, and (b) defend against future direct PostgREST exposure.
4. **No recursive policies.** Membership checks go through `SECURITY DEFINER` helper functions so policies never query the table they're attached to.
5. **Money in paise** (`bigint`). **Times in `timestamptz`**. **IDs are `uuid` default `gen_random_uuid()`**.
6. **Soft delete** via `deleted_at timestamptz` only where it's needed (workspaces, automations). Everything else hard-deletes.
7. **Audit columns** on every table: `created_at`, `updated_at` (trigger keeps `updated_at` fresh).
8. **Enums via Postgres `create type`** so values are validated at the DB layer.

---

## 2. Extensions

```sql
create extension if not exists "pgcrypto";   -- gen_random_uuid()
create extension if not exists "citext";     -- case-insensitive emails / usernames
create extension if not exists "pg_trgm";    -- search on contacts
```

---

## 3. Enums

```sql
create type app_role            as enum ('owner', 'admin', 'member');
create type plan_tier           as enum ('free', 'pro', 'business', 'enterprise');
create type billing_cycle       as enum ('monthly', 'yearly');
create type subscription_status as enum ('active', 'trialing', 'past_due', 'canceled', 'incomplete');
create type automation_status   as enum ('draft', 'active', 'inactive');
create type trigger_type        as enum ('comment_post', 'dm', 'live_comment', 'story_reply', 'story_mention');
create type action_type         as enum ('send_dm', 'send_comment_reply', 'ask_for_email', 'ask_for_phone', 'send_link', 'tag_contact');
create type order_status        as enum ('pending', 'completed', 'cancelled', 'refunded');
create type run_status          as enum ('queued', 'running', 'succeeded', 'failed');
```

---

## 4. Helper functions (SECURITY DEFINER)

These avoid RLS recursion. They run as the function owner and bypass the caller's RLS — they only read membership.

```sql
-- Is the caller a member of this workspace?
create or replace function public.is_workspace_member(_workspace_id uuid)
returns boolean
language sql stable security definer
set search_path = public
as $$
  select exists (
    select 1 from public.workspace_members
    where workspace_id = _workspace_id and user_id = auth.uid()
  );
$$;

-- Does the caller hold one of the given roles in this workspace?
create or replace function public.has_workspace_role(_workspace_id uuid, _roles app_role[])
returns boolean
language sql stable security definer
set search_path = public
as $$
  select exists (
    select 1 from public.workspace_members
    where workspace_id = _workspace_id
      and user_id = auth.uid()
      and role = any(_roles)
  );
$$;

-- Generic updated_at trigger
create or replace function public.tg_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;
```

> **Why functions, not inline subqueries?** A policy on `workspace_members` that selects from `workspace_members` causes infinite recursion. The `security definer` function breaks the loop.

---

## 5. Tables

### 5.1 `users` (profile mirror of `auth.users`)

```sql
create table public.users (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       citext unique not null,
  first_name  text,
  last_name   text,
  phone       text,
  avatar_url  text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create trigger users_updated_at before update on public.users
  for each row execute function public.tg_set_updated_at();
```

Populated by `POST /auth/sync` from Supabase JWT claims. **Never** stores roles or admin flags.

### 5.2 `workspaces`

```sql
create table public.workspaces (
  id            uuid primary key default gen_random_uuid(),
  owner_id     uuid not null references public.users(id) on delete restrict,
  name          text not null check (length(name) between 1 and 80),
  avatar_url    text,
  deleted_at    timestamptz,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index on public.workspaces (owner_id) where deleted_at is null;
create trigger workspaces_updated_at before update on public.workspaces
  for each row execute function public.tg_set_updated_at();
```

### 5.3 `workspace_members`

```sql
create table public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id      uuid not null references public.users(id) on delete cascade,
  role         app_role not null default 'member',
  active       boolean not null default false,        -- the user's currently-selected workspace
  created_at   timestamptz not null default now(),
  primary key (workspace_id, user_id)
);
create index on public.workspace_members (user_id);
-- A user has at most one active workspace
create unique index workspace_members_one_active_per_user
  on public.workspace_members (user_id) where active;
```

### 5.4 `instagram_connections` (one per workspace)

```sql
create table public.instagram_connections (
  workspace_id      uuid primary key references public.workspaces(id) on delete cascade,
  ig_user_id        text not null,
  ig_username       text not null,
  access_token_enc  bytea not null,                  -- encrypted at rest (pgcrypto or app-level)
  token_expires_at  timestamptz,
  scopes            text[] not null default '{}',
  connected_at      timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
-- The same IG account can't be connected to two workspaces owned by the same user.
create unique index instagram_connections_ig_user_id_uniq
  on public.instagram_connections (ig_user_id);
create trigger ig_conn_updated_at before update on public.instagram_connections
  for each row execute function public.tg_set_updated_at();
```

### 5.5 `plans` (seeded reference data)

```sql
create table public.plans (
  id              text primary key,                   -- 'free' | 'pro' | 'business' | 'enterprise'
  tier            plan_tier not null,
  display_name    text not null,
  monthly_paise   bigint not null check (monthly_paise >= 0),
  features        jsonb  not null default '[]'::jsonb,
  is_popular      boolean not null default false,
  sort_order      int    not null default 0
);
-- Seed
insert into public.plans (id, tier, display_name, monthly_paise, features, sort_order) values
  ('free',       'free',       'Free',       0,     '["Basic automations","Community support"]', 1),
  ('pro',        'pro',        'Pro',        9900,  '["Unlimited automations","Email support"]',  2),
  ('business',   'business',   'Business',   29900, '["Team seats","Priority support"]',          3),
  ('enterprise', 'enterprise', 'Enterprise', 39900, '["SSO","Dedicated success manager"]',        4);
```

Yearly price is computed in code: `monthly_paise * 12 * 0.8`. Don't store it.

### 5.6 `subscriptions` (one active row per workspace)

```sql
create table public.subscriptions (
  id                       uuid primary key default gen_random_uuid(),
  workspace_id             uuid not null references public.workspaces(id) on delete cascade,
  plan_id                  text not null references public.plans(id),
  cycle                    billing_cycle not null default 'monthly',
  status                   subscription_status not null default 'active',
  current_period_start     timestamptz,
  current_period_end       timestamptz,
  cancel_at_period_end     boolean not null default false,
  provider                 text,                          -- 'stripe' | 'razorpay' | null (free)
  provider_customer_id     text,
  provider_subscription_id text,
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);
-- One live (non-canceled) subscription per workspace
create unique index subscriptions_one_live_per_ws
  on public.subscriptions (workspace_id)
  where status <> 'canceled';
create trigger subscriptions_updated_at before update on public.subscriptions
  for each row execute function public.tg_set_updated_at();
```

New workspaces get a `free` subscription row inserted by trigger (see §7).

### 5.7 `invoices`

```sql
create table public.invoices (
  id                   uuid primary key default gen_random_uuid(),
  workspace_id         uuid not null references public.workspaces(id) on delete cascade,
  subscription_id      uuid references public.subscriptions(id) on delete set null,
  provider             text not null,
  provider_invoice_id  text not null,
  amount_paise         bigint not null,
  currency             text not null default 'INR',
  status               text not null,                   -- 'paid' | 'open' | 'void' | 'uncollectible'
  hosted_invoice_url   text,
  pdf_url              text,
  issued_at            timestamptz not null default now(),
  unique (provider, provider_invoice_id)
);
create index on public.invoices (workspace_id, issued_at desc);
```

### 5.8 `automations`

```sql
create table public.automations (
  id              uuid primary key default gen_random_uuid(),
  workspace_id    uuid not null references public.workspaces(id) on delete cascade,
  name            text not null check (length(name) between 1 and 120),
  status          automation_status not null default 'draft',
  trigger_type    trigger_type,
  trigger_config  jsonb not null default '{}'::jsonb,
  created_by      uuid references public.users(id) on delete set null,
  deleted_at      timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index on public.automations (workspace_id, status) where deleted_at is null;
create trigger automations_updated_at before update on public.automations
  for each row execute function public.tg_set_updated_at();
```

### 5.9 `automation_steps`

```sql
create table public.automation_steps (
  id             uuid primary key default gen_random_uuid(),
  automation_id  uuid not null references public.automations(id) on delete cascade,
  step_order     int  not null check (step_order > 0),
  action_type    action_type not null,
  config         jsonb not null default '{}'::jsonb,
  created_at     timestamptz not null default now(),
  unique (automation_id, step_order)
);
```

### 5.10 `automation_runs`

```sql
create table public.automation_runs (
  id              uuid primary key default gen_random_uuid(),
  workspace_id    uuid not null references public.workspaces(id) on delete cascade,
  automation_id   uuid not null references public.automations(id) on delete cascade,
  contact_id      uuid references public.contacts(id) on delete set null,
  status          run_status not null default 'queued',
  trigger_event   jsonb not null,                      -- raw IG event snapshot
  step_trace      jsonb not null default '[]'::jsonb,  -- [{step_order, action_type, ok, error?}]
  error           text,
  started_at      timestamptz,
  finished_at     timestamptz,
  created_at      timestamptz not null default now()
);
create index on public.automation_runs (workspace_id, created_at desc);
create index on public.automation_runs (automation_id, created_at desc);
```

### 5.11 `contacts`

```sql
create table public.contacts (
  id                    uuid primary key default gen_random_uuid(),
  workspace_id          uuid not null references public.workspaces(id) on delete cascade,
  ig_user_id            text,                                   -- IG user id (stable)
  ig_username           citext,
  name                  text,
  email                 citext,
  phone                 text,
  source_automation_id  uuid references public.automations(id) on delete set null,
  tags                  text[] not null default '{}',
  notes                 text,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),
  unique (workspace_id, ig_user_id)
);
create index on public.contacts (workspace_id, created_at desc);
create index contacts_search_idx on public.contacts
  using gin ((coalesce(ig_username::text,'') || ' ' || coalesce(name,'') || ' ' || coalesce(email::text,'')) gin_trgm_ops);
create trigger contacts_updated_at before update on public.contacts
  for each row execute function public.tg_set_updated_at();
```

### 5.12 `products`

```sql
create table public.products (
  id            uuid primary key default gen_random_uuid(),
  workspace_id  uuid not null references public.workspaces(id) on delete cascade,
  name          text not null check (length(name) between 1 and 160),
  price_paise   bigint not null check (price_paise >= 0),
  link          text,
  image_url     text,
  description   text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index on public.products (workspace_id, created_at desc);
create trigger products_updated_at before update on public.products
  for each row execute function public.tg_set_updated_at();
```

### 5.13 `orders`

```sql
create table public.orders (
  id            uuid primary key default gen_random_uuid(),
  workspace_id  uuid not null references public.workspaces(id) on delete cascade,
  contact_id    uuid not null references public.contacts(id) on delete restrict,
  product_id    uuid not null references public.products(id) on delete restrict,
  amount_paise  bigint not null check (amount_paise >= 0),
  status        order_status not null default 'pending',
  placed_at     timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index on public.orders (workspace_id, placed_at desc);
create index on public.orders (workspace_id, status);
create trigger orders_updated_at before update on public.orders
  for each row execute function public.tg_set_updated_at();
```

### 5.14 `usage_counters` (rolled up daily for dashboard + sidebar meters)

```sql
create table public.usage_counters (
  workspace_id   uuid not null references public.workspaces(id) on delete cascade,
  period_start   date not null,                       -- first day of billing month
  dm_count       int  not null default 0,
  contact_count  int  not null default 0,
  updated_at     timestamptz not null default now(),
  primary key (workspace_id, period_start)
);
```

### 5.15 `referrals`

```sql
create table public.referrals (
  id                 uuid primary key default gen_random_uuid(),
  referrer_user_id   uuid not null references public.users(id) on delete cascade,
  code               text unique not null,
  referred_user_id   uuid references public.users(id) on delete set null,
  converted_at       timestamptz,
  credit_paise       bigint not null default 0,
  created_at         timestamptz not null default now()
);
create index on public.referrals (referrer_user_id);
```

### 5.16 `webhook_events` (idempotency log)

```sql
create table public.webhook_events (
  id            uuid primary key default gen_random_uuid(),
  provider      text not null,                       -- 'stripe' | 'razorpay' | 'instagram'
  external_id   text not null,
  payload       jsonb not null,
  received_at   timestamptz not null default now(),
  processed_at  timestamptz,
  error         text,
  unique (provider, external_id)
);
```

---

## 6. ER overview

```text
auth.users ──1:1── users
users ──1:N── workspace_members ──N:1── workspaces
workspaces ──1:1── instagram_connections
workspaces ──1:1── subscriptions ──N:1── plans
workspaces ──1:N── invoices
workspaces ──1:N── automations ──1:N── automation_steps
workspaces ──1:N── automation_runs ──N:1── automations
                                      └─N:1── contacts
workspaces ──1:N── contacts
workspaces ──1:N── products
workspaces ──1:N── orders ──N:1── contacts, products
workspaces ──1:N── usage_counters
users ──1:N── referrals
```

---

## 7. Triggers / lifecycle

```sql
-- When a workspace is created, owner becomes an active 'owner' member and gets a Free subscription.
create or replace function public.tg_workspace_after_insert()
returns trigger language plpgsql as $$
begin
  -- Demote any other active workspace for this owner
  update public.workspace_members
     set active = false
   where user_id = new.owner_id and active;

  insert into public.workspace_members (workspace_id, user_id, role, active)
  values (new.id, new.owner_id, 'owner', true);

  insert into public.subscriptions (workspace_id, plan_id, cycle, status)
  values (new.id, 'free', 'monthly', 'active');

  return new;
end $$;

create trigger workspaces_after_insert
  after insert on public.workspaces
  for each row execute function public.tg_workspace_after_insert();
```

---

## 8. Row-Level Security

Enable RLS on every public table:

```sql
alter table public.users                   enable row level security;
alter table public.workspaces              enable row level security;
alter table public.workspace_members       enable row level security;
alter table public.instagram_connections   enable row level security;
alter table public.subscriptions           enable row level security;
alter table public.invoices                enable row level security;
alter table public.automations             enable row level security;
alter table public.automation_steps        enable row level security;
alter table public.automation_runs         enable row level security;
alter table public.contacts                enable row level security;
alter table public.products                enable row level security;
alter table public.orders                  enable row level security;
alter table public.usage_counters          enable row level security;
alter table public.referrals               enable row level security;
alter table public.plans                   enable row level security;
-- webhook_events: no RLS policies; only the service role touches it.
alter table public.webhook_events          enable row level security;
```

### 8.1 `plans` — public read

```sql
create policy plans_read_all on public.plans
  for select to authenticated using (true);
```

### 8.2 `users` — self-only

```sql
create policy users_select_self on public.users
  for select to authenticated using (id = auth.uid());
create policy users_update_self on public.users
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());
-- Inserts done by FastAPI via service role (POST /auth/sync); no insert policy needed.
```

### 8.3 `workspaces`

```sql
create policy workspaces_select_member on public.workspaces
  for select to authenticated using (public.is_workspace_member(id));

create policy workspaces_update_admin on public.workspaces
  for update to authenticated
  using (public.has_workspace_role(id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(id, array['owner','admin']::app_role[]));

create policy workspaces_delete_owner on public.workspaces
  for delete to authenticated
  using (public.has_workspace_role(id, array['owner']::app_role[]));
-- Insert handled by FastAPI service role after IG connect.
```

### 8.4 `workspace_members`

```sql
create policy wm_select_self_or_admin on public.workspace_members
  for select to authenticated
  using (
    user_id = auth.uid()
    or public.has_workspace_role(workspace_id, array['owner','admin']::app_role[])
  );

create policy wm_insert_admin on public.workspace_members
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

create policy wm_update_admin on public.workspace_members
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

create policy wm_delete_admin_or_self on public.workspace_members
  for delete to authenticated
  using (
    user_id = auth.uid()
    or public.has_workspace_role(workspace_id, array['owner','admin']::app_role[])
  );
```

### 8.5 Workspace-scoped resources (one pattern, applied to each)

Apply this template to **instagram_connections, subscriptions, invoices, automations, automation_steps, automation_runs, contacts, products, orders, usage_counters**.

Read = any member. Write = `owner` or `admin`. `automation_steps` derives its `workspace_id` via its parent `automation`.

```sql
-- READ (members)
create policy <t>_select on public.<t>
  for select to authenticated
  using (public.is_workspace_member(workspace_id));

-- WRITE (owner/admin)
create policy <t>_insert on public.<t>
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

create policy <t>_update on public.<t>
  for update to authenticated
  using       (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check  (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

create policy <t>_delete on public.<t>
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
```

`automation_steps` needs the join because it has no `workspace_id` column:

```sql
create policy steps_select on public.automation_steps
  for select to authenticated using (
    exists (
      select 1 from public.automations a
      where a.id = automation_id and public.is_workspace_member(a.workspace_id)
    )
  );
create policy steps_write on public.automation_steps
  for all to authenticated
  using (
    exists (
      select 1 from public.automations a
      where a.id = automation_id
        and public.has_workspace_role(a.workspace_id, array['owner','admin']::app_role[])
    )
  )
  with check (
    exists (
      select 1 from public.automations a
      where a.id = automation_id
        and public.has_workspace_role(a.workspace_id, array['owner','admin']::app_role[])
    )
  );
```

### 8.6 `referrals` — self-only

```sql
create policy referrals_select_self on public.referrals
  for select to authenticated using (referrer_user_id = auth.uid());
```

### 8.7 `webhook_events`

No policies. Only the FastAPI service role (which bypasses RLS) reads/writes this table.

---

## 9. Indexes summary

Beyond the inline indexes above:
- `workspace_members (user_id)` — sidebar workspace list.
- `automations (workspace_id, status) where deleted_at is null` — list page.
- `automation_runs (workspace_id, created_at desc)` — dashboard activity feed.
- `contacts (workspace_id, created_at desc)` + trigram GIN — list & search.
- `orders (workspace_id, placed_at desc)` and `(workspace_id, status)`.
- `invoices (workspace_id, issued_at desc)` — billing history.

---

## 10. Migrations

- Use a single tool (Alembic *or* Supabase CLI migrations). Recommended: Supabase CLI so migrations live in the Supabase project and apply identically to local + prod.
- One migration per logical change; never mutate an applied migration.
- Order:
  1. Extensions
  2. Enums + helper functions + `tg_set_updated_at`
  3. `users`, `workspaces`, `workspace_members`
  4. `instagram_connections`, `plans` (+ seed), `subscriptions`, `invoices`
  5. Automations + steps + runs
  6. Contacts, products, orders, usage_counters
  7. Referrals, webhook_events
  8. Triggers (`tg_workspace_after_insert`)
  9. RLS enable + policies (last, so all referenced tables exist)

---

## 11. Seed / test data

Provide a seed script (`scripts/seed_dev.sql` or Python) that:
- Creates a test user in `auth.users` (via Supabase admin API).
- Inserts a workspace; trigger handles membership + free subscription.
- Inserts 3 automations, 5 contacts, 3 products, 3 orders matching `src/lib/mock-data.ts`.

---

## 12. Future considerations (not v1)

- Partition `automation_runs` and `webhook_events` by month once volume warrants.
- Move encrypted IG tokens out into Supabase Vault (`vault.secrets`) instead of `bytea`.
- Add `audit_log` table if compliance ever requires per-record change history.
- Add `feature_flags` table keyed by workspace if plan-based gating gets complex.
