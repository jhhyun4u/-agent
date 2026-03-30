/**
 * 프롬프트 ID → 사람 친화적 라벨 + 한줄 설명 매핑
 *
 * 카탈로그, 대시보드, 워크벤치에서 공통 사용.
 */

interface PromptMeta {
  label: string;
  description: string;
  step: string;
}

const PROMPT_META: Record<string, PromptMeta> = {
  // A. 공고 분석
  "bid_review.PREPROCESSOR_SYSTEM": { label: "공고 전처리", description: "G2B 공고문에서 핵심 정보(기관/예산/범위/자격/평가) 추출", step: "공고 검색" },
  "bid_review.PREPROCESSOR_USER": { label: "공고 전처리 (사용자)", description: "공고 원문 → BidSummary JSON 변환 지시", step: "공고 검색" },
  "bid_review.REVIEWER_SYSTEM": { label: "적합도 평가", description: "TENOPA 역량 기반 공고 적합성 0~100점 평가", step: "공고 검색" },
  "bid_review.REVIEWER_USER_SINGLE": { label: "단건 평가", description: "개별 공고 적합도 점수 + 판정 생성", step: "공고 검색" },
  "bid_review.REVIEWER_USER_BATCH": { label: "일괄 평가", description: "다건 공고 일괄 적합도 평가", step: "공고 검색" },
  "bid_review.UNIFIED_ANALYSIS_SYSTEM": { label: "통합 분석", description: "전처리+리뷰 1-shot 통합 분석", step: "공고 검색" },
  "bid_review.UNIFIED_ANALYSIS_USER": { label: "통합 분석 (사용자)", description: "통합 분석 지시 + JSON 출력 형식", step: "공고 검색" },
  "bid_review.VERDICT_TO_ACTION": { label: "판정→액션 매핑", description: "추천/검토/제외 → 액션 코드 변환", step: "공고 검색" },
  "bid_review.VERDICT_TO_PROBABILITY": { label: "판정→확률 매핑", description: "추천/검토/제외 → 상/중/하 변환", step: "공고 검색" },

  // B. 전략 수립
  "strategy.GENERATE_PROMPT": { label: "전략 수립", description: "RFP+GoNoGo→Win Theme+SWOT+시나리오+대안 전략 생성", step: "전략 수립" },
  "strategy.POSITIONING_STRATEGY_MATRIX": { label: "포지셔닝 매트릭스", description: "수성/공격/인접 3방향 전략 가이드", step: "전략 수립" },
  "strategy.COMPETITIVE_ANALYSIS_FRAMEWORK": { label: "경쟁 분석", description: "SWOT+차별화+시나리오 프레임워크", step: "전략 수립" },
  "strategy.STRATEGY_RESEARCH_FRAMEWORK": { label: "연구수행 전략", description: "연구질문 도출 + 방법론 근거", step: "전략 수립" },

  // C. 계획 수립
  "plan.TEAM_PROMPT": { label: "팀 구성", description: "RFP+전략에 맞는 역할별 인력 구성", step: "계획 수립" },
  "plan.ASSIGN_PROMPT": { label: "산출물 배분", description: "산출물 목록 + 담당 역할 + QA 체크포인트", step: "계획 수립" },
  "plan.SCHEDULE_PROMPT": { label: "추진 일정", description: "Phase 구분 + 마일스톤 + 크리티컬패스", step: "계획 수립" },
  "plan.STORY_PROMPT": { label: "스토리라인 설계", description: "목차 최적화 + 섹션별 핵심 주장 + SMART 목표", step: "계획 수립" },
  "plan.PRICE_PROMPT": { label: "예산/가격 전략", description: "노임단가 기반 예산 + 입찰가 시뮬레이션", step: "계획 수립" },
  "plan.BUDGET_DETAIL_FRAMEWORK": { label: "예산 프레임워크", description: "원가 기준 + 경비 항목 + 이윤 산출 구조", step: "계획 수립" },

  // D. 제안서 작성
  "section_prompts.EVALUATOR_PERSPECTIVE_BLOCK": { label: "평가위원 관점 (공통)", description: "모든 섹션에 주입되는 채점 관점 + 스토리텔링 원칙", step: "제안서 작성" },
  "section_prompts.UNDERSTAND": { label: "사업의 이해", description: "발주기관 관점 재해석 + AS-IS/TO-BE + 핫버튼", step: "제안서 작성" },
  "section_prompts.STRATEGY": { label: "추진 전략", description: "Win Theme 선언 + 전략 프레임워크 + 차별화 포인트", step: "제안서 작성" },
  "section_prompts.METHODOLOGY": { label: "수행 방법론", description: "방법론 선택 근거 + 단계별 수행활동·산출물 + 품질 게이트", step: "제안서 작성" },
  "section_prompts.TECHNICAL": { label: "기술적 수행방안", description: "아키텍처 + 기술 선택 근거 + 구현 방법 + RFP 매핑", step: "제안서 작성" },
  "section_prompts.MANAGEMENT": { label: "사업 관리", description: "추진 체계 + 일정 + 품질 + 리스크 + 의사소통", step: "제안서 작성" },
  "section_prompts.PERSONNEL": { label: "투입 인력", description: "인력표 + 핵심인력 경험 + RACI + M/M 투입 계획", step: "제안서 작성" },
  "section_prompts.TRACK_RECORD": { label: "수행 실적", description: "유사성 매트릭스 + 정량 성과 + 시사점", step: "제안서 작성" },
  "section_prompts.SECURITY": { label: "보안 대책", description: "법령 대응표 + 기술·관리·물리 보안 + 개인정보", step: "제안서 작성" },
  "section_prompts.MAINTENANCE": { label: "유지보수/하자보수", description: "SLA 지표 + 장애 대응 + 기술 이전 + 지속가능성", step: "제안서 작성" },
  "section_prompts.ADDED_VALUE": { label: "부가제안/기대효과", description: "부가 제안 + SMART 기대효과 + 로드맵", step: "제안서 작성" },
  "section_prompts.CASE_B": { label: "서식 지정 (케이스 B)", description: "발주기관 지정 서식 보존하며 내용 작성", step: "제안서 작성" },
  "proposal_prompts.CASE_A_PROMPT": { label: "자유 양식 (케이스 A)", description: "자유 양식 제안서 섹션 작성", step: "제안서 작성" },
  "proposal_prompts.CASE_B_PROMPT": { label: "서식 양식 (케이스 B)", description: "서식 지정 제안서 섹션 작성", step: "제안서 작성" },
  "proposal_prompts.SELF_REVIEW": { label: "자가진단", description: "4축 100점 평가(컴플라이언스/전략/품질/신뢰성) + 3-페르소나", step: "자가진단" },

  // E. 발표 자료
  "proposal_prompts.PRESENTATION_STRATEGY": { label: "발표 전략", description: "시간 배분 + 구조 + Q&A 전략 + 시각 전략", step: "발표 자료" },
  "proposal_prompts.PPT_SLIDE": { label: "PPT 슬라이드", description: "섹션→슬라이드 변환 (불릿+시각+발표노트)", step: "발표 자료" },
  "ppt_pipeline.TOC_SYSTEM": { label: "PPT 목차 설계", description: "25~35장 목차 + 배점 기반 슬라이드 수 배분", step: "발표 자료" },
  "ppt_pipeline.TOC_USER": { label: "PPT 목차 (사용자)", description: "평가항목→목차 레이아웃 매핑 지시", step: "발표 자료" },
  "ppt_pipeline.VISUAL_BRIEF_SYSTEM": { label: "비주얼 전략", description: "F-Pattern 시각 설계 (Message→Logic→Structure→Design)", step: "발표 자료" },
  "ppt_pipeline.VISUAL_BRIEF_USER": { label: "비주얼 전략 (사용자)", description: "TOC+Win Theme→슬라이드별 시각 전략", step: "발표 자료" },
  "ppt_pipeline.STORYBOARD_SYSTEM": { label: "PPT 스토리보드", description: "슬라이드별 본문+불릿+발표자노트 생성", step: "발표 자료" },
  "ppt_pipeline.STORYBOARD_USER": { label: "스토리보드 (사용자)", description: "TOC+비주얼+제안서→슬라이드 콘텐츠", step: "발표 자료" },

  // F. 품질 보증
  "trustworthiness.SOURCE_TAG_FORMAT": { label: "출처 태그 규칙", description: "8종 출처 태그 형식 ([KB], [RFP p.N] 등)", step: "품질 보증" },
  "trustworthiness.TRUSTWORTHINESS_RULES": { label: "신뢰성 6대 규칙", description: "할루시네이션 금지 + 출처 태그 + 과장 금지", step: "품질 보증" },
  "trustworthiness.TRUSTWORTHINESS_SCORING": { label: "신뢰성 평가 기준", description: "25점 평가 (출처 태그/KB 활용/과장/일관성)", step: "품질 보증" },
  "trustworthiness.FORBIDDEN_EXPRESSIONS": { label: "금지 표현 목록", description: "업계 최초, 혁신적 등 10개 금지어", step: "품질 보증" },
  "submission_docs.EXTRACT_SUBMISSION_DOCS": { label: "제출서류 추출", description: "RFP→제출 서류 목록 JSON 추출", step: "품질 보증" },
};

/** 프롬프트 ID → 사람 친화적 라벨 */
export function getPromptLabel(promptId: string): string {
  return PROMPT_META[promptId]?.label ?? promptId.split(".").pop()?.replace(/_/g, " ") ?? promptId;
}

/** 프롬프트 ID → 한줄 설명 */
export function getPromptDescription(promptId: string): string {
  return PROMPT_META[promptId]?.description ?? "";
}

/** 프롬프트 ID → 워크플로 단계명 */
export function getPromptStep(promptId: string): string {
  return PROMPT_META[promptId]?.step ?? "";
}

/** 시드 데이터의 prompt_id에도 매핑 (section.UNDERSTAND → section_prompts.UNDERSTAND) */
export function normalizePromptId(rawId: string): string {
  if (rawId.startsWith("section.")) {
    return `section_prompts.${rawId.slice(8)}`;
  }
  if (rawId === "strategy.positioning") return "strategy.POSITIONING_STRATEGY_MATRIX";
  if (rawId === "plan.story") return "plan.STORY_PROMPT";
  if (rawId === "plan.price") return "plan.PRICE_PROMPT";
  if (rawId === "self_review") return "proposal_prompts.SELF_REVIEW";
  return rawId;
}

export { PROMPT_META };
