import asyncio
import json
import sys
from app.db import get_sessionmaker
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Fetch events matching click or postback
        events_res = await session.execute(
            text("select id, provider, external_id, received_at, payload from public.webhook_events where payload::text ilike '%step_click%' or payload::text ilike '%Done%' order by received_at desc limit 10")
        )
        events = events_res.mappings().all()
        print("=== MATCHING CLICK/POSTBACK WEBHOOK EVENTS ===")
        for ev in events:
            payload = ev["payload"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    pass
            print(f"Event ID: {ev['id']}, Provider: {ev['provider']}, External ID: {ev['external_id']}, Received: {ev['received_at']}")
            print(f"Payload: {json.dumps(payload, ensure_ascii=False)[:300]}...")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
