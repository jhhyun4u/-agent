"""
최종 검토 모듈 상세 구현
PPT 생성 및 최종 검토 프로세스
"""

from typing import Dict, List, Any, Tuple, Optional
import asyncio
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from pathlib import Path
import json

class ReviewStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"

class PPTSection(Enum):
    TITLE = "title"
    EXECUTIVE_SUMMARY = "executive_summary"
    COMPANY_OVERVIEW = "company_overview"
    SOLUTION_OVERVIEW = "solution_overview"
    TECHNICAL_APPROACH = "technical_approach"
    PROJECT_PLAN = "project_plan"
    TEAM_COMPOSITION = "team_composition"
    BUDGET_BREAKDOWN = "budget_breakdown"
    RISK_MANAGEMENT = "risk_management"
    CONCLUSION = "conclusion"

class ReviewPriority(Enum):
    CRITICAL = "critical"      # 심각한 문제
    HIGH = "high"             # 높은 우선순위
    MEDIUM = "medium"         # 중간 우선순위
    LOW = "low"              # 낮은 우선순위

@dataclass
class ReviewComment:
    """검토 의견"""
    comment_id: str
    reviewer: str
    section: str
    priority: ReviewPriority
    comment: str
    suggestion: str
    status: ReviewStatus
    timestamp: datetime

@dataclass
class PPTSlide:
    """PPT 슬라이드"""
    slide_id: str
    section: PPTSection
    title: str
    content: Dict[str, Any]  # 슬라이드 내용 (텍스트, 차트, 이미지 등)
    layout: str
    notes: str
    order: int

@dataclass
class FinalReviewResult:
    """최종 검토 결과"""
    proposal_doc_path: Optional[str]
    ppt_path: Optional[str]
    review_comments: List[ReviewComment]
    overall_score: float
    approval_status: ReviewStatus
    final_recommendations: List[str]
    submission_ready: bool

