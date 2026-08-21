import asyncio
import sys

from sqlalchemy import text

from app.db import get_sessionmaker

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        res = await session.execute(
            text("select workspace_id, ig_user_id, ig_username, access_token_enc, scopes, connection_type from public.instagram_connections")
        )
        row = res.mappings().first()
        if not row:
            print("No Instagram connection found!")
            return
            
        print("=== CONNECTION DETAILS ===")
        print(f"Workspace ID: {row['workspace_id']}")
        print(f"IG User ID: {row['ig_user_id']}")
        print(f"IG Username: {row['ig_username']}")
        print(f"Connection Type: {row['connection_type']}")
        print(f"Scopes: {row['scopes']}")
        
        token = row['access_token_enc'].decode('utf-8')
        print(f"Token length: {len(token)}")
        print(f"Token starts with: {token[:10]}...")
        if token.startswith("EAA"):
            print("Token type: Facebook Page/User Access Token (EAA...)")
        else:
            print("Token type: Likely Instagram Direct/other Token")

if __name__ == "__main__":
    asyncio.run(main())
