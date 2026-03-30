"""
Node 8C: proposal_sections_consolidation
결정론적 통합 로직 (Claude 프롬프트 필요 없음).

이 노드:
1. 여러 버전의 검증된 섹션 병합
2. 사용자 버전 선택 적용
3. 충돌 해결
4. 섹션 간 일관성 보장
5. consolidated_proposal 메타데이터 + proposal_sections v2 생성

프롬프트 템플릿 불필요 - 로직은 결정론적입니다.
"""

# 통합 로직 패턴:

CONSOLIDATION_RULES = {
    "merge_strategy": "사용자 선택에 따라 선택된 버전 사용",
    "section_ordering": "dynamic_sections 계획 순서 따르기",
    "conflict_resolution": "resolved_conflicts 목록에서 표시",
    "consistency_checks": [
        "섹션 간 예산 금액 일관성",
        "섹션 간 일정 일관성",
        "인원/역할 일관성",
        "승리 테마 강화",
    ],
}
