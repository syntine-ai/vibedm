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
            return
        token = row['access_token_enc'].decode('utf-8')
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Try Facebook Graph API /me
            print("Querying graph.facebook.com/me with IG token...")
            try:
                res_fb = await client.get(
                    "https://graph.facebook.com/v25.0/me",
                    params={"access_token": token}
                )
                print(f"Status: {res_fb.status_code}")
                print(f"Response: {res_fb.text}")
            except Exception as e:
                print(f"Error: {e}")
                
            # Try Facebook Graph API /me/accounts
            print("\nQuerying graph.facebook.com/me/accounts with IG token...")
            try:
                res_fb_acc = await client.get(
                    "https://graph.facebook.com/v25.0/me/accounts",
                    params={"access_token": token}
                )
                print(f"Status: {res_fb_acc.status_code}")
                print(f"Response: {res_fb_acc.text}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
