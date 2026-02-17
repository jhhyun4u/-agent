"""코어 기능 통합 테스트"""
import asyncio
from pathlib import Path
from datetime import datetime

from app.models.schemas import ProjectInput, ProposalContent
from app.services.proposal_generator import generate_proposal_from_input
from app.services.docx_builder import build_docx
from app.services.pptx_builder import build_pptx


async def test_full_workflow():
    """전체 워크플로우 테스트: 입력 → 제안서 생성 → 문서 생성"""

    print("=" * 60)
    print("1. 프로젝트 입력 데이터 준비")
    print("=" * 60)

    project = ProjectInput(
        project_name="클라우드 기반 ERP 시스템 구축",
        client_name="ABC 주식회사",
        project_scope="기존 레거시 ERP 시스템을 클라우드 기반으로 전환",
        duration="6개월",
        budget="5억원",
        requirements=[
            "SAP 또는 Oracle ERP 경험 필수",
            "AWS 또는 Azure 클라우드 인프라 구축 경험",
            "데이터 마이그레이션 및 통합 경험",
            "재무, 인사, 구매, 재고 모듈 구현"
        ],
        additional_info="2024년 Q3 완료 목표, 사용자 교육 포함"
    )

    print(f"프로젝트명: {project.project_name}")
    print(f"고객사: {project.client_name}")
    print(f"기간: {project.duration}")
    print(f"예산: {project.budget}")

    print("\n" + "=" * 60)
    print("2. Claude를 사용한 제안서 콘텐츠 생성")
    print("=" * 60)

    try:
        proposal_content = await generate_proposal_from_input(project)
        print("✓ 제안서 생성 성공!")
        print(f"  - 사업 개요: {len(proposal_content.project_overview)} 자")
        print(f"  - 사업 이해도: {len(proposal_content.understanding)} 자")
        print(f"  - 접근 방법론: {len(proposal_content.approach)} 자")
        print(f"  - 수행 방법론: {len(proposal_content.methodology)} 자")
        print(f"  - 추진 일정: {len(proposal_content.schedule)} 자")
        print(f"  - 투입 인력: {len(proposal_content.team_composition)} 자")
        print(f"  - 기대 효과: {len(proposal_content.expected_outcomes)} 자")

    except Exception as e:
        print(f"✗ 제안서 생성 실패: {e}")
        return

    print("\n" + "=" * 60)
    print("3. DOCX 문서 생성")
    print("=" * 60)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    docx_path = output_dir / f"proposal_{timestamp}.docx"

    try:
        result_path = build_docx(proposal_content, project.project_name, docx_path)
        print(f"✓ DOCX 생성 성공: {result_path}")
    except Exception as e:
        print(f"✗ DOCX 생성 실패: {e}")

    print("\n" + "=" * 60)
    print("4. PPTX 문서 생성")
    print("=" * 60)

    pptx_path = output_dir / f"proposal_{timestamp}.pptx"

    try:
        result_path = build_pptx(proposal_content, project.project_name, pptx_path)
        print(f"✓ PPTX 생성 성공: {result_path}")
    except Exception as e:
        print(f"✗ PPTX 생성 실패: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print(f"\n생성된 파일:")
    print(f"  - {docx_path}")
    print(f"  - {pptx_path}")


if __name__ == "__main__":
    # .env 파일에 ANTHROPIC_API_KEY가 설정되어 있어야 합니다
    asyncio.run(test_full_workflow())
