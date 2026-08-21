import asyncio
from sqlalchemy import text
from app.db import get_session

async def main():
    session_generator = get_session()
    session = await anext(session_generator)
    try:
        # Query connections
        res_conn = await session.execute(
            text("select workspace_id, ig_user_id, ig_username, connection_type from public.instagram_connections where ig_user_id = :ig_user_id"),
            {"ig_user_id": "26851808784440810"}
        )
        rows_conn = res_conn.mappings().all()
        print(f"Connections in DB for ig_user_id='26851808784440810': {len(rows_conn)}")
        for row in rows_conn:
            print(f"- Workspace ID: {row['workspace_id']}, Username: {row['ig_username']}, Type: {row['connection_type']}")

        # Query all workspaces
        res_ws = await session.execute(
            text("select id, name, owner_id from public.workspaces")
        )
        rows_ws = res_ws.mappings().all()
        print(f"\nTotal Workspaces in DB: {len(rows_ws)}")
        for ws in rows_ws:
            # check if workspace has a connection
            res_c = await session.execute(
                text("select ig_user_id, ig_username from public.instagram_connections where workspace_id = :workspace_id"),
                {"workspace_id": ws["id"]}
            )
            c = res_c.mappings().first()
            conn_str = f"Linked to IG: {c['ig_username']} ({c['ig_user_id']})" if c else "No IG link"
            print(f"- Workspace: {ws['name']} (ID: {ws['id']}), Owner: {ws['owner_id']} -> {conn_str}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
