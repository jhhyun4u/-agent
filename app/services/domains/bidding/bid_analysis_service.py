"""
공고 분석 서비스 — G2B 공고 → 마크다운 분석 문서 생성

3가지 분석 문서 생성:
1. RFP分析: 사업개요, 평가항목, 기술요구사항, 가격평가, 우리의 강점/약점, 경쟁강도, 제안전략
2. 공고문: 공고 요약
3. 과업지시서: 과업 범위, 요구사항, 일정

모든 문서는 Supabase Storage에 저장되고, bid_announcements에 경로 기록.
"""

import logging
from typing import Any

from app.services.core.claude_client import claude_generate
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def generate_bid_analysis_documents(
    bid_no: str,
    bid_title: str,
    agency: str,
    budget_amount: int | None,
    deadline_date: str,
    raw_data: dict[str, Any],
) -> dict[str, str]:
    """공고 분석 → 3가지 마크다운 문서 생성 및 Storage 저장.

    Args:
        bid_no: G2B 공고번호
        bid_title: 공고제목
        agency: 발주기관
        budget_amount: 예정가격
        deadline_date: 공고마감일
        raw_data: G2B API 응답 (구조화된 데이터)

    Returns:
        {
            "md_rfp_analysis_path": "bids/{bid_no}/rfp_analysis.md",
            "md_notice_path": "bids/{bid_no}/notice.md",
            "md_instruction_path": "bids/{bid_no}/instruction.md"
        }
    """
    logger.info(f"[Bid Analysis] 시작: bid_no={bid_no}, title={bid_title}")

    # 3가지 문서 생성 (병렬 처리는 하지 않고 순차적으로)
    rfp_analysis_md = await _generate_rfp_analysis_md(
        bid_no=bid_no,
        bid_title=bid_title,
        agency=agency,
        budget_amount=budget_amount,
        deadline_date=deadline_date,
        raw_data=raw_data,
    )

    notice_md = await _generate_notice_md(
        bid_no=bid_no,
        bid_title=bid_title,
        agency=agency,
        budget_amount=budget_amount,
        deadline_date=deadline_date,
    )

    instruction_md = await _generate_instruction_md(
        bid_no=bid_no,
        bid_title=bid_title,
        raw_data=raw_data,
    )

    # Supabase Storage에 저장
    client = await get_async_client()
    bucket_name = "documents"

    # 폴더 경로: bids/{bid_no}/
    folder = f"bids/{bid_no}"

    # 문서 저장 (덮어쓰기 모드)
    # NOTE: Supabase Storage는 ASCII 문자만 지원하므로 romanized 파일명 사용
    rfp_path = f"{folder}/rfp_analysis.md"
    notice_path = f"{folder}/notice.md"
    instruction_path = f"{folder}/instruction.md"

    try:
        # RFP 분석 저장
        try:
            await client.storage.from_(bucket_name).upload(
                rfp_path,
                rfp_analysis_md.encode("utf-8"),
                file_options={"cacheControl": "3600", "upsert": "true"},  # type: ignore
            )
            logger.info(f"✓ RFP Analysis saved: {rfp_path}")
        except Exception as e:
            logger.error(f"✗ RFP Analysis save failed: {str(e)}")
            raise

        # 공고문 저장
        try:
            await client.storage.from_(bucket_name).upload(
                notice_path,
                notice_md.encode("utf-8"),
                file_options={"cacheControl": "3600", "upsert": "true"},  # type: ignore
            )
            logger.info(f"✓ Notice saved: {notice_path}")
        except Exception as e:
            logger.error(f"✗ Notice save failed: {str(e)}")
            raise

        # 과업지시서 저장
        try:
            await client.storage.from_(bucket_name).upload(
                instruction_path,
                instruction_md.encode("utf-8"),
                file_options={"cacheControl": "3600", "upsert": "true"},  # type: ignore
            )
            logger.info(f"✓ Instruction saved: {instruction_path}")
        except Exception as e:
            logger.error(f"✗ Instruction save failed: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"[Bid Analysis] Storage save failed: {str(e)}")
        raise

    return {
        "md_rfp_analysis_path": rfp_path,
        "md_notice_path": notice_path,
        "md_instruction_path": instruction_path,
    }


async def _generate_rfp_analysis_md(
    bid_no: str,
    bid_title: str,
    agency: str,
    budget_amount: int | None,
    deadline_date: str,
    content_text: str,
    raw_data: dict[str, Any],
) -> str:
    """RFP分析 마크다운 생성: 사업개요, 평가항목, 기술요구사항, 가격평가, 강점/약점, 경쟁강도, 제안전략"""

    logger.info(f"[RFP分析] 생성 중: {bid_no}")

    prompt = f"""당신은 한국 정부 용역 제안 전문가입니다. 아래 공고 정보를 분석하여 제안전략 수립에 필요한 RFP分析 마크다운을 작성하세요.

## 공고 정보
- 공고번호: {bid_no}
- 공고제목: {bid_title}
- 발주기관: {agency}
- 예정가격: {budget_amount:,}원 (미정) if {budget_amount is None}
- 마감일: {deadline_date}
- 공고문 내용: {content_text[:5000]}...  (생략)

## 생성할 RFP分析 (마크다운 형식)

다음 섹션을 포함하여 마크다운으로 작성하세요:

1. **사업 개요**
   - 발주기관, 사업명, 예정가격, 마감일 정리

2. **평가 항목 & 배점**
   - 기술점수, 가격점수, 기타점수 등
   - 배점 비율 분석

3. **기술 요구사항**
   - 핵심 요구사항 3~5개
   - 필수 자격요건

4. **가격 평가 산식**
   - 낙찰가 결정 방식
   - 최저가 부터의 구간별 점수

5. **핵심 요구사항**
   - 우리가 주목해야 할 요구사항 3~5개

6. **우리 회사의 강점/약점** (점수 매기기)
   - 🟢 강점 (우리가 잘할 수 있는 항목)
   - 🟡 중점 (개선 필요한 항목)
   - 🔴 약점 (보강 필요한 항목)

7. **경쟁 강도**
   - 예상되는 경쟁사, 경쟁 강도 수준

8. **제안 전략**
   - 포지셔닝 방향 (예: 기술선도, 가성비, 경험, 혁신)
   - 차별화 포인트 3~5개

마크다운으로 작성하고, 목록은 불릿(-) 형식 사용하세요."""

    try:
        result = await claude_generate(
            prompt=prompt,
            response_format="text",
            step_name="bid_analysis_rfp",
            max_tokens=3000,
        )
        return result.get("text", "")
    except Exception as e:
        logger.error(f"[RFP分析] Claude 생성 실패: {str(e)}")
        raise


async def _generate_notice_md(
    bid_no: str,
    bid_title: str,
    agency: str,
    budget_amount: int | None,
    deadline_date: str,
    content_text: str,
) -> str:
    """공고문 요약 마크다운 생성"""

    logger.info(f"[공고문] 생성 중: {bid_no}")

    prompt = f"""당신은 한국 정부 용역 제안 전문가입니다. 아래 공고 정보를 요약하여 공고문 마크다운을 작성하세요.

## 공고 원본
- 공고번호: {bid_no}
- 공고제목: {bid_title}
- 발주기관: {agency}
- 예정가격: {budget_amount:,}원 if {budget_amount} else '미정'
- 마감일: {deadline_date}
- 내용: {content_text[:3000]}...

## 생성할 공고문 마크다운

1. **기본 정보**
   - 공고번호, 제목, 발주기관, 예정가격, 마감일

2. **사업 목적**
   - 사업의 목적과 추진 배경

3. **사업 범위**
   - 과업의 범위와 규모

4. **필수 요건**
   - 자격요건, 필수 경험, 인력요건

5. **제출 서류**
   - 제출해야 할 주요 서류 목록

6. **평가 방식**
   - 기술점수, 가격점수 등

마크다운 형식으로 작성하세요."""

    try:
        result = await claude_generate(
            prompt=prompt,
            response_format="text",
            step_name="bid_analysis_notice",
            max_tokens=2000,
        )
        return result.get("text", "")
    except Exception as e:
        logger.error(f"[공고문] Claude 생성 실패: {str(e)}")
        raise


async def _generate_instruction_md(
    bid_no: str,
    bid_title: str,
    content_text: str,
    raw_data: dict[str, Any],
) -> str:
    """과업지시서 마크다운 생성"""

    logger.info(f"[과업지시서] 생성 중: {bid_no}")

    prompt = f"""당신은 한국 정부 용역 제안 전문가입니다. 아래 공고를 분석하여 과업지시서 마크다운을 작성하세요.

## 공고 정보
- 공고번호: {bid_no}
- 공고제목: {bid_title}
- 내용 (발췌): {content_text[:3000]}...

## 생성할 과업지시서 마크다운

1. **과업 목적**
   - 용역의 최종 목표

2. **과업 범위**
   - 포함되는 업무
   - 제외되는 업무

3. **과업 기간**
   - 예상 수행 기간

4. **주요 산출물**
   - 최종 산출물 목록 및 형식

5. **수행 방법**
   - 단계별 수행 방식
   - 필수 점검/승인 절차

6. **인력 및 기술**
   - 필수 기술요건
   - 인력 구성 요건

7. **납기 및 완료 기준**
   - 각 단계별 납기일정
   - 완료 판정 기준

마크다운 형식으로 작성하세요."""

    try:
        result = await claude_generate(
            prompt=prompt,
            response_format="text",
            step_name="bid_analysis_instruction",
            max_tokens=2000,
        )
        return result.get("text", "")
    except Exception as e:
        logger.error(f"[과업지시서] Claude 생성 실패: {str(e)}")
        raise