class FinalReviewEngine:
    """최종 검토 엔진"""

    def __init__(self):
        self.ppt_templates = self._load_ppt_templates()
        self.review_checklist = self._load_review_checklist()

    async def conduct_final_review(self, proposal_content: Dict, strategy_result: Dict,
                                 parallel_work_result: Dict, rfp_analysis: Dict,
                                 company_profile: Dict) -> FinalReviewResult:
        """
        최종 검토 및 PPT 생성 실행

        Args:
            proposal_content: 제안서 내용
            strategy_result: 전략 수립 결과
            parallel_work_result: 병렬 작업 결과
            rfp_analysis: RFP 분석 결과
            company_profile: 회사 프로필

        Returns:
            FinalReviewResult: 최종 검토 결과
        """

        # 1. 제안서 최종 검토
        review_comments = await self._conduct_comprehensive_review(
            proposal_content, strategy_result, parallel_work_result, rfp_analysis
        )

        # 2. PPT 생성
        ppt_slides = await self._generate_ppt_presentation(
            proposal_content, strategy_result, parallel_work_result, rfp_analysis, company_profile
        )

        # 3. PPT 파일 생성 (시뮬레이션)
        ppt_path = await self._create_ppt_file(ppt_slides, rfp_analysis["basic_info"]["title"])

        # 4. 제안서 문서 생성 (시뮬레이션)
        proposal_doc_path = await self._create_proposal_document(proposal_content, rfp_analysis)

        # 5. 최종 승인 평가
        overall_score, approval_status = self._calculate_final_score(review_comments)

        # 6. 최종 권고사항
        final_recommendations = self._generate_final_recommendations(
            review_comments, approval_status, rfp_analysis
        )

        # 7. 제출 준비 상태 결정
        submission_ready = self._assess_submission_readiness(
            approval_status, review_comments, ppt_path, proposal_doc_path
        )

        result = FinalReviewResult(
            proposal_doc_path=proposal_doc_path,
            ppt_path=ppt_path,
            review_comments=review_comments,
            overall_score=overall_score,
            approval_status=approval_status,
            final_recommendations=final_recommendations,
            submission_ready=submission_ready
        )

        return result

    async def _conduct_comprehensive_review(self, proposal_content: Dict, strategy_result: Dict,
                                          parallel_work_result: Dict, rfp_analysis: Dict) -> List[ReviewComment]:
        """종합 검토 실행"""

        comments = []

        # 1. 전략 일관성 검토
        strategy_comments = await self._review_strategy_alignment(
            proposal_content, strategy_result, rfp_analysis
        )
        comments.extend(strategy_comments)

        # 2. 기술적 완전성 검토
        technical_comments = await self._review_technical_completeness(
            proposal_content, parallel_work_result, rfp_analysis
        )
        comments.extend(technical_comments)

        # 3. 사업적 타당성 검토
        business_comments = await self._review_business_viability(
            proposal_content, strategy_result, company_profile
        )
        comments.extend(business_comments)

        # 4. 준수사항 검토
        compliance_comments = await self._review_compliance_requirements(
            proposal_content, rfp_analysis
        )
        comments.extend(compliance_comments)

        # 5. 품질 및 완성도 검토
        quality_comments = await self._review_quality_and_completeness(
            proposal_content, parallel_work_result
        )
        comments.extend(quality_comments)

        return comments

    async def _review_strategy_alignment(self, proposal_content: Dict, strategy_result: Dict,
                                       rfp_analysis: Dict) -> List[ReviewComment]:
        """전략 일관성 검토"""

        comments = []

        # 승점 전략 일관성 확인
        winning_points = strategy_result.get("winning_points", [])
        proposal_strategy = self._extract_strategy_from_proposal(proposal_content)

        for point in winning_points:
            if point["score"] > 0.7:  # 높은 승점
                alignment = self._check_strategy_alignment(point, proposal_strategy)
                if alignment < 0.7:
                    comment = ReviewComment(
                        comment_id=f"strategy_{point['factor'].replace(' ', '_')}",
                        reviewer="전략 검토자",
                        section="전체 제안서",
                        priority=ReviewPriority.HIGH if point["impact"] > 0.8 else ReviewPriority.MEDIUM,
                        comment=f"{point['factor']} 승점이 제안서에 충분히 반영되지 않았습니다.",
                        suggestion=f"{point['factor']}를 강조하는 내용 추가 및 구체적 근거 제시",
                        status=ReviewStatus.REVISION_REQUIRED,
                        timestamp=datetime.now()
                    )
                    comments.append(comment)

        return comments

    async def _review_technical_completeness(self, proposal_content: Dict,
                                           parallel_work_result: Dict,
                                           rfp_analysis: Dict) -> List[ReviewComment]:
        """기술적 완전성 검토"""

        comments = []

        # RFP 기술 요구사항 확인
        required_tech = rfp_analysis["requirements"].get("technical_requirements", [])
        proposed_tech = self._extract_technical_proposals(proposal_content)

        for req in required_tech:
            if req not in proposed_tech:
                comment = ReviewComment(
                    comment_id=f"tech_missing_{req.replace(' ', '_')}",
                    reviewer="기술 검토자",
                    section="기술 아키텍처",
                    priority=ReviewPriority.CRITICAL,
                    comment=f"필수 기술 요구사항 '{req}'이 제안서에 포함되지 않았습니다.",
                    suggestion=f"'{req}' 기술에 대한 구체적인 구현 방안 및 근거 추가",
                    status=ReviewStatus.REVISION_REQUIRED,
                    timestamp=datetime.now()
                )
                comments.append(comment)

        # 모의 평가 결과 반영
        mock_evaluations = parallel_work_result.get("mock_evaluations", [])
        technical_evals = [e for e in mock_evaluations if "기술" in e.criteria and e.score < 0.7]

        for eval in technical_evals:
            comment = ReviewComment(
                comment_id=f"tech_eval_{eval.evaluation_id}",
                reviewer="품질 검증자",
                section="기술 제안",
                priority=ReviewPriority.HIGH,
                comment=f"기술 평가에서 낮은 점수: {eval.feedback}",
                suggestion=f"평가 피드백 반영: {', '.join(eval.recommendations)}",
                status=ReviewStatus.REVISION_REQUIRED,
                timestamp=datetime.now()
            )
            comments.append(comment)

        return comments

    async def _review_business_viability(self, proposal_content: Dict, strategy_result: Dict,
                                       company_profile: Dict) -> List[ReviewComment]:
        """사업적 타당성 검토"""

        comments = []

        # 가격 전략 검토
        price_strategy = strategy_result.get("price_strategy")
        proposed_price = self._extract_proposed_price(proposal_content)

        if price_strategy and proposed_price:
            price_alignment = self._check_price_alignment(price_strategy, proposed_price)
            if price_alignment < 0.8:
                comment = ReviewComment(
                    comment_id="price_strategy_mismatch",
                    reviewer="사업 검토자",
                    section="가격 제안",
                    priority=ReviewPriority.HIGH,
                    comment="수립된 가격 전략과 실제 제안 가격이 일치하지 않습니다.",
                    suggestion="가격 전략에 따른 가격 조정 또는 전략 재검토",
                    status=ReviewStatus.REVISION_REQUIRED,
                    timestamp=datetime.now()
                )
                comments.append(comment)

        # 사업성 분석 검토
        business_case = self._extract_business_case(proposal_content)
        if not business_case.get("roi_analysis"):
            comment = ReviewComment(
                comment_id="missing_roi_analysis",
                reviewer="사업 검토자",
                section="사업성 분석",
                priority=ReviewPriority.MEDIUM,
                comment="ROI 분석 및 경제성 평가가 부족합니다.",
                suggestion="투자 수익률 분석 및 경제성 평가 지표 추가",
                status=ReviewStatus.REVISION_REQUIRED,
                timestamp=datetime.now()
            )
            comments.append(comment)

        return comments

    async def _review_compliance_requirements(self, proposal_content: Dict,
                                            rfp_analysis: Dict) -> List[ReviewComment]:
        """준수사항 검토"""

        comments = []

        # 자격 요건 준수 확인
        required_qualifications = rfp_analysis["requirements"].get("qualification_requirements", [])
        claimed_qualifications = self._extract_qualifications(proposal_content)

        for req_qual in required_qualifications:
            if req_qual not in claimed_qualifications:
                comment = ReviewComment(
                    comment_id=f"qual_missing_{req_qual.replace(' ', '_')}",
                    reviewer="준수 검토자",
                    section="자격 요건",
                    priority=ReviewPriority.CRITICAL,
                    comment=f"필수 자격 '{req_qual}'이 누락되었거나 불충분합니다.",
                    suggestion=f"'{req_qual}' 자격에 대한 구체적인 증빙 자료 추가",
                    status=ReviewStatus.REVISION_REQUIRED,
                    timestamp=datetime.now()
                )
                comments.append(comment)

        # 법적 준수사항 확인
        legal_requirements = rfp_analysis["requirements"].get("compliance_requirements", [])
        legal_compliance = self._check_legal_compliance(proposal_content, legal_requirements)

        for req in legal_requirements:
            if not legal_compliance.get(req, False):
                comment = ReviewComment(
                    comment_id=f"legal_{req.replace(' ', '_')}",
                    reviewer="법무 검토자",
                    section="준수사항",
                    priority=ReviewPriority.HIGH,
                    comment=f"법적 요구사항 '{req}' 준수가 확인되지 않습니다.",
                    suggestion=f"'{req}' 준수를 위한 구체적인 조치 및 증빙 추가",
                    status=ReviewStatus.REVISION_REQUIRED,
                    timestamp=datetime.now()
                )
                comments.append(comment)

        return comments

    async def _review_quality_and_completeness(self, proposal_content: Dict,
                                             parallel_work_result: Dict) -> List[ReviewComment]:
        """품질 및 완성도 검토"""

        comments = []

        # 체크리스트 완료도 검토
        checklist = parallel_work_result.get("checklist", [])
        incomplete_critical = [
            item for item in checklist
            if not item.is_completed and item.priority >= 4
        ]

        if incomplete_critical:
            comment = ReviewComment(
                comment_id="incomplete_checklist",
                reviewer="품질 검토자",
                section="전체 문서",
                priority=ReviewPriority.HIGH,
                comment=f"중요 체크리스트 항목 {len(incomplete_critical)}건이 미완료되었습니다.",
                suggestion=f"미완료 항목 우선 처리: {[item.title for item in incomplete_critical[:3]]}",
                status=ReviewStatus.REVISION_REQUIRED,
                timestamp=datetime.now()
            )
            comments.append(comment)

        # 문서 완성도 검토
        completeness_score = self._assess_document_completeness(proposal_content)
        if completeness_score < 0.8:
            comment = ReviewComment(
                comment_id="document_incomplete",
                reviewer="품질 검토자",
                section="전체 문서",
                priority=ReviewPriority.MEDIUM,
                comment=f"문서 완성도가 {completeness_score:.1%}로 낮습니다.",
                suggestion="누락된 섹션 및 내용 보완",
                status=ReviewStatus.REVISION_REQUIRED,
                timestamp=datetime.now()
            )
            comments.append(comment)

        return comments

    async def _generate_ppt_presentation(self, proposal_content: Dict, strategy_result: Dict,
                                       parallel_work_result: Dict, rfp_analysis: Dict,
                                       company_profile: Dict) -> List[PPTSlide]:
        """PPT 프레젠테이션 생성"""

        slides = []

        # 슬라이드 템플릿에 따른 생성
        slide_order = [
            PPTSection.TITLE,
            PPTSection.EXECUTIVE_SUMMARY,
            PPTSection.COMPANY_OVERVIEW,
            PPTSection.SOLUTION_OVERVIEW,
            PPTSection.TECHNICAL_APPROACH,
            PPTSection.PROJECT_PLAN,
            PPTSection.TEAM_COMPOSITION,
            PPTSection.BUDGET_BREAKDOWN,
            PPTSection.RISK_MANAGEMENT,
            PPTSection.CONCLUSION
        ]

        for i, section in enumerate(slide_order):
            slide_content = await self._generate_slide_content(
                section, proposal_content, strategy_result, parallel_work_result,
                rfp_analysis, company_profile
            )

            slide = PPTSlide(
                slide_id=f"slide_{i+1:02d}",
                section=section,
                title=slide_content["title"],
                content=slide_content["content"],
                layout=slide_content["layout"],
                notes=slide_content["notes"],
                order=i+1
            )
            slides.append(slide)

        return slides

    async def _generate_slide_content(self, section: PPTSection, proposal_content: Dict,
                                    strategy_result: Dict, parallel_work_result: Dict,
                                    rfp_analysis: Dict, company_profile: Dict) -> Dict[str, Any]:
        """슬라이드 내용 생성"""

        content_templates = self.ppt_templates.get(section.value, {})

        if section == PPTSection.TITLE:
            return {
                "title": rfp_analysis["basic_info"]["title"],
                "content": {
                    "subtitle": f"제안사: {company_profile.get('name', '회사명')}",
                    "date": datetime.now().strftime("%Y년 %m월 %d일"),
                    "presenter": company_profile.get('presenter', '대표자명')
                },
                "layout": "title_slide",
                "notes": "제목 슬라이드 - 청중의 관심을 끌 수 있도록 간결하게"
            }

        elif section == PPTSection.EXECUTIVE_SUMMARY:
            winning_points = strategy_result.get("winning_points", [])
            top_points = sorted(winning_points, key=lambda x: x["score"], reverse=True)[:3]

            return {
                "title": "Executive Summary",
                "content": {
                    "key_points": [point["factor"] for point in top_points],
                    "value_proposition": strategy_result.get("competitive_advantages", []),
                    "budget": f"₩{rfp_analysis['basic_info']['budget']:,}"
                },
                "layout": "bullet_points",
                "notes": "핵심 가치 제안과 차별화 포인트를 30초 안에 전달"
            }

        elif section == PPTSection.TECHNICAL_APPROACH:
            technical_content = proposal_content.get("technical_approach", {})

            return {
                "title": "기술적 접근방법",
                "content": {
                    "architecture": technical_content.get("architecture", "시스템 아키텍처"),
                    "technologies": technical_content.get("technologies", []),
                    "innovation": technical_content.get("innovation_points", [])
                },
                "layout": "architecture_diagram",
                "notes": "기술적 우위와 혁신성을 시각적으로 표현"
            }

        # 다른 섹션들도 유사하게 구현...

        return {
            "title": section.value,
            "content": {},
            "layout": "default",
            "notes": ""
        }

    async def _create_ppt_file(self, slides: List[PPTSlide], project_title: str) -> str:
        """PPT 파일 생성 (시뮬레이션)"""

        # 실제 구현에서는 python-pptx 라이브러리 사용
        filename = f"{project_title.replace(' ', '_')}_presentation.pptx"
        file_path = f"output/{filename}"

        # 시뮬레이션: 파일 생성 로깅
        print(f"PPT 파일 생성: {file_path}")
        print(f"총 슬라이드 수: {len(slides)}")

        return file_path

    async def _create_proposal_document(self, proposal_content: Dict, rfp_analysis: Dict) -> str:
        """제안서 문서 생성 (시뮬레이션)"""

        # 실제 구현에서는 python-docx 라이브러리 사용
        filename = f"{rfp_analysis['basic_info']['title'].replace(' ', '_')}_proposal.docx"
        file_path = f"output/{filename}"

        # 시뮬레이션: 파일 생성 로깅
        print(f"제안서 문서 생성: {file_path}")

        return file_path

    def _calculate_final_score(self, review_comments: List[ReviewComment]) -> Tuple[float, ReviewStatus]:
        """최종 점수 계산"""

        # 기본 점수
        base_score = 1.0

        # 코멘트별 감점
        penalty_points = 0
        critical_count = 0
        high_count = 0

        for comment in review_comments:
            if comment.priority == ReviewPriority.CRITICAL:
                penalty_points += 0.3
                critical_count += 1
            elif comment.priority == ReviewPriority.HIGH:
                penalty_points += 0.2
                high_count += 1
            elif comment.priority == ReviewPriority.MEDIUM:
                penalty_points += 0.1

        final_score = max(0.0, base_score - penalty_points)

        # 승인 상태 결정
        if critical_count > 0 or final_score < 0.6:
            status = ReviewStatus.REJECTED
        elif high_count > 2 or final_score < 0.8:
            status = ReviewStatus.REVISION_REQUIRED
        else:
            status = ReviewStatus.APPROVED

        return final_score, status

    def _generate_final_recommendations(self, review_comments: List[ReviewComment],
                                      approval_status: ReviewStatus,
                                      rfp_analysis: Dict) -> List[str]:
        """최종 권고사항 생성"""

        recommendations = []

        if approval_status == ReviewStatus.REJECTED:
            recommendations.append("심각한 문제점들을 모두 해결한 후 재검토 요청")
            critical_comments = [c for c in review_comments if c.priority == ReviewPriority.CRITICAL]
            recommendations.append(f"우선 해결 사항: {[c.comment[:50] + '...' for c in critical_comments[:3]]}")

        elif approval_status == ReviewStatus.REVISION_REQUIRED:
            recommendations.append("지적된 문제점들을 수정하여 재제출")
            high_priority_comments = [c for c in review_comments if c.priority in [ReviewPriority.HIGH, ReviewPriority.CRITICAL]]
            recommendations.append(f"주요 수정 사항: {[c.suggestion[:50] + '...' for c in high_priority_comments[:3]]}")

        else:
            recommendations.append("제출 준비 완료 - 최종 승인 대기")
            recommendations.append("발표 준비 및 Q&A 시뮬레이션 권장")

        # RFP 마감일 고려
        duration = rfp_analysis["basic_info"].get("duration_months", 12)
        if duration < 3:
            recommendations.append("긴급 제출 일정 고려하여 우선순위 조정")

        return recommendations

    def _assess_submission_readiness(self, approval_status: ReviewStatus,
                                   review_comments: List[ReviewComment],
                                   ppt_path: str, proposal_doc_path: str) -> bool:
        """제출 준비 상태 평가"""

        # 기본 조건 확인
        if not ppt_path or not proposal_doc_path:
            return False

        # 승인 상태 확인
        if approval_status in [ReviewStatus.REJECTED, ReviewStatus.REVISION_REQUIRED]:
            return False

        # 심각한 문제 없음 확인
        critical_issues = [c for c in review_comments if c.priority == ReviewPriority.CRITICAL]
        if critical_issues:
            return False

        return True

    # 헬퍼 메소드들
    def _load_ppt_templates(self) -> Dict[str, Dict]:
        """PPT 템플릿 로드"""
        return {
            "title": {
                "layout": "title_slide",
                "elements": ["title", "subtitle", "date", "presenter"]
            },
            "executive_summary": {
                "layout": "bullet_points",
                "elements": ["key_points", "value_proposition", "budget"]
            },
            "technical_approach": {
                "layout": "architecture_diagram",
                "elements": ["architecture", "technologies", "innovation"]
            }
        }

    def _load_review_checklist(self) -> List[Dict]:
        """검토 체크리스트 로드"""
        return [
            {
                "category": "technical",
                "item": "기술 요구사항 완전성",
                "priority": "critical"
            },
            {
                "category": "business",
                "item": "가격 적정성",
                "priority": "high"
            },
            {
                "category": "compliance",
                "item": "자격 요건 준수",
                "priority": "critical"
            }
        ]

    def _extract_strategy_from_proposal(self, proposal_content: Dict) -> Dict:
        """제안서에서 전략 추출"""
        return proposal_content.get("strategy", {})

    def _check_strategy_alignment(self, winning_point: Dict, proposal_strategy: Dict) -> float:
        """전략 일관성 점수 계산"""
        # 간단한 일치도 계산
        return 0.8  # 시뮬레이션

    def _extract_technical_proposals(self, proposal_content: Dict) -> List[str]:
        """기술 제안사항 추출"""
        return proposal_content.get("technical_approach", {}).get("technologies", [])

    def _extract_proposed_price(self, proposal_content: Dict) -> Optional[int]:
        """제안 가격 추출"""
        return proposal_content.get("budget", {}).get("total_price")

    def _check_price_alignment(self, price_strategy: Dict, proposed_price: int) -> float:
        """가격 전략 일관성 확인"""
        target_range = price_strategy.get("target_price_range", (0, 0))
        if target_range[0] <= proposed_price <= target_range[1]:
            return 1.0
        else:
            return 0.5

    def _extract_business_case(self, proposal_content: Dict) -> Dict:
        """사업성 분석 추출"""
        return proposal_content.get("business_case", {})

    def _extract_qualifications(self, proposal_content: Dict) -> List[str]:
        """자격 요건 추출"""
        return proposal_content.get("qualifications", [])

    def _check_legal_compliance(self, proposal_content: Dict, requirements: List[str]) -> Dict[str, bool]:
        """법적 준수사항 확인"""
        compliance = {}
        for req in requirements:
            compliance[req] = True  # 시뮬레이션
        return compliance

    def _assess_document_completeness(self, proposal_content: Dict) -> float:
        """문서 완성도 평가"""
        required_sections = ["executive_summary", "technical_approach", "project_plan", "budget"]
        present_sections = [s for s in required_sections if s in proposal_content]
        return len(present_sections) / len(required_sections)</content>
<parameter name="filePath">c:\Users\현재호\OneDrive - 테크노베이션파트너스\바탕 화면\viveproject\tenopa proposer\final_review_engine.py