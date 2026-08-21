import asyncio

from sqlalchemy import text

from app.db import get_session


async def main():
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        result = await session.execute(
            text("select id, provider, external_id, payload from public.webhook_events order by id desc limit 5")
        )
        rows = result.mappings().all()
        print(f"Found {len(rows)} recent webhook events:")
        for idx, row in enumerate(rows):
            print(f"\n--- Event #{idx + 1} ---")
            print(f"ID: {row['id']}")
            print(f"Provider: {row['provider']}")
            print(f"External ID: {row['external_id']}")
            print(f"Payload: {row['payload']}")
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
