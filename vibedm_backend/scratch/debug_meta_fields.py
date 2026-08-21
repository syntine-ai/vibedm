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
            # Try various fields on /me
            fields = "id,username,name,account_type,ig_id"
            print(f"Querying /me with fields: {fields}")
            res_me = await client.get(
                "https://graph.instagram.com/v25.0/me",
                params={"fields": fields, "access_token": token}
            )
            print(f"Status: {res_me.status_code}")
            print(f"Response: {res_me.text}")

if __name__ == "__main__":
    asyncio.run(main())
