import asyncio
from sqlalchemy import text
from app.db import get_session

async def main():
    print("Starting DDL migration...")
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        # Run ALTER TABLE to add connection_type column
        await session.execute(
            text("""
                ALTER TABLE public.instagram_connections 
                ADD COLUMN IF NOT EXISTS connection_type varchar(50) NOT NULL DEFAULT 'instagram_direct'
            """)
        )
        await session.commit()
        print("Successfully added connection_type column to public.instagram_connections!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
