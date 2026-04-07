import asyncio
from app.utils.supabase_client import get_async_client

async def main():
    client = await get_async_client()
    
    # 모든 제안 프로젝트 삭제
    result = await client.table("proposals").delete().neq("id", "").execute()
    
    print(f"Deleted {len(result.data) if result.data else 0} proposals")

asyncio.run(main())
