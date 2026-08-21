import asyncio
import sys

import httpx
from sqlalchemy import text

from app.db import get_sessionmaker

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        res = await session.execute(
            text("select access_token_enc from public.instagram_connections limit 1")
        )
        row = res.mappings().first()
        if not row:
            return
        token = row['access_token_enc'].decode('utf-8')
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Query media using the global ID 17841435569954875
            global_id = "17841435569954875"
            print(f"Querying /{global_id}/media...")
            try:
                res_media = await client.get(
                    f"https://graph.instagram.com/v25.0/{global_id}/media",
                    params={"fields": "id,caption", "limit": 3, "access_token": token}
                )
                print(f"Status: {res_media.status_code}")
                print(f"Response: {res_media.text}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
