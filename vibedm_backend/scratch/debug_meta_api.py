import asyncio
import sys
import httpx
from app.db import get_sessionmaker
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        res = await session.execute(
            text("select access_token_enc from public.instagram_connections limit 1")
        )
        row = res.mappings().first()
        if not row:
            print("No Instagram connection found!")
            return
            
        token = row['access_token_enc'].decode('utf-8')
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for target_id in ["17841435569954875", "17841474484493870"]:
                print(f"\n--- Querying /{target_id} ---")
                try:
                    res_user = await client.get(
                        f"https://graph.instagram.com/v25.0/{target_id}",
                        params={"fields": "id,username,name", "access_token": token}
                    )
                    print(f"Status: {res_user.status_code}")
                    print(f"Response: {res_user.text}")
                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
