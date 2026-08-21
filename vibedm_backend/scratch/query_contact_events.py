import asyncio
import json
import sys

from sqlalchemy import text

from app.db import get_sessionmaker

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Fetch events for the specific contact
        events_res = await session.execute(
            text("select id, provider, external_id, received_at, payload from public.webhook_events where payload::text ilike '%883093804043055%' order by received_at desc limit 15")
        )
        events = events_res.mappings().all()
        print("=== WEBHOOK EVENTS FOR CONTACT 883093804043055 ===")
        for ev in events:
            payload = ev["payload"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    pass
            print(f"Event ID: {ev['id']}, Provider: {ev['provider']}, External ID: {ev['external_id']}, Received: {ev['received_at']}")
            print(f"Payload: {json.dumps(payload, ensure_ascii=False)[:400]}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
