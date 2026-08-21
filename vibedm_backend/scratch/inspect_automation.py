import asyncio
from sqlalchemy import text
from app.db import get_session

async def main():
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        result = await session.execute(
            text("select id, workspace_id, name, trigger_type::text, trigger_config, status from public.automations")
        )
        rows = result.mappings().all()
        print(f"Found {len(rows)} automations in database:")
        for idx, row in enumerate(rows):
            print(f"\nAutomation #{idx + 1}:")
            print(f"  ID: {row['id']}")
            print(f"  Workspace ID: {row['workspace_id']}")
            print(f"  Name: {row['name']}")
            print(f"  Trigger Type: {row['trigger_type']}")
            print(f"  Trigger Config: {row['trigger_config']}")
            print(f"  Status: {row['status']}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
