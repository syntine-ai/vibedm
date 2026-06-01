import asyncio
from sqlalchemy import text
from app.db import get_session

async def main():
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        user_id = "d6a57f76-d878-41a4-b31c-d347094a7633"
        print(f"Inspecting workspaces for User: {user_id}")
        
        res = await session.execute(
            text("""
                select wm.workspace_id, wm.role, wm.active, w.name
                from public.workspace_members wm
                join public.workspaces w on wm.workspace_id = w.id
                where wm.user_id = :user_id
            """),
            {"user_id": user_id}
        )
        rows = res.mappings().all()
        for row in rows:
            print(f"- Workspace Name: {row['name']} (ID: {row['workspace_id']})")
            print(f"  Role: {row['role']}, Active: {row['active']}")
            
            # Check connection
            res_c = await session.execute(
                text("select ig_user_id, ig_username from public.instagram_connections where workspace_id = :workspace_id"),
                {"workspace_id": row['workspace_id']}
            )
            c = res_c.mappings().first()
            if c:
                print(f"  Instagram: Connected as @{c['ig_username']} ({c['ig_user_id']})")
            else:
                print("  Instagram: Not Connected")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
