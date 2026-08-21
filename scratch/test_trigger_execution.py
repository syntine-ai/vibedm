import asyncio
import sys
from uuid import UUID
from app.db import get_sessionmaker
from app.modules.automations.repositories.automations import AutomationRepository
from app.core.jobs import PostgresJobQueue
from app.worker import dispatch_job
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    workspace_id = UUID("04559f81-dc17-4c2d-8759-3a33cfe5eba4")
    automation_id = UUID("c9e8d98e-76f8-48fc-96ae-02d3037de349")
    
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        repo = AutomationRepository(session)
        queue = PostgresJobQueue(session)
        
        # 1. Create the run with a mock sender_id
        print("Creating automation run via create_run with sender_id...")
        run_row = await repo.create_run(
            workspace_id=workspace_id,
            automation_id=automation_id,
            event={"source": "backend_verification_test", "sender_id": "mock_customer_123"}
        )
        run_id = run_row["id"]
        print(f"Created run with ID: {run_id}")
        
        # 2. Check if a background job was enqueued
        result_after = await session.execute(
            text("select id, status, payload from public.background_jobs where job_type = 'automation.run' order by created_at desc limit 1")
        )
        job = result_after.mappings().first()
        if not job:
            print("❌ Verification Failed: No background job was enqueued!")
            return
            
        print(f"✅ Background job enqueued successfully with ID: {job['id']}")
        
        # 3. Simulate claiming and executing the job
        print("Running worker simulation on this job...")
        claimed_job = await queue.claim_next("verification-worker", ["automation.run"])
        if not claimed_job or str(claimed_job.id) != str(job["id"]):
            print("❌ Failed to claim the newly enqueued job!")
            return
            
        print(f"Claimed job {claimed_job.id} successfully. Dispatching...")
        try:
            result = await dispatch_job(claimed_job)
            print(f"✅ Job execution returned: {result}")
            await queue.mark_succeeded(claimed_job.id)
            print("Job marked as succeeded in database.")
        except Exception as e:
            print(f"❌ Job execution failed: {e}")
            await queue.mark_failed(claimed_job.id, str(e))
            
        # Verify run status was updated
        run_status_res = await session.execute(
            text("select status, error, step_trace from public.automation_runs where id = :run_id"),
            {"run_id": run_id}
        )
        run_status = run_status_res.mappings().first()
        print(f"Updated Run Status: {run_status['status']}")
        print(f"Error (if any): {run_status['error']}")
        print(f"Step Trace: {run_status['step_trace']}")

if __name__ == "__main__":
    asyncio.run(main())
