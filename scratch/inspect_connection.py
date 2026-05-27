import asyncio
from sqlalchemy import text
from app.db import get_session

async def main():
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        result = await session.execute(
            text("select workspace_id, ig_user_id, ig_username from public.instagram_connections")
        )
        rows = result.mappings().all()
        print(f"Found {len(rows)} Instagram connections in database:")
        for idx, row in enumerate(rows):
            print(f"Connection #{idx + 1}: Workspace ID = {row['workspace_id']}, IG User ID = {row['ig_user_id']}, IG Username = {row['ig_username']}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
