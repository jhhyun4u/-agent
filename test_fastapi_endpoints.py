"""
v3.1.1 FastAPI 엔드포인트 테스트

테스트 항목:
1. POST /v3.1/proposals/generate - 제안서 생성 시작
2. GET /v3.1/proposals/{id}/status - 상태 조회
3. POST /v3.1/proposals/{id}/execute - Phase 실행
4. GET /v3.1/proposals/{id}/result - 최종 결과
"""

import sys
import os
from pathlib import Path

_project_root = str(Path(__file__).parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
from fastapi.testclient import TestClient
from app.main import app


def test_fastapi_endpoints():
    """FastAPI 엔드포인트 테스트"""
    
    client = TestClient(app)
    
    print("\n" + "="*80)
    print("v3.1.1 FastAPI 엔드포인트 테스트")
    print("="*80)
    
    # ─────── Test 1: 제안서 생성 시작 ───────
    print("\n[TEST 1] POST /v3.1/proposals/generate")
    print("-" * 80)
    
    response = client.post(
        "/v3.1/proposals/generate",
        params={
            "rfp_title": "클라우드 마이그레이션 제안 요청서",
            "client_name": "삼성전자",
            "rfp_content": "우리는 레거시 시스템을 최신 클라우드 아키텍처로 마이그레이션하려고 합니다.",
            "express_mode": False,
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        proposal_id = result["proposal_id"]
        print(f"✓ 제안서 ID: {proposal_id}")
        print(f"✓ 상태: {result['status']}")
        print(f"✓ 예상 소요시간: {result['estimated_duration_seconds']}초")
        print(f"✓ 단계: {result['phases']}")
    else:
        print(f"✗ 에러: {response.text}")
        return False
    
    # ─────── Test 2: 상태 조회 ───────
    print("\n[TEST 2] GET /v3.1/proposals/{id}/status")
    print("-" * 80)
    
    response = client.get(f"/v3.1/proposals/{proposal_id}/status")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 제안서 ID: {result['proposal_id']}")
        print(f"✓ RFP: {result['rfp_title']}")
        print(f"✓ 고객사: {result['client_name']}")
        print(f"✓ 현재 단계: {result['current_phase']}")
        print(f"✓ 완료된 단계: {result['phases_completed']}")
    else:
        print(f"✗ 에러: {response.text}")
        return False
    
    # ─────── Test 3: Phase 실행 (자동) ───────
    print("\n[TEST 3] POST /v3.1/proposals/{id}/execute (auto_run=true)")
    print("-" * 80)
    
    response = client.post(f"/v3.1/proposals/{proposal_id}/execute?auto_run=true")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 상태: {result['status']}")
        print(f"✓ 완료된 단계: {result['phases_completed']}")
        print(f"✓ 메시지: {result['message']}")
    else:
        print(f"✗ 에러: {response.text}")
        return False
    
    # ─────── Test 4: 최종 결과 조회 ───────
    print("\n[TEST 4] GET /v3.1/proposals/{id}/result")
    print("-" * 80)
    
    response = client.get(f"/v3.1/proposals/{proposal_id}/result")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 제안서 ID: {result['proposal_id']}")
        print(f"✓ 상태: {result['status']}")
        print(f"✓ 완료된 Phase: {result['phases_completed']}")
        print(f"✓ 품질 점수: {result['quality_score']:.2f}")
        print(f"✓ 포함된 아티팩트: {list(result['artifacts'].keys())}")
    else:
        print(f"✗ 에러: {response.text}")
        return False
    
    # ─────── Summary ───────
    print("\n" + "="*80)
    print("✅ FastAPI 엔드포인트 테스트 완료")
    print("="*80)
    print("""
테스트 결과:
  ✓ POST /v3.1/proposals/generate: 제안서 생성 시작
  ✓ GET /v3.1/proposals/{id}/status: 진행 상태 조회
  ✓ POST /v3.1/proposals/{id}/execute: Phase 자동 실행
  ✓ GET /v3.1/proposals/{id}/result: 최종 결과 조회

다음 단계:
  1. 개별 Phase 실행 모드 테스트
  2. HITL 게이트 시뮬레이션
  3. WebSocket 실시간 업데이트
  4. Docker 배포
""")
    
    return True


if __name__ == "__main__":
    try:
        success = test_fastapi_endpoints()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
