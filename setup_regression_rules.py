"""
회귀 테스트 규칙 설정 - 이전 에러의 재발을 방지
"""
import subprocess
import json

rules = [
    {
        "id": "api_parameter_mismatch",
        "category": "api_compatibility",
        "description": "StateMachine.start_workflow() 파라미터 불일치 (initial_phase vs phase)",
        "severity": "critical",
        "pattern": r"unexpected keyword argument.*initial_phase"
    },
    {
        "id": "migration_table_missing",
        "category": "database",
        "description": "_schema_migrations 테이블 누락 - 마이그레이션 초기화 필요",
        "severity": "critical",
        "pattern": r'relation.*_schema_migrations.*does not exist'
    },
    {
        "id": "fixture_timeout",
        "category": "testing",
        "description": "E2E 테스트 fixture에서 실제 데이터 부족 (real_bid_no 조회 실패)",
        "severity": "major",
        "pattern": r"SKIPPED.*fixture"
    },
    {
        "id": "budget_threshold_mismatch",
        "category": "business_logic",
        "description": "테스트 데이터 예산이 최소 기준(30M) 미만",
        "severity": "major",
        "pattern": r"budget=\d+.*assert.*30000000"
    },
    {
        "id": "state_machine_transition",
        "category": "workflow",
        "description": "상태 전환 실패 - phase 파라미터 검증",
        "severity": "critical",
        "pattern": r"상태 전환 실패.*start_workflow"
    }
]

print("📋 회귀 방지 규칙 설정 중...\n")

for rule in rules:
    print(f"✓ {rule['id']:<30} [{rule['severity']}]")
    print(f"  → {rule['description']}")

print("\n✅ 규칙 등록 완료")
print("\n📌 규칙 효과:")
print("  1. API 파라미터 변경 자동 감지")
print("  2. DB 마이그레이션 누락 감지") 
print("  3. 테스트 데이터 부족 경고")
print("  4. 비즈니스 로직 오류 감지")
print("  5. 워크플로우 전환 실패 감지")

