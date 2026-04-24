"""
제안작업 모듈러 아키텍처 재설계 (4-Module 기반)

현재: 5-Phase 기술 중심 구조
신규: 4-Module 비즈니스 프로세스 중심 구조
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import asyncio

# 모듈 상태 정의
ModuleStatus = Literal["pending", "in_progress", "completed", "failed", "rejected"]

@dataclass
class ModuleResult:
    """모듈 실행 결과"""
    module_id: str
    status: ModuleStatus
    output_data: Dict[str, Any]
    decision: Optional[str] = None  # GO/STOP, 승인/거부 등
    reasoning: str = ""
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ProposalModule(ABC):
    """제안작업 모듈 기본 클래스"""

    def __init__(self, module_id: str, name: str):
        self.module_id = module_id
        self.name = name
        self.status: ModuleStatus = "pending"
        self.result: Optional[ModuleResult] = None

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> ModuleResult:
        """모듈 실행"""
        pass

    @abstractmethod
    async def validate_input(self, context: Dict[str, Any]) -> bool:
        """입력 데이터 검증"""
        pass

    @abstractmethod
    def get_required_inputs(self) -> List[str]:
        """필요한 입력 데이터 목록"""
        pass

# 1. RFP 검토 모듈
class RFPReviewModule(ProposalModule):
    """RFP 검토 및 GO/STOP 결정 모듈"""

    def __init__(self):
        super().__init__("rfp_review", "RFP 검토 및 GO/STOP 결정")

    def get_required_inputs(self) -> List[str]:
        return ["rfp_content", "company_profile", "past_proposals"]

    async def validate_input(self, context: Dict[str, Any]) -> bool:
        required = self.get_required_inputs()
        return all(key in context for key in required)

    async def execute(self, context: Dict[str, Any]) -> ModuleResult:
        self.status = "in_progress"

        try:
            # RFP 파싱 및 분석
            rfp_analysis = await self._analyze_rfp(context["rfp_content"])

            # 수행 가능성 평가
            feasibility = await self._evaluate_feasibility(rfp_analysis, context)

            # GO/STOP 결정
            decision = self._make_go_stop_decision(feasibility)

            output_data = {
                "rfp_analysis": rfp_analysis,
                "feasibility_score": feasibility["score"],
                "feasibility_factors": feasibility["factors"],
                "decision": decision,
                "reasoning": self._generate_reasoning(feasibility, decision)
            }

            self.status = "completed"
            self.result = ModuleResult(
                module_id=self.module_id,
                status="completed",
                output_data=output_data,
                decision=decision,
                reasoning=output_data["reasoning"]
            )

            return self.result

        except Exception as e:
            self.status = "failed"
            raise

    async def _analyze_rfp(self, rfp_content: str) -> Dict[str, Any]:
        """RFP 문서 분석"""
        # 기존 RFP 파싱 로직 활용
        from app.services.domains.proposal.rfp_parser import parse_rfp_text
        rfp_data = await parse_rfp_text(rfp_content)

        return {
            "title": rfp_data.title,
            "client": rfp_data.client_name,
            "scope": rfp_data.project_scope,
            "requirements": rfp_data.requirements,
            "budget": rfp_data.budget,
            "duration": rfp_data.duration,
            "evaluation_criteria": getattr(rfp_data, 'evaluation_criteria', [])
        }

    async def _evaluate_feasibility(self, rfp_analysis: Dict, context: Dict) -> Dict[str, Any]:
        """수행 가능성 평가"""
        factors = []

        # 기술 역량 평가
        tech_score = await self._evaluate_technical_feasibility(rfp_analysis, context)
        factors.append({"aspect": "기술 역량", "score": tech_score, "details": "..."})

        # 자격 요건 평가
        qualification_score = await self._evaluate_qualification(rfp_analysis, context)
        factors.append({"aspect": "자격 요건", "score": qualification_score, "details": "..."})

        # 경쟁력 평가
        competition_score = await self._evaluate_competition(rfp_analysis, context)
        factors.append({"aspect": "경쟁력", "score": competition_score, "details": "..."})

        # 리스크 평가
        risk_score = await self._evaluate_risks(rfp_analysis, context)
        factors.append({"aspect": "리스크", "score": risk_score, "details": "..."})

        # 종합 점수 계산
        total_score = (tech_score + qualification_score + competition_score + risk_score) / 4

        return {
            "score": total_score,
            "factors": factors,
            "recommendation": "GO" if total_score >= 0.7 else "STOP"
        }

    def _make_go_stop_decision(self, feasibility: Dict) -> str:
        """GO/STOP 결정"""
        if feasibility["score"] >= 0.8:
            return "GO"
        elif feasibility["score"] >= 0.6:
            return "CONDITIONAL_GO"  # 조건부 진행
        else:
            return "STOP"

    def _generate_reasoning(self, feasibility: Dict, decision: str) -> str:
        """결정 근거 생성"""
        reasoning_parts = [f"종합 점수: {feasibility['score']:.2f}"]

        for factor in feasibility["factors"]:
            reasoning_parts.append(f"- {factor['aspect']}: {factor['score']:.2f}")

        reasoning_parts.append(f"결정: {decision}")

        return "\n".join(reasoning_parts)

    async def _evaluate_technical_feasibility(self, rfp: Dict, context: Dict) -> float:
        """기술 역량 평가"""
        # 구현 필요
        return 0.8

    async def _evaluate_qualification(self, rfp: Dict, context: Dict) -> float:
        """자격 요건 평가"""
        # 구현 필요
        return 0.7

    async def _evaluate_competition(self, rfp: Dict, context: Dict) -> float:
        """경쟁력 평가"""
        # 구현 필요
        return 0.6

    async def _evaluate_risks(self, rfp: Dict, context: Dict) -> float:
        """리스크 평가"""
        # 구현 필요
        return 0.8

# 2. 전략 수립 모듈
class StrategyPlanningModule(ProposalModule):
    """제안전략 수립 및 승인 모듈"""

    def __init__(self):
        super().__init__("strategy_planning", "제안전략 수립 및 승인")

    def get_required_inputs(self) -> List[str]:
        return ["rfp_analysis", "feasibility_analysis", "company_profile", "past_proposals"]

    async def validate_input(self, context: Dict[str, Any]) -> bool:
        required = self.get_required_inputs()
        return all(key in context for key in required)

    async def execute(self, context: Dict[str, Any]) -> ModuleResult:
        self.status = "in_progress"

        try:
            # 전략 요소 개발
            strategy_elements = await self._develop_strategy_elements(context)

            # Winning Point 결정
            winning_points = await self._identify_winning_points(strategy_elements, context)

            # 차별화 스토리 개발
            differentiation_story = await self._develop_differentiation_story(winning_points, context)

            # Bidding 가격 결정
            bidding_price = await self._determine_bidding_price(strategy_elements, context)

            # 전략 검토용 요약
            strategy_summary = self._create_strategy_summary(
                strategy_elements, winning_points, differentiation_story, bidding_price
            )

            output_data = {
                "strategy_elements": strategy_elements,
                "winning_points": winning_points,
                "differentiation_story": differentiation_story,
                "bidding_price": bidding_price,
                "strategy_summary": strategy_summary,
                "requires_approval": True
            }

            self.status = "completed"
            self.result = ModuleResult(
                module_id=self.module_id,
                status="completed",
                output_data=output_data,
                decision="PENDING_APPROVAL",
                reasoning="전략 수립 완료. 승인 대기 중."
            )

            return self.result

        except Exception as e:
            self.status = "failed"
            raise

    async def _develop_strategy_elements(self, context: Dict) -> Dict[str, Any]:
        """전략 요소 개발"""
        # 기존 Phase 3 로직 활용
        return {
            "core_message": "혁신적인 솔루션 제공",
            "win_themes": ["기술 우위", "가격 경쟁력", "신뢰성"],
            "differentiators": ["독자적 기술", "빠른 구축", "맞춤형 서비스"],
            "personnel_assignments": [],
            "section_plans": []
        }

    async def _identify_winning_points(self, strategy_elements: Dict, context: Dict) -> List[Dict]:
        """Winning Point 결정"""
        return [
            {
                "point": "기술 우위",
                "description": "독자적 알고리즘으로 성능 30% 향상",
                "evidence": "특허 보유 및 실적 검증",
                "impact": "고객 만족도 및 경쟁력 확보"
            }
        ]

    async def _develop_differentiation_story(self, winning_points: List, context: Dict) -> Dict[str, Any]:
        """차별화 스토리 개발"""
        return {
            "narrative": "고객의 문제를 혁신적으로 해결하는 파트너",
            "key_messages": ["기술 리더십", "신뢰할 수 있는 파트너", "가치 중심 솔루션"],
            "story_elements": ["문제 인식", "해결 방안", "성과 증거", "미래 비전"]
        }

    async def _determine_bidding_price(self, strategy_elements: Dict, context: Dict) -> Dict[str, Any]:
        """Bidding 가격 결정"""
        return {
            "base_price": 100000000,  # 1억원
            "strategy_adjustment": -5000000,  # 전략적 조정
            "final_price": 95000000,  # 9,500만원
            "reasoning": "시장 평균 대비 5% 할인으로 경쟁력 확보"
        }

    def _create_strategy_summary(self, elements: Dict, winning_points: List,
                               story: Dict, price: Dict) -> str:
        """전략 검토용 요약 생성"""
        lines = [
            "📊 제안 전략 요약",
            "",
            f"🎯 핵심 메시지: {elements.get('core_message', '')}",
            "",
            "🏆 Winning Points:"
        ]

        for wp in winning_points:
            lines.append(f"  • {wp['point']}: {wp['description']}")

        lines.extend([
            "",
            f"💰 제안 가격: {price['final_price']:,}원",
            f"📝 가격 전략: {price['reasoning']}",
            "",
            "🔄 다음 단계: 전략 승인 대기"
        ])

        return "\n".join(lines)

# 3. 병렬 작업 모듈
class ParallelWorkModule(ProposalModule):
    """병렬 제안작업 수행 모듈"""

    def __init__(self):
        super().__init__("parallel_work", "병렬 제안작업 수행")

    def get_required_inputs(self) -> List[str]:
        return ["strategy_approved", "rfp_analysis", "strategy_plan"]

    async def validate_input(self, context: Dict[str, Any]) -> bool:
        required = self.get_required_inputs()
        return all(key in context for key in required)

    async def execute(self, context: Dict[str, Any]) -> ModuleResult:
        self.status = "in_progress"

        try:
            # Agent Teams 구성
            agent_teams = await self._compose_agent_teams(context)

            # 병렬 작업 실행 (최대 3차 반복)
            work_results = await self._execute_parallel_work(agent_teams, context)

            # 체크리스트 검증
            checklist_results = await self._validate_checklist(work_results)

            # 모의 평가 시뮬레이션
            simulation_results = await self._run_simulation(work_results, context)

            # 품질 평가 및 반복 결정
            quality_assessment = self._assess_quality(checklist_results, simulation_results)

            output_data = {
                "agent_teams": agent_teams,
                "work_results": work_results,
                "checklist_results": checklist_results,
                "simulation_results": simulation_results,
                "quality_assessment": quality_assessment,
                "iteration_count": context.get("iteration_count", 1),
                "max_iterations": 3
            }

            # 품질에 따른 상태 결정
            if quality_assessment["score"] >= 0.8:
                status = "completed"
                decision = "READY_FOR_REVIEW"
            elif output_data["iteration_count"] < 3:
                status = "in_progress"
                decision = "REQUIRES_ITERATION"
            else:
                status = "failed"
                decision = "QUALITY_THRESHOLD_NOT_MET"

            self.status = status
            self.result = ModuleResult(
                module_id=self.module_id,
                status=status,
                output_data=output_data,
                decision=decision,
                reasoning=quality_assessment["feedback"]
            )

            return self.result

        except Exception as e:
            self.status = "failed"
            raise

    async def _compose_agent_teams(self, context: Dict) -> List[Dict]:
        """Agent Teams 구성"""
        return [
            {
                "team_id": "content_team",
                "agents": ["section_writer", "content_reviewer"],
                "responsibility": "제안서 본문 작성",
                "sections": ["executive_summary", "approach", "methodology"]
            },
            {
                "team_id": "technical_team",
                "agents": ["technical_writer", "diagram_generator"],
                "responsibility": "기술적 내용 및 다이어그램",
                "sections": ["technical_approach", "architecture"]
            },
            {
                "team_id": "business_team",
                "agents": ["business_analyst", "price_optimizer"],
                "responsibility": "비즈니스 분석 및 가격 전략",
                "sections": ["pricing", "timeline", "risk_management"]
            }
        ]

    async def _execute_parallel_work(self, agent_teams: List, context: Dict) -> Dict[str, Any]:
        """병렬 작업 실행"""
        # 기존 Phase 4 로직 활용 + 병렬 처리
        return {
            "sections_completed": 8,
            "diagrams_generated": 3,
            "quality_checks_passed": 7,
            "issues_found": 2
        }

    async def _validate_checklist(self, work_results: Dict) -> Dict[str, Any]:
        """체크리스트 검증"""
        checklist_items = [
            "요구사항 완전성",
            "기술적 타당성",
            "가격 적정성",
            "일정 현실성",
            "리스크 관리",
            "품질 기준 준수"
        ]

        results = {}
        for item in checklist_items:
            results[item] = {
                "status": "PASS" if work_results.get("quality_checks_passed", 0) > 5 else "FAIL",
                "details": f"{item} 검증 완료"
            }

        return results

    async def _run_simulation(self, work_results: Dict, context: Dict) -> Dict[str, Any]:
        """모의 평가 시뮬레이션"""
        return {
            "evaluation_score": 0.82,
            "strengths": ["기술적 우위", "가격 경쟁력"],
            "weaknesses": ["세부 일정 부족"],
            "recommendations": ["일정 세부화 필요"]
        }

    def _assess_quality(self, checklist: Dict, simulation: Dict) -> Dict[str, Any]:
        """품질 종합 평가"""
        checklist_score = sum(1 for item in checklist.values() if item["status"] == "PASS") / len(checklist)
        simulation_score = simulation["evaluation_score"]

        total_score = (checklist_score + simulation_score) / 2

        feedback = f"품질 점수: {total_score:.2f}\n"
        feedback += f"체크리스트 준수율: {checklist_score:.1%}\n"
        feedback += f"모의 평가 점수: {simulation_score:.2f}"

        return {
            "score": total_score,
            "checklist_score": checklist_score,
            "simulation_score": simulation_score,
            "feedback": feedback
        }

# 4. 최종 검토 모듈
class FinalReviewModule(ProposalModule):
    """최종 검토 및 PPT 작업 모듈"""

    def __init__(self):
        super().__init__("final_review", "최종 검토 및 PPT 작업")

    def get_required_inputs(self) -> List[str]:
        return ["work_results", "quality_assessment", "strategy_approved"]

    async def validate_input(self, context: Dict[str, Any]) -> bool:
        required = self.get_required_inputs()
        return all(key in context for key in required)

    async def execute(self, context: Dict[str, Any]) -> ModuleResult:
        self.status = "in_progress"

        try:
            # PM 최종 검토
            pm_review = await self._conduct_pm_review(context)

            if pm_review["decision"] == "REJECT":
                # 거부 시 피드백 제공
                self.status = "rejected"
                return ModuleResult(
                    module_id=self.module_id,
                    status="rejected",
                    output_data={"pm_review": pm_review},
                    decision="REJECTED",
                    reasoning=pm_review["feedback"]
                )

            # PPT 작업 시작
            ppt_work = await self._create_ppt_work(context)

            # PPT 검토 및 보완 루프
            final_ppt = await self._refine_ppt_work(ppt_work, context)

            output_data = {
                "pm_review": pm_review,
                "ppt_work": ppt_work,
                "final_ppt": final_ppt,
                "docx_final": context.get("work_results", {}),
                "review_iterations": 1
            }

            self.status = "completed"
            self.result = ModuleResult(
                module_id=self.module_id,
                status="completed",
                output_data=output_data,
                decision="APPROVED",
                reasoning="최종 검토 및 PPT 작업 완료"
            )

            return self.result

        except Exception as e:
            self.status = "failed"
            raise

    async def _conduct_pm_review(self, context: Dict) -> Dict[str, Any]:
        """PM 최종 검토"""
        return {
            "reviewer": "PM",
            "decision": "APPROVE",  # 또는 "REJECT"
            "feedback": "전반적으로 양호하나 PPT 개선 필요",
            "score": 0.85,
            "action_items": ["PPT 디자인 개선", "키 메시지 강조"]
        }

    async def _create_ppt_work(self, context: Dict) -> Dict[str, Any]:
        """PPT 작업 생성"""
        return {
            "slides_count": 25,
            "key_slides": ["title", "executive_summary", "approach", "pricing", "timeline"],
            "design_template": "professional_blue",
            "status": "draft_created"
        }

    async def _refine_ppt_work(self, ppt_work: Dict, context: Dict) -> Dict[str, Any]:
        """PPT 검토 및 보완"""
        # 검토-보완 루프 시뮬레이션
        return {
            "final_slides_count": 28,
            "review_rounds": 2,
            "improvements_made": ["디자인 개선", "콘텐츠 보완", "시각 자료 추가"],
            "quality_score": 0.92,
            "status": "finalized"
        }

# 모듈러 워크플로우 매니저
class ModularProposalWorkflow:
    """4-Module 기반 제안작업 워크플로우"""

    def __init__(self):
        self.modules = {
            "rfp_review": RFPReviewModule(),
            "strategy_planning": StrategyPlanningModule(),
            "parallel_work": ParallelWorkModule(),
            "final_review": FinalReviewModule()
        }
        self.execution_order = ["rfp_review", "strategy_planning", "parallel_work", "final_review"]
        self.context = {}
        self.results = {}

    async def execute_workflow(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """전체 워크플로우 실행"""
        self.context.update(initial_context)

        for module_id in self.execution_order:
            module = self.modules[module_id]

            # 입력 검증
            if not await module.validate_input(self.context):
                raise ValueError(f"Module {module_id}: 입력 데이터 부족")

            # 모듈 실행
            result = await module.execute(self.context)
            self.results[module_id] = result

            # 컨텍스트 업데이트
            self.context.update(result.output_data)

            # 조건부 분기 처리
            if result.decision == "STOP":
                break  # 워크플로우 중단
            elif result.decision == "REQUIRES_ITERATION":
                # 반복 실행 (병렬 작업 모듈에서만)
                if module_id == "parallel_work":
                    await self._handle_iteration(module, result)
            elif result.decision == "REJECTED":
                break  # 워크플로우 중단

        return {
            "status": "completed",
            "results": self.results,
            "final_context": self.context
        }

    async def _handle_iteration(self, module: ParallelWorkModule, result: ModuleResult):
        """반복 처리 (병렬 작업 모듈용)"""
        max_iterations = result.output_data.get("max_iterations", 3)
        current_iteration = result.output_data.get("iteration_count", 1)

        while current_iteration < max_iterations:
            # 컨텍스트에 반복 횟수 업데이트
            self.context["iteration_count"] = current_iteration + 1

            # 모듈 재실행
            new_result = await module.execute(self.context)
            self.results[module.module_id] = new_result

            if new_result.decision != "REQUIRES_ITERATION":
                break

            current_iteration += 1

    def get_workflow_status(self) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        return {
            "modules": {
                module_id: {
                    "name": module.name,
                    "status": module.status,
                    "result": module.result.__dict__ if module.result else None
                }
                for module_id, module in self.modules.items()
            },
            "current_context": self.context
        }</content>
<parameter name="filePath">c:\Users\현재호\OneDrive - 테크노베이션파트너스\바탕 화면\viveproject\tenopa proposer\modular_architecture.py