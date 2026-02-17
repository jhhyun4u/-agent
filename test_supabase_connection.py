"""Supabase 연결 테스트"""
import asyncio
from app.utils.supabase_client import get_supabase_client


async def test_connection():
    """Supabase 연결 및 기본 작업 테스트"""

    print("\n" + "="*70)
    print("Supabase 연결 테스트")
    print("="*70)

    try:
        # 클라이언트 가져오기
        client = get_supabase_client()

        print("\n[1] 클라이언트 초기화")
        if client.is_available():
            print("    OK: Supabase 클라이언트 사용 가능")
        else:
            print("    ERROR: Supabase 클라이언트 초기화 실패")
            print("    → .env 파일에 SUPABASE_URL과 SUPABASE_KEY를 확인하세요")
            return

        # 제안서 조회 테스트
        print("\n[2] 제안서 데이터 조회")
        proposals = await client.get_proposals()
        print(f"    OK: 제안서 {len(proposals)}건 조회")

        if proposals:
            for prop in proposals[:3]:
                print(f"    - {prop.get('title', 'N/A')} ({prop.get('client', 'N/A')})")

        # 인력 조회 테스트
        print("\n[3] 인력 데이터 조회")
        personnel = await client.get_personnel()
        print(f"    OK: 인력 {len(personnel)}명 조회")

        if personnel:
            for person in personnel[:3]:
                print(f"    - {person.get('name', 'N/A')} ({person.get('role', 'N/A')})")

        # 참고 자료 조회 테스트
        print("\n[4] 참고 자료 조회")
        references = await client.get_references()
        print(f"    OK: 참고 자료 {len(references)}건 조회")

        if references:
            for ref in references[:3]:
                print(f"    - {ref.get('title', 'N/A')}")

        # 검색 테스트
        print("\n[5] 검색 기능 테스트")
        search_results = await client.search_proposals("클라우드")
        print(f"    OK: '클라우드' 검색 결과: {len(search_results)}건")

        print("\n" + "="*70)
        print("SUCCESS: Supabase 연결 테스트 성공!")
        print("="*70)
        print("\n모든 기능이 정상 작동합니다!")

    except Exception as e:
        print("\n" + "="*70)
        print("FAILED: Supabase 연결 테스트 실패")
        print("="*70)
        print(f"\n에러: {e}")
        print("\n문제 해결 방법:")
        print("1. .env 파일에 SUPABASE_URL이 올바른지 확인")
        print("2. .env 파일에 SUPABASE_KEY가 올바른지 확인")
        print("3. Supabase 프로젝트가 활성 상태인지 확인")
        print("4. database/supabase_schema.sql이 실행되었는지 확인")

        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_connection())
