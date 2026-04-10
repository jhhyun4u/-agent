import asyncio
import os
os.environ['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

from supabase import create_client

async def main():
    url = os.environ['SUPABASE_URL']
    key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    client = create_client(url, key)
    
    # 모든 제안 삭제
    client.table("proposals").delete().neq("id", "ffffffff-ffff-ffff-ffff-ffffffffffff").execute()
    print("Deleted proposals")

if __name__ == "__main__":
    asyncio.run(main())
