-- ============================================================
-- Vibe DM initial schema (per backend-plan/database-plan.md)
-- ============================================================

-- Extensions
create extension if not exists "pgcrypto";
create extension if not exists "citext";
create extension if not exists "pg_trgm";

-- ---------- Enums ----------
do $$ begin
  create type app_role as enum ('owner','admin','member');
exception when duplicate_object then null; end $$;

do $$ begin
  create type plan_tier as enum ('free','pro','business','enterprise');
exception when duplicate_object then null; end $$;

do $$ begin
  create type billing_cycle as enum ('monthly','yearly');
exception when duplicate_object then null; end $$;

do $$ begin
  create type subscription_status as enum ('active','trialing','past_due','canceled','incomplete');
exception when duplicate_object then null; end $$;

do $$ begin
  create type automation_status as enum ('draft','active','inactive');
exception when duplicate_object then null; end $$;

do $$ begin
  create type trigger_type as enum ('comment_post','dm','live_comment','story_reply','story_mention');
exception when duplicate_object then null; end $$;

do $$ begin
  create type action_type as enum ('send_dm','send_comment_reply','ask_for_email','ask_for_phone','send_link','tag_contact');
exception when duplicate_object then null; end $$;

do $$ begin
  create type order_status as enum ('pending','completed','cancelled','refunded');
exception when duplicate_object then null; end $$;

do $$ begin
  create type run_status as enum ('queued','running','succeeded','failed');
exception when duplicate_object then null; end $$;

-- ---------- Shared trigger fn ----------
create or replace function public.tg_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- ============================================================
-- Tables
-- ============================================================

