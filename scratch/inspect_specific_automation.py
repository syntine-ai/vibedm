import asyncio
import json
import sys
from app.db import get_sessionmaker
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    target_id = "5fbc9c4c-ddd9-4499-a771-927d49f314e6"
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # 1. Fetch the automation detail
        auto_res = await session.execute(
            text("select id, workspace_id, name, status, trigger_type, trigger_config, created_at from public.automations where id = :target_id"),
            {"target_id": target_id}
        )
        auto = auto_res.mappings().first()
        if not auto:
            print(f"Automation {target_id} not found!")
            # Let's search for any recent automations
            recent_autos_res = await session.execute(
                text("select id, workspace_id, name, status, trigger_type, trigger_config, created_at from public.automations order by created_at desc limit 5")
            )
            print("Recent automations:")
            for a in recent_autos_res.mappings().all():
                print(f"  ID: {a['id']}, Name: '{a['name']}', Status: {a['status']}, Trigger: {a['trigger_type']}, Created: {a['created_at']}")
            return

        print("=== AUTOMATION DETAIL ===")
        print(f"ID: {auto['id']}")
        print(f"Workspace ID: {auto['workspace_id']}")
        print(f"Name: {auto['name']}")
        print(f"Status: {auto['status']}")
        print(f"Trigger Type: {auto['trigger_type']}")
        print(f"Trigger Config: {json.dumps(auto['trigger_config'], indent=2)}")
        print(f"Created At: {auto['created_at']}")
        print("=" * 50)

        # 2. Fetch the automation steps
        steps_res = await session.execute(
            text("select id, step_order, action_type, config from public.automation_steps where automation_id = :target_id order by step_order"),
            {"target_id": target_id}
        )
        print("=== AUTOMATION STEPS ===")
        for s in steps_res.mappings().all():
            print(f"Step Order: {s['step_order']}, ID: {s['id']}, Type: {s['action_type']}, Config: {json.dumps(s['config'])}")
        print("=" * 50)

        # 3. Fetch runs for this automation
        runs_res = await session.execute(
            text("select id, contact_id, status, error, trigger_event, step_trace, created_at from public.automation_runs where automation_id = :target_id order by created_at desc limit 10"),
            {"target_id": target_id}
        )
        runs = runs_res.mappings().all()
        print("=== LATEST RUNS FOR AUTOMATION ===")
        print(f"Total runs found: {len(runs)}")
        for r in runs:
            # Parse trigger event
            trigger = r["trigger_event"]
            if isinstance(trigger, str):
                try: trigger = json.loads(trigger)
                except Exception: pass
            # Parse step trace
            trace = r["step_trace"]
            if isinstance(trace, str):
                try: trace = json.loads(trace)
                except Exception: pass
            
            print(f"Run ID: {r['id']}, Contact ID: {r['contact_id']}, Status: {r['status']}, Created: {r['created_at']}")
            print(f"  Error: {r['error']}")
            if isinstance(trigger, dict):
                is_followup = trigger.get("is_followup") or trigger.get("payload", {}).get("is_followup")
                print(f"  Trigger: is_followup={is_followup}, sender={trigger.get('sender', {}).get('id') or trigger.get('sender_id') or trigger.get('raw_event', {}).get('sender_id')}")
            else:
                print(f"  Trigger: {trigger}")
            print(f"  Step Trace: {json.dumps(trace, ensure_ascii=False)}")
            print("-" * 50)
        print("=" * 50)

        # 4. Fetch background jobs
        jobs_res = await session.execute(
            text("select id, job_type, workspace_id, status, attempts, max_attempts, run_at, locked_at, locked_by, last_error, created_at from public.background_jobs order by created_at desc limit 10")
        )
        print("=== LATEST BACKGROUND JOBS ===")
        for j in jobs_res.mappings().all():
            print(f"Job ID: {j['id']}, Type: {j['job_type']}, Status: {j['status']}, Attempts: {j['attempts']}/{j['max_attempts']}, RunAt: {j['run_at']}, Error: {j['last_error']}")
        print("=" * 50)

        # 5. Fetch webhook events
        events_res = await session.execute(
            text("select id, provider, external_id, created_at from public.webhook_events order by created_at desc limit 10")
        )
        print("=== LATEST WEBHOOK EVENTS ===")
        for e in events_res.mappings().all():
            print(f"Event ID: {e['id']}, Provider: {e['provider']}, External ID: {e['external_id']}, Created: {e['created_at']}")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
