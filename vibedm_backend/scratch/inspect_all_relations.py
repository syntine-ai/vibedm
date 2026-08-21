import asyncio
import sys

from sqlalchemy import text

from app.db import get_sessionmaker

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Workspaces
        res = await session.execute(text("select id, name, created_at from public.workspaces"))
        workspaces = res.mappings().all()
        print("=== WORKSPACES ===")
        for w in workspaces:
            print(f"ID: {w['id']}, Name: '{w['name']}', Created: {w['created_at']}")
        print("=" * 60)

        # Instagram Connections
        res = await session.execute(text("select workspace_id, ig_user_id, ig_username, connection_type from public.instagram_connections"))
        conns = res.mappings().all()
        print("=== INSTAGRAM CONNECTIONS ===")
        for c in conns:
            print(f"Workspace ID: {c['workspace_id']}, IG User ID: {c['ig_user_id']}, Username: @{c['ig_username']}, Type: {c.get('connection_type')}")
        print("=" * 60)

        # Automations
        res = await session.execute(text("select id, workspace_id, name, status, trigger_type, trigger_config from public.automations"))
        autos = res.mappings().all()
        print("=== AUTOMATIONS ===")
        for a in autos:
            print(f"ID: {a['id']}, Workspace ID: {a['workspace_id']}, Name: '{a['name']}', Status: {a['status']}, Trigger: {a['trigger_type']}")
        print("=" * 60)

        # Latest background jobs
        res = await session.execute(text("select id, job_type, workspace_id, status, last_error, run_at from public.background_jobs order by created_at desc limit 10"))
        jobs = res.mappings().all()
        print("=== RECENT BACKGROUND JOBS ===")
        for j in jobs:
            print(f"Job ID: {j['id']}, Type: {j['job_type']}, Workspace: {j['workspace_id']}, Status: {j['status']}, Error: {j['last_error']}, RunAt: {j['run_at']}")
        print("=" * 60)

        # Recent runs
        res = await session.execute(text("select id, workspace_id, automation_id, status, error, created_at from public.automation_runs order by created_at desc limit 10"))
        runs = res.mappings().all()
        print("=== RECENT AUTOMATION RUNS ===")
        for r in runs:
            print(f"Run ID: {r['id']}, Workspace: {r['workspace_id']}, Automation: {r['automation_id']}, Status: {r['status']}, Error: {r['error']}, Created: {r['created_at']}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
