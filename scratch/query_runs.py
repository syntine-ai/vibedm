import asyncio
import json
import sys
from uuid import UUID
from app.db import get_sessionmaker
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Fetch automations
        automations_res = await session.execute(
            text("select id, name, status, trigger_type, trigger_config from public.automations order by updated_at desc limit 5")
        )
        automations = automations_res.mappings().all()
        print("=== LATEST AUTOMATIONS ===")
        for aut in automations:
            print(f"ID: {aut['id']}, Name: {aut['name']}, Status: {aut['status']}, Trigger: {aut['trigger_type']}")
            print(f"Trigger Config: {json.dumps(aut['trigger_config'], ensure_ascii=False)}")
            
            # Fetch steps for this automation
            steps_res = await session.execute(
                text("select id, step_order, action_type, config from public.automation_steps where automation_id = :aid order by step_order asc"),
                {"aid": aut["id"]}
            )
            steps = steps_res.mappings().all()
            for s in steps:
                print(f"  Step {s['step_order']}: ID={s['id']}, Action={s['action_type']}")
                print(f"  Config: {json.dumps(s['config'], ensure_ascii=False)}")
            print("-" * 50)
            
        # Fetch latest runs
        runs_res = await session.execute(
            text("select id, automation_id, status, error, step_trace, created_at from public.automation_runs order by created_at desc limit 5")
        )
        runs = runs_res.mappings().all()
        print("\n=== LATEST AUTOMATION RUNS ===")
        for r in runs:
            print(f"Run ID: {r['id']}, Automation ID: {r['automation_id']}, Status: {r['status']}, Created: {r['created_at']}")
            print(f"Error: {r['error']}")
            print(f"Step Trace: {json.dumps(r['step_trace'], ensure_ascii=False) if isinstance(r['step_trace'], list) else r['step_trace']}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
