"""
발표 자료 생성 샘플 테스트 스크립트
- 실제 Claude API 호출 (mock 아님)
- 공공 AI 교육 플랫폼 구축 사업 가상 시나리오
- 결과: /tmp/sample_presentation.pptx
"""

import asyncio
import json
from pathlib import Path

from types import SimpleNamespace

from app.models.phase_schemas import Phase2Artifact, Phase3Artifact, Phase4Artifact
from app.services.presentation_generator import generate_presentation_slides
from app.services.presentation_pptx_builder import build_presentation_pptx

# ── 가상 RFP 데이터 ────────────────────────────────────────────────────────────

RFP = SimpleNamespace(project_name="행정안전부 공공 AI 교육 플랫폼 구축 사업")

# ── Phase 2: RFP 분석 산출물 ──────────────────────────────────────────────────

PHASE2 = Phase2Artifact(
    summary="행정안전부 AI 교육 플랫폼 구축 사업 분석. 기술이해도(40점)와 수행방법론(30점)이 배점의 70% 차지.",
    structured_data={
        "evaluator_perspective": {
            "decision_criteria": [
                "LLM 기반 맞춤형 학습 경로 설계 능력",
                "공무원 업무 특화 콘텐츠 개발 실적",
                "6개월 내 파일럿 운영 전환 가능성",
                "데이터 보안 및 개인정보 보호 체계",
            ],
            "preferred_contractor_profile": "AI/ML 개발 실적 3건 이상, 공공기관 납품 경험 보유, 중소기업 우대",
        }
    },
    key_requirements=[
        "LLM 기반 개인 맞춤형 학습 경로 자동 생성",
        "공무원 직급별 AI 리터러시 커리큘럼 개발",
        "실습 샌드박스 환경 구축 (보안 격리)",
        "학습 진도 및 역량 측정 대시보드",
    ],
    evaluation_weights={
        "기술이해도": 40,
        "수행방법론": 30,
        "추진일정": 15,
        "인력구성": 15,
    },
)

# ── Phase 3: 전략 산출물 ──────────────────────────────────────────────────────

PHASE3 = Phase3Artifact(
    summary="LLM 개인화 학습 경로 + 공무원 특화 콘텐츠를 핵심 차별화 전략으로 설정.",
    win_strategy="공무원 업무 맥락에 최적화된 LLM 튜터를 통해 개인 맞춤형 AI 역량 강화를 6개월 내 실현",
    win_theme={
        "primary_message": "공무원 한 명 한 명에게 맞춤화된 AI 튜터 — 6개월 내 전 직급 AI 리터러시 달성",
        "evidence_pillars": [
            "GPT-4o 파인튜닝으로 공무원 업무 문서 92% 정확도 달성",
            "유사 공공기관 3곳 도입 후 평균 학습 완료율 78% (업계 평균 34%)",
            "보안 격리 샌드박스로 개인정보보호법 완전 준수",
        ],
    },
    differentiation_strategy=[
        "공무원 직급별 맞춤 커리큘럼 — 일반 LLM 교육과 달리 행정 문서 작성, 정책 분석에 특화",
        "실습 우선 설계 — 이론 20% : 실습 80% 비율로 즉시 업무 적용 가능",
        "지속 학습 모델 — 신규 AI 도구 출시 시 커리큘럼 자동 업데이트",
    ],
    section_plan=[
        {
            "section_name": "사업 이해도 및 기술 역량",
            "target_criteria": "기술이해도",
            "score_weight": 40,
            "evaluator_check_points": [
                "LLM API 연동 및 파인튜닝 경험 확인",
                "공무원 업무 특화 데이터셋 보유 여부",
                "유사 AI 교육 플랫폼 구축 실적",
            ],
        },
        {
            "section_name": "수행 방법론 및 차별화",
            "target_criteria": "수행방법론",
            "score_weight": 30,
            "evaluator_check_points": [
                "개인 맞춤형 학습 경로 알고리즘 설계",
                "콘텐츠 품질 관리 프로세스",
                "보안 격리 환경 구축 방법론",
            ],
        },
        {
            "section_name": "추진 일정",
            "target_criteria": "추진일정",
            "score_weight": 15,
            "evaluator_check_points": [
                "6개월 파일럿 운영 전환 실현 가능성",
                "단계별 마일스톤 명확성",
            ],
        },
        {
            "section_name": "투입 인력 및 역량",
            "target_criteria": "인력구성",
            "score_weight": 15,
            "evaluator_check_points": [
                "AI/ML 전문 인력 투입 계획",
                "PM 공공사업 관리 경험",
            ],
        },
    ],
    team_plan="PM 1명(PMP 자격, 공공사업 8년), AI 엔지니어 3명(LLM 파인튜닝), 콘텐츠 기획 2명, QA 1명 — 총 7명",
    implementation_checklist=[
        {
            "phase": "1단계: 착수·설계",
            "duration": "1~2개월",
            "deliverables": ["요구사항 정의서", "시스템 아키텍처 설계", "커리큘럼 프레임워크"],
        },
        {
            "phase": "2단계: 개발·콘텐츠 제작",
            "duration": "3~6개월",
            "deliverables": ["LLM 튜터 엔진", "직급별 콘텐츠 50모듈", "샌드박스 환경"],
        },
        {
            "phase": "3단계: 파일럿·이관",
            "duration": "7~9개월",
            "deliverables": ["파일럿 운영 보고서", "운영 매뉴얼", "유지보수 계약"],
        },
    ],
)

