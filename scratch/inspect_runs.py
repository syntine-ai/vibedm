import asyncio
from sqlalchemy import text
from app.db import get_session

async def main():
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        # Check automation runs
        result = await session.execute(
            text("select id, workspace_id, automation_id, contact_id, status, created_at from public.automation_runs order by created_at desc limit 5")
        )
        rows = result.mappings().all()
        print(f"Found {len(rows)} automation runs:")
        for idx, row in enumerate(rows):
            print(f"  Run #{idx + 1}: ID = {row['id']}, Status = {row['status']}, Created At = {row['created_at']}")

        # Check background jobs
        result_jobs = await session.execute(
            text("select id, job_type, workspace_id, attempts from public.background_jobs limit 5")
        )
        rows_jobs = result_jobs.mappings().all()
        print(f"\nFound {len(rows_jobs)} background jobs:")
        for idx, row in enumerate(rows_jobs):
            print(f"  Job #{idx + 1}: ID = {row['id']}, Type = {row['job_type']}, Attempts = {row['attempts']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
