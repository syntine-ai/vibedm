import asyncio
import os
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

async def test_query():
    db_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            # Let's execute the original query to see if it reproduces the AmbiguousParameterError
            # when statement caching is disabled.
            print("Running test query with explicit casts...")
            query = text("""
                select id, workspace_id, ig_user_id, ig_username::text as ig_username, name,
                       email::text as email, phone, source_automation_id, tags, notes
                from public.contacts
                where workspace_id = :workspace_id
                  and (
                    cast(:source_automation_id as uuid) is null
                    or source_automation_id = cast(:source_automation_id as uuid)
                  )
                  and (cast(:tag as text) is null or cast(:tag as text) = any(tags))
                  and (
                    cast(:q as text) is null or
                    coalesce(ig_username::text, '') ilike '%' || cast(:q as text) || '%' or
                    coalesce(name, '') ilike '%' || cast(:q as text) || '%' or
                    coalesce(email::text, '') ilike '%' || cast(:q as text) || '%' or
                    coalesce(phone, '') ilike '%' || cast(:q as text) || '%'
                  )
                order by created_at desc
            """)
            
            # Using a mock workspace UUID and None for optional parameters
            result = await conn.execute(
                query,
                {
                    "workspace_id": UUID("900a0785-83b2-4095-91fa-b1627fd81d3f"),
                    "q": None,
                    "source_automation_id": None,
                    "tag": None,
                }
            )
            print("Query succeeded! Found rows:", len(result.all()))
    except Exception:
        print("Query failed with error:")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_query())
