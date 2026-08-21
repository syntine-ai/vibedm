import asyncio
import json
import sys

from sqlalchemy import text

from app.db import get_sessionmaker

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    run_ids = ["e5e0cab5-2bbe-4569-8f29-915d11776c7d", "f3e67c3c-1a1c-40d6-80c7-335c22a57835"]
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        for r_id in run_ids:
            res = await session.execute(
                text("select id, workspace_id, automation_id, contact_id, status, trigger_event, step_trace, error, created_at from public.automation_runs where id = :r_id"),
                {"r_id": r_id}
            )
            r = res.mappings().first()
            if not r:
                print(f"Run {r_id} not found!")
                continue
            
            print(f"=== RUN: {r['id']} ===")
            print(f"Workspace: {r['workspace_id']}")
            print(f"Automation ID: {r['automation_id']}")
            print(f"Contact ID: {r['contact_id']}")
            print(f"Status: {r['status']}")
            print(f"Created At: {r['created_at']}")
            print(f"Error: {r['error']}")
            
            trigger = r["trigger_event"]
            if isinstance(trigger, str):
                try: trigger = json.loads(trigger)
                except Exception: pass
            print(f"Trigger Event: {json.dumps(trigger, indent=2)}")
            
            trace = r["step_trace"]
            if isinstance(trace, str):
                try: trace = json.loads(trace)
                except Exception: pass
            print(f"Step Trace: {json.dumps(trace, indent=2)}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