-- users (profile mirror)
create table public.users (
  id         uuid primary key references auth.users(id) on delete cascade,
  email      citext unique not null,
  first_name text,
  last_name  text,
  phone      text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create trigger users_updated_at before update on public.users
  for each row execute function public.tg_set_updated_at();

-- workspaces
create table public.workspaces (
  id         uuid primary key default gen_random_uuid(),
  owner_id   uuid not null references public.users(id) on delete restrict,
  name       text not null check (length(name) between 1 and 80),
  avatar_url text,
  deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index workspaces_owner_idx on public.workspaces (owner_id) where deleted_at is null;
create trigger workspaces_updated_at before update on public.workspaces
  for each row execute function public.tg_set_updated_at();

-- workspace_members
create table public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id      uuid not null references public.users(id) on delete cascade,
  role         app_role not null default 'member',
  active       boolean not null default false,
  created_at   timestamptz not null default now(),
  primary key (workspace_id, user_id)
);
create index workspace_members_user_idx on public.workspace_members (user_id);
create unique index workspace_members_one_active_per_user
  on public.workspace_members (user_id) where active;

-- ---------- Helper functions (SECURITY DEFINER) ----------
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

-- instagram_connections
create table public.instagram_connections (
  workspace_id     uuid primary key references public.workspaces(id) on delete cascade,
  ig_user_id       text not null,
  ig_username      text not null,
  access_token_enc bytea not null,
  token_expires_at timestamptz,
  scopes           text[] not null default '{}',
  connected_at     timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create unique index instagram_connections_ig_user_id_uniq
  on public.instagram_connections (ig_user_id);
create trigger ig_conn_updated_at before update on public.instagram_connections
  for each row execute function public.tg_set_updated_at();

-- plans
create table public.plans (
  id            text primary key,
  tier          plan_tier not null,
  display_name  text not null,
  monthly_paise bigint not null check (monthly_paise >= 0),
  features      jsonb not null default '[]'::jsonb,
  is_popular    boolean not null default false,
  sort_order    int not null default 0
);
insert into public.plans (id, tier, display_name, monthly_paise, features, sort_order) values
  ('free',       'free',       'Free',       0,     '["Basic automations","Community support"]'::jsonb, 1),
  ('pro',        'pro',        'Pro',        9900,  '["Unlimited automations","Email support"]'::jsonb,  2),
  ('business',   'business',   'Business',   29900, '["Team seats","Priority support"]'::jsonb,          3),
  ('enterprise', 'enterprise', 'Enterprise', 39900, '["SSO","Dedicated success manager"]'::jsonb,        4);

-- subscriptions
create table public.subscriptions (
  id                       uuid primary key default gen_random_uuid(),
  workspace_id             uuid not null references public.workspaces(id) on delete cascade,
  plan_id                  text not null references public.plans(id),
  cycle                    billing_cycle not null default 'monthly',
  status                   subscription_status not null default 'active',
  current_period_start     timestamptz,
  current_period_end       timestamptz,
  cancel_at_period_end     boolean not null default false,
  provider                 text,
  provider_customer_id     text,
  provider_subscription_id text,
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);
create unique index subscriptions_one_live_per_ws
  on public.subscriptions (workspace_id) where status <> 'canceled';
create trigger subscriptions_updated_at before update on public.subscriptions
  for each row execute function public.tg_set_updated_at();

-- invoices
create table public.invoices (
  id                  uuid primary key default gen_random_uuid(),
  workspace_id        uuid not null references public.workspaces(id) on delete cascade,
  subscription_id     uuid references public.subscriptions(id) on delete set null,
  provider            text not null,
  provider_invoice_id text not null,
  amount_paise        bigint not null,
  currency            text not null default 'INR',
  status              text not null,
  hosted_invoice_url  text,
  pdf_url             text,
  issued_at           timestamptz not null default now(),
  unique (provider, provider_invoice_id)
);
create index invoices_ws_issued_idx on public.invoices (workspace_id, issued_at desc);

-- automations
create table public.automations (
  id             uuid primary key default gen_random_uuid(),
  workspace_id   uuid not null references public.workspaces(id) on delete cascade,
  name           text not null check (length(name) between 1 and 120),
  status         automation_status not null default 'draft',
  trigger_type   trigger_type,
  trigger_config jsonb not null default '{}'::jsonb,
  created_by     uuid references public.users(id) on delete set null,
  deleted_at     timestamptz,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index automations_ws_status_idx on public.automations (workspace_id, status) where deleted_at is null;
create trigger automations_updated_at before update on public.automations
  for each row execute function public.tg_set_updated_at();

-- automation_steps
create table public.automation_steps (
  id            uuid primary key default gen_random_uuid(),
  automation_id uuid not null references public.automations(id) on delete cascade,
  step_order    int not null check (step_order > 0),
  action_type   action_type not null,
  config        jsonb not null default '{}'::jsonb,
  created_at    timestamptz not null default now(),
  unique (automation_id, step_order)
);

-- contacts (must exist before automation_runs)
create table public.contacts (
  id                   uuid primary key default gen_random_uuid(),
  workspace_id         uuid not null references public.workspaces(id) on delete cascade,
  ig_user_id           text,
  ig_username          citext,
  name                 text,
  email                citext,
  phone                text,
  source_automation_id uuid references public.automations(id) on delete set null,
  tags                 text[] not null default '{}',
  notes                text,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  unique (workspace_id, ig_user_id)
);
create index contacts_ws_created_idx on public.contacts (workspace_id, created_at desc);
create index contacts_search_idx on public.contacts
  using gin ((coalesce(ig_username::text,'') || ' ' || coalesce(name,'') || ' ' || coalesce(email::text,'')) gin_trgm_ops);
create trigger contacts_updated_at before update on public.contacts
  for each row execute function public.tg_set_updated_at();

-- automation_runs
create table public.automation_runs (
  id            uuid primary key default gen_random_uuid(),
  workspace_id  uuid not null references public.workspaces(id) on delete cascade,
  automation_id uuid not null references public.automations(id) on delete cascade,
  contact_id    uuid references public.contacts(id) on delete set null,
  status        run_status not null default 'queued',
  trigger_event jsonb not null,
  step_trace    jsonb not null default '[]'::jsonb,
  error         text,
  started_at    timestamptz,
  finished_at   timestamptz,
  created_at    timestamptz not null default now()
);
create index automation_runs_ws_created_idx on public.automation_runs (workspace_id, created_at desc);
create index automation_runs_auto_created_idx on public.automation_runs (automation_id, created_at desc);

-- products
create table public.products (
  id           uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  name         text not null check (length(name) between 1 and 160),
  price_paise  bigint not null check (price_paise >= 0),
  link         text,
  image_url    text,
  description  text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index products_ws_created_idx on public.products (workspace_id, created_at desc);
create trigger products_updated_at before update on public.products
  for each row execute function public.tg_set_updated_at();

-- orders
create table public.orders (
  id           uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  contact_id   uuid not null references public.contacts(id) on delete restrict,
  product_id   uuid not null references public.products(id) on delete restrict,
  amount_paise bigint not null check (amount_paise >= 0),
  status       order_status not null default 'pending',
  placed_at    timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index orders_ws_placed_idx on public.orders (workspace_id, placed_at desc);
create index orders_ws_status_idx on public.orders (workspace_id, status);
create trigger orders_updated_at before update on public.orders
  for each row execute function public.tg_set_updated_at();

-- usage_counters
create table public.usage_counters (
  workspace_id  uuid not null references public.workspaces(id) on delete cascade,
  period_start  date not null,
  dm_count      int not null default 0,
  contact_count int not null default 0,
  updated_at    timestamptz not null default now(),
  primary key (workspace_id, period_start)
);

-- referrals
create table public.referrals (
  id               uuid primary key default gen_random_uuid(),
  referrer_user_id uuid not null references public.users(id) on delete cascade,
  code             text unique not null,
  referred_user_id uuid references public.users(id) on delete set null,
  converted_at     timestamptz,
  credit_paise     bigint not null default 0,
  created_at       timestamptz not null default now()
);
create index referrals_referrer_idx on public.referrals (referrer_user_id);

-- webhook_events
create table public.webhook_events (
  id           uuid primary key default gen_random_uuid(),
  provider     text not null,
  external_id  text not null,
  payload      jsonb not null,
  received_at  timestamptz not null default now(),
  processed_at timestamptz,
  error        text,
  unique (provider, external_id)
);

-- ============================================================
-- Lifecycle trigger: new workspace -> owner membership + free sub
-- ============================================================
create or replace function public.tg_workspace_after_insert()
returns trigger language plpgsql
security definer set search_path = public
as $$
begin
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

-- ============================================================
-- Row-Level Security
-- ============================================================
alter table public.users                 enable row level security;
alter table public.workspaces            enable row level security;
alter table public.workspace_members     enable row level security;
alter table public.instagram_connections enable row level security;
alter table public.plans                 enable row level security;
alter table public.subscriptions         enable row level security;
alter table public.invoices              enable row level security;
alter table public.automations           enable row level security;
alter table public.automation_steps      enable row level security;
alter table public.automation_runs       enable row level security;
alter table public.contacts              enable row level security;
alter table public.products              enable row level security;
alter table public.orders                enable row level security;
alter table public.usage_counters        enable row level security;
alter table public.referrals             enable row level security;
alter table public.webhook_events        enable row level security;

-- plans: anyone signed in can read
create policy plans_read_all on public.plans
  for select to authenticated using (true);

-- users: self only
create policy users_select_self on public.users
  for select to authenticated using (id = auth.uid());
create policy users_update_self on public.users
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- workspaces
create policy workspaces_select_member on public.workspaces
  for select to authenticated using (public.is_workspace_member(id));
create policy workspaces_update_admin on public.workspaces
  for update to authenticated
  using (public.has_workspace_role(id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(id, array['owner','admin']::app_role[]));
create policy workspaces_delete_owner on public.workspaces
  for delete to authenticated
  using (public.has_workspace_role(id, array['owner']::app_role[]));

-- workspace_members
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

-- Workspace-scoped resource template, applied per table
-- instagram_connections
create policy ig_conn_select on public.instagram_connections
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy ig_conn_insert on public.instagram_connections
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy ig_conn_update on public.instagram_connections
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy ig_conn_delete on public.instagram_connections
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- subscriptions
create policy subs_select on public.subscriptions
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy subs_insert on public.subscriptions
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy subs_update on public.subscriptions
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy subs_delete on public.subscriptions
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- invoices
create policy invoices_select on public.invoices
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy invoices_insert on public.invoices
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy invoices_update on public.invoices
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy invoices_delete on public.invoices
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- automations
create policy automations_select on public.automations
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy automations_insert on public.automations
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy automations_update on public.automations
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy automations_delete on public.automations
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- automation_steps (joins through parent automation)
create policy steps_select on public.automation_steps
  for select to authenticated using (
    exists (
      select 1 from public.automations a
      where a.id = automation_id and public.is_workspace_member(a.workspace_id)
    )
  );
create policy steps_insert on public.automation_steps
  for insert to authenticated with check (
    exists (
      select 1 from public.automations a
      where a.id = automation_id
        and public.has_workspace_role(a.workspace_id, array['owner','admin']::app_role[])
    )
  );
create policy steps_update on public.automation_steps
  for update to authenticated
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
create policy steps_delete on public.automation_steps
  for delete to authenticated using (
    exists (
      select 1 from public.automations a
      where a.id = automation_id
        and public.has_workspace_role(a.workspace_id, array['owner','admin']::app_role[])
    )
  );

-- automation_runs
create policy runs_select on public.automation_runs
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy runs_insert on public.automation_runs
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy runs_update on public.automation_runs
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy runs_delete on public.automation_runs
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- contacts
create policy contacts_select on public.contacts
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy contacts_insert on public.contacts
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy contacts_update on public.contacts
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy contacts_delete on public.contacts
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- products
create policy products_select on public.products
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy products_insert on public.products
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy products_update on public.products
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy products_delete on public.products
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- orders
create policy orders_select on public.orders
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy orders_insert on public.orders
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy orders_update on public.orders
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy orders_delete on public.orders
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- usage_counters
create policy usage_select on public.usage_counters
  for select to authenticated using (public.is_workspace_member(workspace_id));
create policy usage_insert on public.usage_counters
  for insert to authenticated
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy usage_update on public.usage_counters
  for update to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]))
  with check (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));
create policy usage_delete on public.usage_counters
  for delete to authenticated
  using (public.has_workspace_role(workspace_id, array['owner','admin']::app_role[]));

-- referrals: self only
create policy referrals_select_self on public.referrals
  for select to authenticated using (referrer_user_id = auth.uid());

-- webhook_events: no authenticated policies; service role only.
