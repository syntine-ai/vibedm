import asyncio
import sys
import httpx
from app.db import get_sessionmaker
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Find the connection in the database
        res = await session.execute(
            text("select workspace_id, ig_user_id, access_token_enc from public.instagram_connections where ig_user_id = '26851808784440810'")
        )
        row = res.mappings().first()
        if not row:
            print("No connection found with ID 26851808784440810")
            return
            
        token = row['access_token_enc'].decode('utf-8')
        workspace_id = row['workspace_id']
        
        # We know from the webhook events that the global ID is 17841435569954875
        global_id = "17841435569954875"
        
        # Verify it
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res_user = await client.get(
                    f"https://graph.instagram.com/v25.0/{global_id}",
                    params={"fields": "id", "access_token": token}
                )
                if res_user.status_code == 200 and res_user.json().get("id") == "26851808784440810":
                    print(f"Verified: Global ID {global_id} corresponds to scoped ID 26851808784440810.")
                    
                    # Update database connection
                    await session.execute(
                        text("""
                            update public.instagram_connections
                            set ig_user_id = :new_id,
                                updated_at = now()
                            where workspace_id = :workspace_id
                        """),
                        {"new_id": global_id, "workspace_id": workspace_id}
                    )
                    await session.commit()
                    print("Successfully updated database connection to use the global ID!")
                else:
                    print(f"Verification failed: {res_user.status_code} - {res_user.text}")
            except Exception as e:
                print(f"Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(main())
