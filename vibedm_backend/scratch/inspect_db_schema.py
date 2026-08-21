import asyncio
import sys

from sqlalchemy import text

from app.db import get_sessionmaker

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Table count
        count_res = await session.execute(text("select count(*) as cnt from public.background_jobs"))
        count = count_res.scalar_one()
        print(f"Total rows in background_jobs: {count}")
        
        # Check table columns and schema
        cols_res = await session.execute(
            text("""
                select column_name, data_type, is_nullable 
                from information_schema.columns 
                where table_schema = 'public' and table_name = 'background_jobs'
            """)
        )
        print("Columns in background_jobs:")
        for col in cols_res.mappings().all():
            print(f"  - {col['column_name']} ({col['data_type']}), Nullable: {col['is_nullable']}")
            
        # Check triggers on background_jobs
        triggers_res = await session.execute(
            text("""
                select trigger_name, event_manipulation, action_statement
                from information_schema.triggers
                where event_object_schema = 'public' and event_object_table = 'background_jobs'
            """)
        )
        print("Triggers on background_jobs:")
        for t in triggers_res.mappings().all():
            print(f"  - {t['trigger_name']} ({t['event_manipulation']}): {t['action_statement']}")

if __name__ == "__main__":
    asyncio.run(main())
