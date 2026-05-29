import asyncio
import json
import sys
from app.db import get_sessionmaker
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Fetch latest webhook events
        events_res = await session.execute(
            text("select * from public.webhook_events order by id desc limit 5")
        )
        events = events_res.mappings().all()
        print("=== LATEST WEBHOOK EVENTS ===")
        for ev in events:
            # print all key-values
            print({k: (str(v)[:150] + "...") if isinstance(v, (str, dict, list)) and len(str(v)) > 150 else v for k, v in ev.items()})
            print("-" * 50)
            
        # Fetch latest background jobs
        jobs_res = await session.execute(
            text("select * from public.background_jobs order by id desc limit 5")
        )
        jobs = jobs_res.mappings().all()
        print("\n=== LATEST BACKGROUND JOBS ===")
        for j in jobs:
            print({k: (str(v)[:150] + "...") if isinstance(v, (str, dict, list)) and len(str(v)) > 150 else v for k, v in j.items()})
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
