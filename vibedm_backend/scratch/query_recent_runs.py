import asyncio
import json
import sys
from app.db import get_sessionmaker
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Fetch runs for the automation created recently
        runs_res = await session.execute(
            text("select id, status, error, trigger_event, step_trace, created_at, finished_at from public.automation_runs where automation_id = '5fb9575f-870e-49f3-ae1c-3ea9059e73fa' and created_at > '2026-05-29 07:00:00+00' order by created_at desc limit 10")
        )
        runs = runs_res.mappings().all()
        print("=== LATEST RUNS SINCE UPDATES ===")
        for r in runs:
            # Parse trigger event
            trigger = r["trigger_event"]
            if isinstance(trigger, str):
                try:
                    trigger = json.loads(trigger)
                except Exception:
                    pass
                    
            # Parse step trace
            trace = r["step_trace"]
            if isinstance(trace, str):
                try:
                    trace = json.loads(trace)
                except Exception:
                    pass
            
            print(f"Run ID: {r['id']}, Status: {r['status']}, Created: {r['created_at']}, Finished: {r['finished_at']}")
            print(f"  Error: {r['error']}")
            # print trigger summary
            if isinstance(trigger, dict):
                is_followup = trigger.get("is_followup") or trigger.get("payload", {}).get("is_followup")
                print(f"  Trigger: is_followup={is_followup}, sender={trigger.get('sender', {}).get('id') or trigger.get('sender_id')}")
            else:
                print(f"  Trigger: {trigger}")
            print(f"  Step Trace: {json.dumps(trace, ensure_ascii=False)}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
