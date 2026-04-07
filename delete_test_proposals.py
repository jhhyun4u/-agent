import asyncio
from app.utils.supabase_client import get_async_client

async def main():
    client = await get_async_client()
    
    # 모든 제안 프로젝트 조회
    result = await client.table("proposals").select("id, bid_no").execute()
    
    if result.data:
        print(f"Found {len(result.data)} proposals")
        # bid_no가 없는 것만 삭제 (테스트 데이터)
        for p in result.data:
            if not p.get('bid_no'):
                print(f"Deleting: {p['id']}")
                await client.table("proposals").delete().eq("id", p['id']).execute()
                print(f"Deleted: {p['id']}")
    else:
        print("No proposals found")

asyncio.run(main())