# ── Phase 4: 제안서 본문 ──────────────────────────────────────────────────────

PHASE4 = Phase4Artifact(
    summary="7개 섹션 제안서 본문 작성 완료.",
    sections={
        "사업 이해도 및 기술 역량": (
            "당사는 GPT-4o 기반 파인튜닝 모델을 행정 문서 2만 건으로 학습시켜 "
            "공무원 업무 문서 처리 정확도 92%를 달성했습니다. "
            "교육부 AI 교육 플랫폼(2024, 5억원), 중소벤처기업부 디지털 전환 교육(2023, 3억원), "
            "과학기술정보통신부 AI 활용 교육(2022, 2억원) 등 공공기관 AI 교육 구축 실적 3건을 보유하고 있습니다. "
            "LLM 파인튜닝, RAG 아키텍처, 벡터 데이터베이스 연동 등 핵심 기술 스택을 자체 보유하고 있으며, "
            "공무원 직급별 업무 패턴 데이터 15만 건을 축적하고 있습니다."
        ),
        "수행 방법론 및 차별화": (
            "개인화 학습 경로는 3단계 알고리즘으로 설계됩니다: "
            "(1) 진단 평가로 현재 AI 리터러시 수준 측정, "
            "(2) 직급·업무 유형별 학습 경로 자동 생성, "
            "(3) 완료율 및 업무 적용 빈도 기반 경로 재조정. "
            "이 방식으로 교육부 파일럿에서 학습 완료율 78%를 달성했습니다 (업계 평균 34% 대비 2.3배). "
            "보안 격리 샌드박스는 AWS GovCloud 기반으로 구축하며, "
            "개인정보보호법 제24조 및 망분리 요건을 완전 준수합니다."
        ),
        "추진 일정": (
            "전체 사업 기간 12개월을 3단계로 구성합니다. "
            "1단계(1~2개월)는 착수 및 설계로 요구사항 확정, 아키텍처 설계, 커리큘럼 프레임워크를 완성합니다. "
            "2단계(3~6개월)는 핵심 개발 단계로 LLM 튜터 엔진과 직급별 콘텐츠 50모듈을 완성합니다. "
            "3단계(7~9개월)는 파일럿 운영으로 100명 대상 시범 운영 후 피드백 반영, "
            "10~12개월은 전체 이관 및 안정화입니다. "
            "6개월 파일럿 운영 시작은 계약 후 6개월 내 보장합니다."
        ),
        "투입 인력 및 역량": (
            "PM 1명(PMP 자격증, 공공사업 8년 경험), "
            "AI 엔지니어 3명(LLM 파인튜닝 경험 각 3년 이상), "
            "콘텐츠 기획 2명(공무원 교육 경력 보유), "
            "QA 엔지니어 1명 — 총 7명 전담 투입. "
            "PM은 교육부·중기부 유사 사업 동시 성공적 수행 이력 보유. "
            "총 투입 공수: 52 person-months."
        ),
    },
)


# ── 실행 ──────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("발표 자료 생성 샘플 테스트")
    print(f"사업명: {RFP.project_name}")
    print("=" * 60)

    print("\n[Step 1] TOC 생성 중...")
    slides_json = await generate_presentation_slides(PHASE2, PHASE3, PHASE4, RFP)

    print(f"\n[Step 1 완료] 슬라이드 {slides_json.get('total_slides')}장 목차 생성")
    print("[Step 2 완료] 스토리보드 생성 완료")
    print(f"eval_coverage: {json.dumps(slides_json.get('eval_coverage', {}), ensure_ascii=False)}")

    print("\n--- 생성된 슬라이드 목차 ---")
    for s in slides_json.get("slides", []):
        badge = f" [{s.get('eval_badge')}]" if s.get('eval_badge') else ""
        print(f"  Slide {s['slide_num']:2d} [{s['layout']:12s}]{badge} {s.get('title', '')}")

    def p(text):
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))

    # PPTX 빌드
    output_path = Path("/tmp/sample_presentation.pptx")
    print(f"\n[PPTX 빌드] → {output_path}")
    build_presentation_pptx(slides_json, output_path, RFP.project_name)
    print(f"[완료] {output_path} ({output_path.stat().st_size // 1024} KB)")

    # JSON 저장 (검토용)
    json_path = Path("/tmp/sample_slides.json")
    json_path.write_text(
        json.dumps(slides_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[JSON] {json_path} (슬라이드 내용 상세 확인용)")


if __name__ == "__main__":
    asyncio.run(main())
