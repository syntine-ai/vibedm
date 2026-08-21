import asyncio
from sqlalchemy import text
from app.db import get_session

async def main():
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        result = await session.execute(
            text("""
                select column_name, data_type 
                from information_schema.columns 
                where table_schema = 'public' and table_name = 'instagram_connections'
            """)
        )
        rows = result.all()
        print("Columns in public.instagram_connections:")
        for row in rows:
            print(f"- {row[0]} ({row[1]})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
