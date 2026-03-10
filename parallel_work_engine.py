"""
병렬 작업 모듈 상세 구현
Agent Teams, 체크리스트, 모의 평가
"""

from typing import Dict, List, Any, Tuple, Optional, Callable
import asyncio
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json

class AgentRole(Enum):
    TECHNICAL_LEAD = "technical_lead"          # 기술 총괄
    BUSINESS_ANALYST = "business_analyst"      # 사업 분석
    SOLUTION_ARCHITECT = "solution_architect"  # 솔루션 설계
    CONTENT_WRITER = "content_writer"          # 내용 작성
    QUALITY_ASSURANCE = "quality_assurance"    # 품질 검증
    LEGAL_REVIEW = "legal_review"             # 법률 검토

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class ChecklistCategory(Enum):
    TECHNICAL = "technical"
    BUSINESS = "business"
    COMPLIANCE = "compliance"
    QUALITY = "quality"
    RISK = "risk"

@dataclass
class AgentTask:
    """에이전트 작업"""
    task_id: str
    role: AgentRole
    title: str
    description: str
    status: TaskStatus
    priority: int  # 1-5 (5가 최고)
    dependencies: List[str]  # 선행 작업 ID들
    estimated_hours: float
    assigned_agent: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    deliverables: List[str]
    progress: float  # 0.0 ~ 1.0

@dataclass
class ChecklistItem:
    """체크리스트 항목"""
    item_id: str
    category: ChecklistCategory
    title: str
    description: str
    is_completed: bool
    priority: int
    assignee: Optional[str]
    due_date: Optional[datetime]
    verification_method: str
    notes: str

@dataclass
class MockEvaluation:
    """모의 평가 결과"""
    evaluation_id: str
    evaluator_role: str
    criteria: str
    score: float  # 0.0 ~ 1.0
    feedback: str
    recommendations: List[str]
    timestamp: datetime

@dataclass
class ParallelWorkResult:
    """병렬 작업 결과"""
    tasks: List[AgentTask]
    checklist: List[ChecklistItem]
    mock_evaluations: List[MockEvaluation]
    overall_progress: float
    bottlenecks: List[str]
    recommendations: List[str]

