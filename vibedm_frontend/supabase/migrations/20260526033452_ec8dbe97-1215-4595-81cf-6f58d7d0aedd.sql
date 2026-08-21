-- Fix search_path on timestamp helper
create or replace function public.tg_set_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- Lock down SECURITY DEFINER helpers: only authenticated may execute
revoke execute on function public.is_workspace_member(uuid) from public, anon;
revoke execute on function public.has_workspace_role(uuid, app_role[]) from public, anon;
revoke execute on function public.tg_workspace_after_insert() from public, anon, authenticated;
revoke execute on function public.tg_set_updated_at() from public, anon, authenticated;
grant execute on function public.is_workspace_member(uuid) to authenticated;
grant execute on function public.has_workspace_role(uuid, app_role[]) to authenticated;

-- webhook_events: explicit deny-all policy so signed-in users cannot read/write.
-- The backend uses the service role which bypasses RLS.
create policy webhook_events_no_access on public.webhook_events
  for all to authenticated using (false) with check (false);

-- Move extensions out of public into a dedicated schema
create schema if not exists extensions;
grant usage on schema extensions to public;
alter extension citext  set schema extensions;
alter extension pg_trgm set schema extensions;
