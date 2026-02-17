"""문서 빌더 테스트 (API 키 불필요)"""
from pathlib import Path
from datetime import datetime

from app.models.schemas import ProposalContent
from app.services.docx_builder import build_docx
from app.services.pptx_builder import build_pptx


def test_document_builders():
    """DOCX 및 PPTX 빌더만 테스트"""

    print("=" * 60)
    print("문서 빌더 테스트 (Mock 데이터 사용)")
    print("=" * 60)

    # Mock 제안서 콘텐츠
    mock_content = ProposalContent(
        project_overview="""본 프로젝트는 ABC 주식회사의 클라우드 기반 ERP 시스템 구축을 목표로 합니다.
기존 레거시 ERP 시스템을 최신 클라우드 인프라로 전환하여 업무 효율성을 극대화하고,
실시간 데이터 분석 및 의사결정을 지원합니다.

프로젝트 기간: 6개월
예산: 5억원
주요 범위: 재무, 인사, 구매, 재고 관리 모듈""",

        understanding="""ABC 주식회사는 현재 15년 이상 사용해온 레거시 ERP 시스템의 한계를 극복하고자 합니다.
주요 과제는 다음과 같습니다:

1. 시스템 노후화로 인한 유지보수 어려움
2. 클라우드 네이티브 환경으로의 전환 필요성
3. 실시간 데이터 처리 및 분석 요구사항 증대
4. 모바일 및 원격 근무 환경 지원 필요

우리는 이러한 요구사항을 충분히 이해하고 있으며, 최적의 솔루션을 제공하겠습니다.""",

        approach="""1. 단계별 마이그레이션 전략
   - Phase 1: 분석 및 설계 (2개월)
   - Phase 2: 개발 및 통합 (3개월)
   - Phase 3: 테스트 및 배포 (1개월)

2. 클라우드 우선 아키텍처
   - AWS 또는 Azure 기반 인프라
   - 마이크로서비스 아키텍처 적용
   - 컨테이너 오케스트레이션 (Kubernetes)

3. 데이터 중심 설계
   - 실시간 데이터 파이프라인 구축
   - BI 도구 통합
   - 데이터 거버넌스 프레임워크""",

        methodology="""### 애자일 기반 개발 방법론

1. **스프린트 기반 개발**
   - 2주 단위 스프린트
   - 데일리 스탠드업 미팅
   - 스프린트 회고 및 개선

2. **CI/CD 파이프라인**
   - 자동화된 빌드 및 배포
   - 코드 품질 자동 검증
   - 무중단 배포 전략

3. **품질 보증**
   - 단위 테스트 커버리지 80% 이상
   - 통합 테스트 자동화
   - 성능 테스트 및 부하 테스트

4. **문서화**
   - API 문서 자동 생성
   - 사용자 매뉴얼 제공
   - 기술 문서 작성""",

        schedule="""### 프로젝트 일정 (6개월)

**1-2개월: 분석 및 설계**
- 현황 분석 및 요구사항 정의
- 아키텍처 설계
- 데이터 마이그레이션 계획 수립

**3-5개월: 개발 및 통합**
- 모듈별 개발 (재무, 인사, 구매, 재고)
- 레거시 시스템 통합
- 데이터 마이그레이션 수행

**6개월: 테스트 및 배포**
- 통합 테스트 및 UAT
- 성능 최적화
- 프로덕션 배포
- 사용자 교육 및 지원

**마일스톤**
- M1: 요구사항 확정 (1개월 차)
- M2: 설계 완료 (2개월 차)
- M3: 개발 완료 (5개월 차)
- M4: 배포 완료 (6개월 차)""",

        team_composition="""### 프로젝트 조직 구성

**프로젝트 관리**
- PM (1명): 전체 프로젝트 관리 및 의사결정
- PMO (1명): 일정 관리 및 이슈 추적

**개발팀**
- 솔루션 아키텍트 (1명): 시스템 아키텍처 설계
- 백엔드 개발자 (3명): API 및 비즈니스 로직 개발
- 프론트엔드 개발자 (2명): UI/UX 개발
- DBA (1명): 데이터베이스 설계 및 최적화

**품질 관리**
- QA 엔지니어 (2명): 테스트 계획 및 수행
- DevOps 엔지니어 (1명): CI/CD 파이프라인 구축

**총 투입 인력: 12명**
**평균 투입률: 80%**""",

        expected_outcomes="""### 기대 효과

**1. 업무 효율성 향상**
- 업무 처리 시간 30% 단축
- 실시간 데이터 접근 및 분석
- 모바일 환경 지원으로 생산성 향상

**2. 비용 절감**
- 유지보수 비용 40% 감소
- 인프라 비용 최적화
- 라이선스 비용 절감

**3. 확장성 및 유연성**
- 클라우드 기반 탄력적 확장
- 신규 모듈 추가 용이
- 다양한 시스템 통합 가능

**4. 데이터 활용**
- 실시간 BI 대시보드
- 데이터 기반 의사결정 지원
- 예측 분석 및 인사이트 제공

**정량적 효과**
- ROI: 18개월 내 투자 회수
- 업무 효율성: 30% 향상
- 시스템 가용성: 99.9% 보장""",

        budget_plan="예산 5억원 (상세 내역은 별도 제공)"
    )

    print("\nMock 콘텐츠 준비 완료")
    print(f"  - 총 {len(mock_content.model_dump())} 개 섹션")

    # 출력 디렉토리 생성
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n" + "=" * 60)
    print("1. DOCX 문서 생성")
    print("=" * 60)

    docx_path = output_dir / f"test_proposal_{timestamp}.docx"
    try:
        result_path = build_docx(mock_content, "클라우드 ERP 시스템 구축", docx_path)
        print(f"[SUCCESS] DOCX 생성 완료: {result_path}")
        print(f"  - 파일 크기: {result_path.stat().st_size} bytes")
    except Exception as e:
        print(f"[ERROR] DOCX 생성 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("2. PPTX 문서 생성")
    print("=" * 60)

    pptx_path = output_dir / f"test_proposal_{timestamp}.pptx"
    try:
        result_path = build_pptx(mock_content, "클라우드 ERP 시스템 구축", pptx_path)
        print(f"[SUCCESS] PPTX 생성 완료: {result_path}")
        print(f"  - 파일 크기: {result_path.stat().st_size} bytes")
    except Exception as e:
        print(f"[ERROR] PPTX 생성 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("[COMPLETE] 테스트 완료!")
    print("=" * 60)
    print(f"\n생성된 파일:")
    if docx_path.exists():
        print(f"  - Word:  {docx_path}")
    if pptx_path.exists():
        print(f"  - PPT:   {pptx_path}")


if __name__ == "__main__":
    test_document_builders()