class ParallelWorkEngine:
    """병렬 작업 엔진"""

    def __init__(self):
        self.task_templates = self._load_task_templates()
        self.checklist_templates = self._load_checklist_templates()
        self.evaluation_criteria = self._load_evaluation_criteria()

    async def execute_parallel_work(self, strategy: Dict, rfp_analysis: Dict,
                                  company_profile: Dict) -> ParallelWorkResult:
        """
        병렬 작업 실행

        Args:
            strategy: 전략 수립 결과
            rfp_analysis: RFP 분석 결과
            company_profile: 회사 프로필

        Returns:
            ParallelWorkResult: 병렬 작업 결과
        """

        # 1. 에이전트 팀 구성 및 작업 할당
        tasks = await self._create_agent_tasks(strategy, rfp_analysis)

        # 2. 체크리스트 생성
        checklist = await self._generate_checklist(strategy, rfp_analysis, company_profile)

        # 3. 모의 평가 실행
        mock_evaluations = await self._conduct_mock_evaluations(tasks, checklist, rfp_analysis)

        # 4. 진행 상황 분석
        overall_progress = self._calculate_overall_progress(tasks, checklist)
        bottlenecks = self._identify_bottlenecks(tasks, checklist)
        recommendations = self._generate_recommendations(tasks, checklist, mock_evaluations)

        result = ParallelWorkResult(
            tasks=tasks,
            checklist=checklist,
            mock_evaluations=mock_evaluations,
            overall_progress=overall_progress,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )

        return result

    async def _create_agent_tasks(self, strategy: Dict, rfp_analysis: Dict) -> List[AgentTask]:
        """에이전트 작업 생성 및 할당"""

        tasks = []

        # 전략에 따른 작업 템플릿 선택
        primary_strategy = strategy.get("primary_strategy", "technical_superiority")
        template_key = f"{primary_strategy}_tasks"

        task_templates = self.task_templates.get(template_key, self.task_templates["default_tasks"])

        # RFP 특성에 따른 작업 조정
        adjusted_templates = self._adjust_tasks_for_rfp(task_templates, rfp_analysis)

        # 작업 인스턴스 생성
        for i, template in enumerate(adjusted_templates):
            task = AgentTask(
                task_id=f"task_{i+1:03d}",
                role=AgentRole(template["role"]),
                title=template["title"],
                description=template["description"],
                status=TaskStatus.PENDING,
                priority=template["priority"],
                dependencies=template.get("dependencies", []),
                estimated_hours=template["estimated_hours"],
                assigned_agent=None,
                start_date=None,
                end_date=None,
                deliverables=template.get("deliverables", []),
                progress=0.0
            )
            tasks.append(task)

        # 작업 의존성 검증 및 조정
        tasks = self._resolve_task_dependencies(tasks)

        # 작업 우선순위 최적화
        tasks = self._optimize_task_priorities(tasks, rfp_analysis)

        return tasks

    async def _generate_checklist(self, strategy: Dict, rfp_analysis: Dict,
                                company_profile: Dict) -> List[ChecklistItem]:
        """체크리스트 생성"""

        checklist_items = []

        # 기본 체크리스트 템플릿 로드
        for category_name, items in self.checklist_templates.items():
            category = ChecklistCategory(category_name)

            for i, item_template in enumerate(items):
                # RFP 및 전략에 따른 조정
                adjusted_item = self._adjust_checklist_item(item_template, rfp_analysis, strategy)

                item = ChecklistItem(
                    item_id=f"{category_name}_{i+1:03d}",
                    category=category,
                    title=adjusted_item["title"],
                    description=adjusted_item["description"],
                    is_completed=False,
                    priority=adjusted_item["priority"],
                    assignee=None,
                    due_date=None,
                    verification_method=adjusted_item["verification_method"],
                    notes=""
                )
                checklist_items.append(item)

        # 우선순위 정렬
        checklist_items.sort(key=lambda x: x.priority, reverse=True)

        return checklist_items

    async def _conduct_mock_evaluations(self, tasks: List[AgentTask],
                                      checklist: List[ChecklistItem],
                                      rfp_analysis: Dict) -> List[MockEvaluation]:
        """모의 평가 실행"""

        evaluations = []

        # 평가자 역할별 평가 실행
        evaluator_roles = ["technical_expert", "business_expert", "client_representative", "quality_assurance"]

        for role in evaluator_roles:
            role_evaluations = await self._evaluate_by_role(role, tasks, checklist, rfp_analysis)
            evaluations.extend(role_evaluations)

        return evaluations

    async def _evaluate_by_role(self, evaluator_role: str, tasks: List[AgentTask],
                               checklist: List[ChecklistItem], rfp_analysis: Dict) -> List[MockEvaluation]:
        """역할별 모의 평가"""

        evaluations = []

        # 평가 기준에 따른 평가
        criteria_list = self.evaluation_criteria.get(evaluator_role, [])

        for criteria in criteria_list:
            # 실제 평가 로직 (시뮬레이션)
            score, feedback, recommendations = await self._simulate_evaluation(
                evaluator_role, criteria, tasks, checklist, rfp_analysis
            )

            evaluation = MockEvaluation(
                evaluation_id=f"eval_{evaluator_role}_{criteria.replace(' ', '_')}",
                evaluator_role=evaluator_role,
                criteria=criteria,
                score=score,
                feedback=feedback,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            evaluations.append(evaluation)

        return evaluations

    async def _simulate_evaluation(self, role: str, criteria: str, tasks: List[AgentTask],
                                 checklist: List[ChecklistItem], rfp_analysis: Dict) -> Tuple[float, str, List[str]]:
        """평가 시뮬레이션 (실제로는 AI나 전문가 평가)"""

        # 간단한 시뮬레이션 로직
        base_score = 0.7  # 기본 점수

        # 작업 완료도 반영
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
        task_completion_ratio = completed_tasks / len(tasks) if tasks else 0
        score = base_score + (task_completion_ratio * 0.2)

        # 체크리스트 완료도 반영
        completed_items = sum(1 for item in checklist if item.is_completed)
        checklist_completion_ratio = completed_items / len(checklist) if checklist else 0
        score = min(1.0, score + (checklist_completion_ratio * 0.1))

        # 역할별 특성 반영
        if role == "technical_expert":
            score = min(1.0, score + 0.1)  # 기술 전문가는 좀 더 긍정적
        elif role == "client_representative":
            score = max(0.0, score - 0.1)  # 고객 대표는 좀 더 엄격

        # 피드백 생성
        feedback = self._generate_evaluation_feedback(role, criteria, score)

        # 개선 권고사항
        recommendations = self._generate_evaluation_recommendations(role, criteria, score)

        return score, feedback, recommendations

    def _calculate_overall_progress(self, tasks: List[AgentTask],
                                  checklist: List[ChecklistItem]) -> float:
        """전체 진행률 계산"""

        # 작업 진행률 (가중치 60%)
        task_progress = sum(task.progress for task in tasks) / len(tasks) if tasks else 0

        # 체크리스트 완료율 (가중치 40%)
        checklist_completion = sum(1 for item in checklist if item.is_completed) / len(checklist) if checklist else 0

        overall_progress = (task_progress * 0.6) + (checklist_completion * 0.4)

        return min(1.0, overall_progress)

    def _identify_bottlenecks(self, tasks: List[AgentTask],
                            checklist: List[ChecklistItem]) -> List[str]:
        """병목 현상 식별"""

        bottlenecks = []

        # 지연된 작업 식별
        delayed_tasks = [task for task in tasks if task.status == TaskStatus.BLOCKED]
        if delayed_tasks:
            bottlenecks.append(f"차단된 작업 {len(delayed_tasks)}건: {[t.title for t in delayed_tasks]}")

        # 우선순위 높은 미완료 체크리스트
        high_priority_incomplete = [
            item for item in checklist
            if not item.is_completed and item.priority >= 4
        ]
        if high_priority_incomplete:
            bottlenecks.append(f"우선순위 높은 미완료 항목 {len(high_priority_incomplete)}건")

        # 의존성 문제 식별
        dependency_issues = self._check_dependency_issues(tasks)
        if dependency_issues:
            bottlenecks.append(f"작업 의존성 문제: {dependency_issues}")

        return bottlenecks

    def _generate_recommendations(self, tasks: List[AgentTask],
                                checklist: List[ChecklistItem],
                                evaluations: List[MockEvaluation]) -> List[str]:
        """개선 권고사항 생성"""

        recommendations = []

        # 낮은 평가 점수 기반 권고
        low_score_evaluations = [e for e in evaluations if e.score < 0.6]
        if low_score_evaluations:
            recommendations.append("모의 평가에서 낮은 점수를 받은 영역 개선 우선")

        # 미완료 작업 권고
        pending_tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]]
        if len(pending_tasks) > len(tasks) * 0.5:
            recommendations.append("병렬 작업 효율성 향상을 위한 리소스 재배분 고려")

        # 체크리스트 기반 권고
        incomplete_critical = [item for item in checklist if not item.is_completed and item.priority >= 5]
        if incomplete_critical:
            recommendations.append("중요 체크리스트 항목 우선 완료")

        return recommendations

    # 헬퍼 메소드들
    def _load_task_templates(self) -> Dict[str, List[Dict]]:
        """작업 템플릿 로드"""
        return {
            "technical_superiority_tasks": [
                {
                    "role": "technical_lead",
                    "title": "기술 아키텍처 설계",
                    "description": "RFP 요구사항 기반 기술 아키텍처 설계",
                    "priority": 5,
                    "estimated_hours": 16.0,
                    "deliverables": ["기술 아키텍처 문서", "시스템 설계도"]
                },
                {
                    "role": "solution_architect",
                    "title": "솔루션 상세 설계",
                    "description": "기술 솔루션의 상세 설계 및 명세",
                    "priority": 4,
                    "estimated_hours": 24.0,
                    "dependencies": ["task_001"],
                    "deliverables": ["솔루션 설계 문서", "API 명세서"]
                },
                {
                    "role": "content_writer",
                    "title": "기술 제안서 작성",
                    "description": "기술적 내용을 중심으로 한 제안서 작성",
                    "priority": 4,
                    "estimated_hours": 20.0,
                    "dependencies": ["task_002"],
                    "deliverables": ["기술 제안서 초안"]
                }
            ],
            "default_tasks": [
                {
                    "role": "business_analyst",
                    "title": "사업 요구사항 분석",
                    "description": "RFP 사업 요구사항 분석 및 정리",
                    "priority": 4,
                    "estimated_hours": 12.0,
                    "deliverables": ["요구사항 분석 문서"]
                },
                {
                    "role": "content_writer",
                    "title": "제안서 초안 작성",
                    "description": "기본 제안서 구조 및 내용 작성",
                    "priority": 3,
                    "estimated_hours": 16.0,
                    "deliverables": ["제안서 초안"]
                }
            ]
        }

    def _load_checklist_templates(self) -> Dict[str, List[Dict]]:
        """체크리스트 템플릿 로드"""
        return {
            "technical": [
                {
                    "title": "기술 요구사항 준수 확인",
                    "description": "RFP 기술 요구사항을 모두 준수하는지 확인",
                    "priority": 5,
                    "verification_method": "문서 검토 및 전문가 검증"
                },
                {
                    "title": "시스템 아키텍처 검토",
                    "description": "제안한 시스템 아키텍처의 타당성 검토",
                    "priority": 4,
                    "verification_method": "아키텍트 리뷰"
                }
            ],
            "business": [
                {
                    "title": "가격 산정 적정성 검토",
                    "description": "제안 가격의 적정성 및 타당성 검토",
                    "priority": 5,
                    "verification_method": "원가 분석 및 시장 비교"
                },
                {
                    "title": "사업성 분석",
                    "description": "제안 사업의 경제성 및 사업성 분석",
                    "priority": 4,
                    "verification_method": "재무 분석"
                }
            ],
            "compliance": [
                {
                    "title": "자격 요건 확인",
                    "description": "필수 자격 요건 및 인증 확인",
                    "priority": 5,
                    "verification_method": "서류 검증"
                },
                {
                    "title": "법적 준수사항 검토",
                    "description": "관련 법규 및 규정 준수 여부 검토",
                    "priority": 4,
                    "verification_method": "법무 검토"
                }
            ],
            "quality": [
                {
                    "title": "품질 관리 계획 수립",
                    "description": "프로젝트 품질 관리 계획 수립 및 검토",
                    "priority": 4,
                    "verification_method": "품질 감사"
                }
            ],
            "risk": [
                {
                    "title": "리스크 평가 및 완화 방안",
                    "description": "주요 리스크 식별 및 완화 방안 검토",
                    "priority": 4,
                    "verification_method": "리스크 워크숍"
                }
            ]
        }

    def _load_evaluation_criteria(self) -> Dict[str, List[str]]:
        """평가 기준 로드"""
        return {
            "technical_expert": [
                "기술적 타당성",
                "아키텍처 설계 품질",
                "기술 구현 가능성"
            ],
            "business_expert": [
                "사업 이해도",
                "가격 적정성",
                "사업성 분석"
            ],
            "client_representative": [
                "요구사항 충족도",
                "제안서 가독성",
                "실현 가능성"
            ],
            "quality_assurance": [
                "품질 관리 체계",
                "문서 완성도",
                "준수사항 이행"
            ]
        }

    def _adjust_tasks_for_rfp(self, templates: List[Dict], rfp_analysis: Dict) -> List[Dict]:
        """RFP 특성에 따른 작업 조정"""
        adjusted = templates.copy()

        # RFP 규모에 따른 작업량 조정
        budget = rfp_analysis["basic_info"].get("budget", 0)
        if budget > 500000000:  # 5억원 이상
            # 작업 시간 증가
            for task in adjusted:
                task["estimated_hours"] *= 1.5

        # 기술 복잡도에 따른 조정
        technical_reqs = rfp_analysis["requirements"].get("technical_requirements", [])
        if len(technical_reqs) > 5:
            # 기술 작업 추가
            adjusted.append({
                "role": "solution_architect",
                "title": "복잡 기술 요구사항 분석",
                "description": "다수의 기술 요구사항 분석 및 우선순위 결정",
                "priority": 4,
                "estimated_hours": 8.0,
                "deliverables": ["기술 요구사항 분석 보고서"]
            })

        return adjusted

    def _adjust_checklist_item(self, item_template: Dict, rfp_analysis: Dict, strategy: Dict) -> Dict:
        """체크리스트 항목 RFP/전략에 따른 조정"""
        adjusted = item_template.copy()

        # 전략에 따른 우선순위 조정
        primary_strategy = strategy.get("primary_strategy")
        if primary_strategy == "technical_superiority" and "기술" in item_template["title"]:
            adjusted["priority"] = min(5, item_template["priority"] + 1)

        return adjusted

    def _resolve_task_dependencies(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """작업 의존성 해결"""
        # 간단한 위상 정렬 구현
        resolved = []
        unresolved = tasks.copy()

        while unresolved:
            # 의존성이 없는 작업 찾기
            ready_tasks = []
            for task in unresolved:
                deps_resolved = all(
                    any(resolved_task.task_id == dep for resolved_task in resolved)
                    for dep in task.dependencies
                )
                if deps_resolved:
                    ready_tasks.append(task)

            if not ready_tasks:
                # 순환 의존성 발견
                break

            # 준비된 작업들을 우선순위로 정렬하여 추가
            ready_tasks.sort(key=lambda t: t.priority, reverse=True)
            resolved.extend(ready_tasks)

            # 처리된 작업 제거
            for task in ready_tasks:
                unresolved.remove(task)

        return resolved + unresolved  # 남은 작업들 추가

    def _optimize_task_priorities(self, tasks: List[AgentTask], rfp_analysis: Dict) -> List[AgentTask]:
        """작업 우선순위 최적화"""

        # RFP 마감일에 따른 우선순위 조정
        duration = rfp_analysis["basic_info"].get("duration_months", 12)
        if duration < 6:  # 6개월 미만 단기 사업
            # 긴급 작업 우선순위 상승
            for task in tasks:
                if task.estimated_hours < 8:  # 단기 작업
                    task.priority = min(5, task.priority + 1)

        # 평가 가중치에 따른 우선순위 조정
        evaluation_weights = rfp_analysis["evaluation_criteria"].get("weights", {})
        if evaluation_weights.get("기술성", 0) > 0.4:
            # 기술 관련 작업 우선순위 상승
            for task in tasks:
                if task.role in [AgentRole.TECHNICAL_LEAD, AgentRole.SOLUTION_ARCHITECT]:
                    task.priority = min(5, task.priority + 1)

        return tasks

    def _check_dependency_issues(self, tasks: List[AgentTask]) -> List[str]:
        """의존성 문제 확인"""
        issues = []

        for task in tasks:
            if task.status == TaskStatus.BLOCKED:
                # 선행 작업 상태 확인
                blocking_deps = []
                for dep_id in task.dependencies:
                    dep_task = next((t for t in tasks if t.task_id == dep_id), None)
                    if dep_task and dep_task.status != TaskStatus.COMPLETED:
                        blocking_deps.append(dep_task.title)

                if blocking_deps:
                    issues.append(f"'{task.title}' 작업이 '{', '.join(blocking_deps)}' 작업에 의해 차단됨")

        return issues

    def _generate_evaluation_feedback(self, role: str, criteria: str, score: float) -> str:
        """평가 피드백 생성"""
        if score >= 0.8:
            return f"{criteria} 항목이 우수하게 평가되었습니다."
        elif score >= 0.6:
            return f"{criteria} 항목이 양호하지만 개선의 여지가 있습니다."
        else:
            return f"{criteria} 항목에서 개선이 필요한 부분이 확인되었습니다."

    def _generate_evaluation_recommendations(self, role: str, criteria: str, score: float) -> List[str]:
        """평가 권고사항 생성"""
        recommendations = []

        if score < 0.6:
            if "기술" in criteria:
                recommendations.append("기술적 근거 자료 보강")
            elif "가격" in criteria:
                recommendations.append("가격 산정 근거 명확화")
            elif "품질" in criteria:
                recommendations.append("품질 관리 프로세스 구체화")

        return recommendations</content>
<parameter name="filePath">c:\Users\현재호\OneDrive - 테크노베이션파트너스\바탕 화면\viveproject\tenopa proposer\parallel_work_engine.py