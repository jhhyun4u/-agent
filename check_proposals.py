import asyncio
from app.utils.supabase_client import get_async_client

async def main():
    client = await get_async_client()
    result = await client.table("proposals").select("id, title, status").execute()
    print(f"총 제안 프로젝트: {len(result.data) if result.data else 0}")
    for p in (result.data or []):
        print(f"  - {p['id']}: {p['title']} ({p['status']})")

asyncio.run(main())
