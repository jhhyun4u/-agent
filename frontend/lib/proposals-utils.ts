import { ProposalSummary } from "@/lib/api";

/**
 * 포지셔닝 정보
 */
export const POS_LABELS = {
  offensive: { label: "공격", icon: "⚔️", color: "text-red-400" },
  defensive: { label: "수성", icon: "🛡️", color: "text-blue-400" },
  adjacent: { label: "인접", icon: "🔄", color: "text-amber-400" },
} as const;

/**
 * 워크플로 단계 매핑 (7단계: RFP분석 → 전략수립 → 제안계획 → 팀구성 → 제안서작성 → PPT → 입찰/제출)
 */
export const STEP_MAP = {
  rfp_analyze: { step: 1, label: "RFP 분석" },
  research_gather: { step: 1, label: "리서치" },
  go_no_go: { step: 1, label: "Go/No-Go" },
  strategy_generate: { step: 2, label: "전략수립" },
  plan_story: { step: 3, label: "제안계획" },
  plan_team: { step: 4, label: "팀구성" },
  plan_assign: { step: 4, label: "팀구성" },
  plan_schedule: { step: 4, label: "팀구성" },
  proposal_write_next: { step: 5, label: "제안서작성" },
  self_review: { step: 5, label: "제안서작성" },
  presentation_strategy: { step: 6, label: "PPT" },
  ppt_slide: { step: 6, label: "PPT" },
  bid_plan: { step: 7, label: "입찰/제출" },
} as const;

/**
 * 테이블 컬럼 설정
 */
export const TABLE_COLUMNS = [
  {
    width: "90px",
    key: "status",
    label: "상태",
    sortable: false,
    align: "center",
  },
  {
    width: "110px",
    key: "deadline",
    label: "마감일",
    sortable: true,
    align: "center",
  },
  {
    width: "1.5fr",
    key: "title",
    label: "프로젝트명",
    sortable: false,
    align: "left",
  },
  { width: "90px", key: "step", label: "단계", sortable: true, align: "left" },
  {
    width: "70px",
    key: "fit_score",
    label: "적합도",
    sortable: false,
    align: "center",
  },
  {
    width: "90px",
    key: "team_name",
    label: "팀",
    sortable: false,
    align: "left",
  },
  {
    width: "90px",
    key: "owner_name",
    label: "담당자",
    sortable: false,
    align: "left",
  },
  {
    width: "100px",
    key: "client_name",
    label: "발주처",
    sortable: false,
    align: "left",
  },
  {
    width: "90px",
    key: "budget",
    label: "예정가",
    sortable: false,
    align: "right",
  },
  {
    width: "90px",
    key: "bid_amount",
    label: "입찰가",
    sortable: false,
    align: "right",
  },
  { width: "36px", key: "menu", label: "", sortable: false, align: "center" },
] as const;

/**
 * 그리드 레이아웃 클래스명
 */
export const GRID_LAYOUT_CLASS =
  "grid-cols-[90px_110px_1.5fr_90px_70px_90px_90px_100px_90px_90px_36px]";

/**
 * 단계 정보 조회
 */
export function getStepInfo(phase: string | null): {
  step: number;
  label: string;
} {
  if (!phase) return { step: 0, label: "—" };
  return STEP_MAP[phase as keyof typeof STEP_MAP] ?? { step: 0, label: phase };
}

/**
 * 마감일 포맷팅
 */
export function formatDeadline(deadline: string | null): {
  text: string;
  urgent: boolean;
  dDay: string;
} {
  if (!deadline) return { text: "—", urgent: false, dDay: "" };
  const d = new Date(deadline);
  const now = new Date();
  const diffDays = Math.ceil(
    (d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
  );
  const text = `${d.getMonth() + 1}/${d.getDate()}`;
  const dDay =
    diffDays > 0
      ? `D-${diffDays}`
      : diffDays === 0
        ? "D-Day"
        : `D+${Math.abs(diffDays)}`;
  return {
    text: `${text} (${dDay})`,
    urgent: diffDays >= 0 && diffDays <= 3,
    dDay,
  };
}

/**
 * 예산 포맷팅
 */
export function formatBudget(amount: number | null | undefined): string {
  if (!amount) return "미기재";
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

/**
 * 간단한 예산 포맷 (테이블용)
 */
export function formatBudgetCompact(amount: number | null | undefined): string {
  if (!amount) return "—";
  return `₩${(amount / 100_000_000).toFixed(1)}억`;
}

/**
 * 상태 정보 도출 — 3단계 단순화: 작업대기 / 작업진행 / 결과대기
 */
export function deriveStatus(p: ProposalSummary): {
  label: string;
  dotColor: string;
  textColor: string;
  tooltip: string;
} {
  // 결과대기: submitted, presented
  if (p.status === "submitted" || p.status === "presented") {
    return {
      label: "결과대기",
      dotColor: "bg-purple-500/40",
      textColor: "text-purple-400",
      tooltip: "평가 결과 대기 중",
    };
  }

  // 작업진행: processing, running, on_hold
  if (
    p.status === "processing" ||
    p.status === "running" ||
    p.status === "on_hold"
  ) {
    return {
      label: "작업진행",
      dotColor: "bg-[#3ecf8e]/40",
      textColor: "text-[#3ecf8e]",
      tooltip: "제안 작업 진행 중",
    };
  }

  // 작업대기: 그 외 모두 (initialized, completed, won, lost, abandoned 등)
  return {
    label: "작업대기",
    dotColor: "bg-[#5c5c5c]/40",
    textColor: "text-[#8c8c8c]",
    tooltip: "작업 시작 대기 중",
  };
}

/**
 * 정렬 함수 생성
 */
export function createSortComparator(
  key: "deadline" | "step" | "created_at",
  direction: 1 | -1,
) {
  return (a: ProposalSummary, b: ProposalSummary): number => {
    if (key === "deadline") {
      const da = a.deadline ? new Date(a.deadline).getTime() : Infinity;
      const db = b.deadline ? new Date(b.deadline).getTime() : Infinity;
      return (da - db) * direction;
    }
    if (key === "step") {
      return (
        (getStepInfo(a.current_phase).step -
          getStepInfo(b.current_phase).step) *
        direction
      );
    }
    if (key === "created_at") {
      return (
        (new Date(a.created_at).getTime() - new Date(b.created_at).getTime()) *
        direction
      );
    }
    return 0;
  };
}

/**
 * 스코프 레이블
 */
export type Scope = "my" | "team" | "division" | "company";

export const SCOPE_LABELS: Record<Scope, { label: string; desc: string }> = {
  my: { label: "개인", desc: "내가 생성한 프로젝트" },
  team: { label: "팀", desc: "우리 팀 프로젝트" },
  division: { label: "본부", desc: "우리 본부 프로젝트" },
  company: { label: "전체", desc: "전사 프로젝트" },
};
