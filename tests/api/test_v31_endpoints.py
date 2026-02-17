"""v3.1 API 테스트 스크립트"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_generate_proposal():
    """제안서 생성 시작"""
    print("=" * 60)
    print("1. 제안서 생성 시작")
    print("=" * 60)

    # Form data로 전송
    data = {
        "rfp_title": "클라우드 기반 ERP 시스템 구축",
        "client_name": "ABC 주식회사",
        "rfp_content": "ERP 시스템 현대화 프로젝트입니다. 기존 레거시 시스템을 클라우드 기반으로 전환하고자 합니다. 주요 기능으로는 회계, 인사, 구매, 재고 관리가 포함됩니다.",
        "express_mode": False
    }

    response = requests.post(f"{BASE_URL}/api/v3.1/proposals/generate", params=data)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result.get("proposal_id")

def test_get_status(proposal_id):
    """제안서 상태 조회"""
    print("\n" + "=" * 60)
    print("2. 제안서 상태 조회")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/v3.1/proposals/{proposal_id}/status")
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result

def test_execute_phase(proposal_id, auto_run=False):
    """Phase 실행"""
    print("\n" + "=" * 60)
    print(f"3. Phase 실행 (auto_run={auto_run})")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/v3.1/proposals/{proposal_id}/execute",
        params={"auto_run": auto_run}
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result

def test_get_result(proposal_id):
    """최종 결과 조회"""
    print("\n" + "=" * 60)
    print("4. 최종 결과 조회")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/v3.1/proposals/{proposal_id}/result")
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result

if __name__ == "__main__":
    try:
        # 1. 제안서 생성
        proposal_id = test_generate_proposal()

        if not proposal_id:
            print("[ERROR] 제안서 생성 실패")
            exit(1)

        # 2. 초기 상태 확인
        test_get_status(proposal_id)

        # 3. Phase 자동 실행
        test_execute_phase(proposal_id, auto_run=True)

        # 4. 실행 후 상태 확인
        time.sleep(1)
        test_get_status(proposal_id)

        # 5. 최종 결과 조회
        test_get_result(proposal_id)

        print("\n" + "=" * 60)
        print("[SUCCESS] 모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 에러 발생: {e}")
        import traceback
        traceback.print_exc()
