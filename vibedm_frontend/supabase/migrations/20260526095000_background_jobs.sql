-- ============================================================
-- Production background jobs queue
-- ============================================================

do $$ begin
  create type job_status as enum ('queued', 'running', 'succeeded', 'failed', 'dead');
exception when duplicate_object then null; end $$;

create table public.background_jobs (
  id uuid primary key default gen_random_uuid(),

  job_type text not null check (length(job_type) between 1 and 120),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,

  status job_status not null default 'queued',
  priority int not null default 0,

  attempts int not null default 0 check (attempts >= 0),
  max_attempts int not null default 5 check (max_attempts > 0),

  run_at timestamptz not null default now(),
  locked_at timestamptz,
  locked_by text,

  last_error text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

create trigger background_jobs_updated_at
  before update on public.background_jobs
  for each row execute function public.tg_set_updated_at();

create index background_jobs_ready_idx
  on public.background_jobs (status, run_at, priority desc, created_at asc)
  where status = 'queued';

create index background_jobs_running_idx
  on public.background_jobs (status, locked_at)
  where status = 'running';

create index background_jobs_workspace_idx
  on public.background_jobs (workspace_id, created_at desc);

create index background_jobs_type_status_idx
  on public.background_jobs (job_type, status, created_at desc);

-- Atomically claim one ready job. Safe for many workers via SKIP LOCKED.
create or replace function public.claim_background_job(
  _worker_id text,
  _job_types text[] default null
)
returns setof public.background_jobs
language plpgsql
security definer
set search_path = public
as $$
begin
  return query
  update public.background_jobs
     set status = 'running',
         attempts = attempts + 1,
         locked_at = now(),
         locked_by = _worker_id,
         updated_at = now()
   where id = (
     select id
       from public.background_jobs
      where status = 'queued'
        and run_at <= now()
        and (_job_types is null or job_type = any(_job_types))
      order by priority desc, run_at asc, created_at asc
      for update skip locked
      limit 1
   )
  returning *;
end $$;

-- Recover jobs abandoned by crashed workers.
create or replace function public.requeue_stale_background_jobs(
  _lock_timeout interval default interval '15 minutes'
)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  _count integer;
begin
  update public.background_jobs
     set status = case
           when attempts >= max_attempts then 'dead'::job_status
           else 'queued'::job_status
         end,
         run_at = case
           when attempts >= max_attempts then run_at
           else now() + make_interval(secs => least(3600, (power(2, attempts)::int * 30)))
         end,
         locked_at = null,
         locked_by = null,
         last_error = coalesce(last_error, 'Worker lock expired'),
         completed_at = case
           when attempts >= max_attempts then now()
           else null
         end,
         updated_at = now()
   where status = 'running'
     and locked_at < now() - _lock_timeout;

  get diagnostics _count = row_count;
  return _count;
end $$;

-- ============================================================
-- RLS and privileges
-- ============================================================

alter table public.background_jobs enable row level security;

revoke all on public.background_jobs from anon, authenticated;
grant select, insert, update, delete on public.background_jobs to service_role;

create policy background_jobs_no_client_access
  on public.background_jobs
  for all
  to anon, authenticated
  using (false)
  with check (false);

create policy background_jobs_service_role_access
  on public.background_jobs
  for all
  to service_role
  using (true)
  with check (true);

revoke execute on function public.claim_background_job(text, text[]) from public, anon, authenticated;
revoke execute on function public.requeue_stale_background_jobs(interval) from public, anon, authenticated;

grant execute on function public.claim_background_job(text, text[]) to service_role;
grant execute on function public.requeue_stale_background_jobs(interval) to service_role;
