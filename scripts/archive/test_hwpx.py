"""HWPX 빌더 간단 테스트 스크립트"""
from pathlib import Path
from app.services.hwpx_builder import build_hwpx

# 테스트용 섹션 데이터
sections = {
    "project_overview": "본 제안서는 테스트 목적으로 작성된 샘플입니다.\n\n□ 주요 목표\n  ❍ AI 기반 제안서 자동 생성 시스템 구축\n  ❍ 공공입찰 대응 효율화",
    "understanding": "- 발주처 요구사항 분석 완료\n- 기술 스펙 검토 완료",
    "approach": "1. 요구사항 분석\n2. 설계 및 개발\n3. 테스트 및 납품",
    "team_composition": "□ 프로젝트 팀 구성\n  ❍ PM: 홍길동 (10년 경력)\n  ❍ 개발자: 김철수 (5년 경력)",
    "methodology": "□ 수행 방법론\n  ❍ 애자일 방법론 적용\n  ☞ 2주 스프린트 단위 개발",
    "schedule": "- 1단계 (1~2개월): 요구사항 분석\n- 2단계 (3~5개월): 개발\n- 3단계 (6개월): 테스트 및 납품",
    "expected_outcomes": "【기대효과】 제안서 작성 시간 80% 단축\n\n(근거: 기존 수작업 대비 AI 자동화 효과 측정 결과)",
}

metadata = {
    "client_name": "한국테스트기관",
    "proposer_name": "테노파파트너스(주)",
    "submit_date": "2026. 3.",
    "bid_notice_number": "20260301-001",
    "evaluation_weights": {
        "사업수행계획서": "40",
        "기술역량": "20",
        "유사실적": "20",
    },
}

output_path = Path("output/test_proposal.hwpx")

print("HWPX 생성 시작...")
result = build_hwpx(
    sections=sections,
    output_path=output_path,
    project_name="AI 기반 제안서 자동생성 시스템 구축 용역",
    metadata=metadata,
)
print(f"생성 완료: {result}")
print(f"파일 크기: {result.stat().st_size:,} bytes")
