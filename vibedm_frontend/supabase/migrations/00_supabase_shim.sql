-- ============================================================
-- Supabase Compatibility Shim for Standard PostgreSQL
-- Allows running Supabase migrations on a standard Postgres DB.
-- ============================================================

-- Create auth schema if it does not exist
CREATE SCHEMA IF NOT EXISTS auth;

-- Create auth.users profile table if not exists (referenced by public.users)
CREATE TABLE IF NOT EXISTS auth.users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE
);

-- Define auth.uid() only if it does not exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc p 
    JOIN pg_namespace n ON p.pronamespace = n.oid 
    WHERE n.nspname = 'auth' AND p.proname = 'uid'
  ) THEN
    EXECUTE 'CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql AS $fn$ SELECT null::uuid $fn$';
  END IF;
END
$$;

-- Create default Supabase roles safely if they do not exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon;
  END IF;
END
$$;
