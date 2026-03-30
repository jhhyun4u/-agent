"use client";

/**
 * GoNoGoPanel — Go/No-Go 의사결정 전용 패널 (§13-3, v4.0)
 *
 * v4.0: 4축 정량 스코어링 (유사실적·자격·경쟁·전략) + 70점 게이트.
 * 포지셔닝 선택 + 의사결정 사유 + Go/No-Go/빠른승인 버튼.
 */

import { useEffect, useState } from "react";
import { api, type WorkflowState, type WorkflowResumeData } from "@/lib/api";

// ── 타입 ──

interface PerformanceDetail {
  score: number;
  required_items?: Array<{
    raw_text: string;
    min_count: number;
    matched_count: number;
    is_met: boolean;
    matched_projects?: Array<{ title: string; amount: number; year: string }>;
  }>;
  coverage_rate?: number;
  same_client_wins?: number;
  is_fatal?: boolean;
  fatal_reason?: string;
}

interface QualificationDetail {
  score: number;
  mandatory?: Array<{
    requirement: string;
    status: "met" | "unmet" | "partial";
    matched_capability?: string;
  }>;
  preferred?: Array<{
    requirement: string;
    status: "met" | "unmet";
  }>;
  is_fatal?: boolean;
  fatal_reason?: string;
  summary?: string;
}

interface CompetitionDetail {
  score: number;
  intensity_level?: "low" | "medium" | "high";
  estimated_competitors?: number;
  top_competitors?: Array<{
    name: string;
    wins_at_client: number;
    head_to_head: string;
  }>;
  our_win_rate_at_client?: number;
  rationale?: string;
}

interface GngAnalysis {
  win_probability?: number;
  scores?: Array<{ label: string; score: number; max?: number }>;
  strengths?: string[];
  risks?: string[];
  recommendation?: string;
  fatal_flaw?: string | null;
  strategic_focus?: string | null;
  score_tag?: string;
  score_breakdown?: Record<string, number>;
  performance_detail?: PerformanceDetail;
  qualification_detail?: QualificationDetail;
  competition_detail?: CompetitionDetail;
}

interface GoNoGoPanelProps {
  proposalId: string;
  workflowState: WorkflowState;
  onStateChange?: () => void;
  className?: string;
}

const POS_OPTIONS = [
  { value: "defensive", label: "수성형", icon: "🛡️" },
  { value: "offensive", label: "공격형", icon: "⚔️" },
  { value: "adjacent", label: "인접형", icon: "🔄" },
] as const;

const AXES = [
  { key: "similar_performance", label: "유사실적", max: 30 },
  { key: "qualification", label: "자격적격", max: 30 },
  { key: "competition", label: "경쟁강도", max: 20 },
  { key: "strategic", label: "전략가산", max: 20 },
] as const;

const TAG_LABELS: Record<string, { text: string; color: string }> = {
  priority: { text: "적극 참여", color: "text-[#3ecf8e] bg-[#3ecf8e]/10 border-[#3ecf8e]/30" },
  standard: { text: "일반 참여", color: "text-amber-400 bg-amber-500/10 border-amber-500/30" },
  below_threshold: { text: "기준 미달", color: "text-red-400 bg-red-500/10 border-red-500/30" },
  disqualified: { text: "자격 미달", color: "text-red-400 bg-red-500/10 border-red-500/30" },
};

function barColor(score: number, max: number) {
  const pct = max > 0 ? score / max : 0;
  if (pct >= 0.7) return "bg-[#3ecf8e]";
  if (pct >= 0.5) return "bg-amber-500";
  return "bg-red-500";
}

function scoreColor(score: number) {
  if (score >= 85) return "text-[#3ecf8e]";
  if (score >= 70) return "text-amber-400";
  return "text-red-400";
}

export default function GoNoGoPanel({
  proposalId,
  workflowState,
  onStateChange,
  className = "",
}: GoNoGoPanelProps) {
  const [posOverride, setPosOverride] = useState(workflowState.positioning ?? "");
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [confirmNoGo, setConfirmNoGo] = useState(false);

  // 접기/펼치기
  const [expandPerf, setExpandPerf] = useState(false);
  const [expandQual, setExpandQual] = useState(false);
  const [expandComp, setExpandComp] = useState(false);

  // AI 분석 결과 로드
  const [analysis, setAnalysis] = useState<GngAnalysis | null>(null);
  useEffect(() => {
    api.artifacts.get(proposalId, "go_no_go").then((a) => {
      const d = a.data as Record<string, unknown>;
      setAnalysis({
        win_probability: d.feasibility_score as number | undefined,
        scores: d.scores as GngAnalysis["scores"],
        strengths: d.pros as string[] | undefined,
        risks: d.risks as string[] | undefined,
        recommendation: d.recommendation as string | undefined,
        fatal_flaw: (d.fatal_flaw as string | null) ?? null,
        strategic_focus: (d.strategic_focus as string | null) ?? null,
        score_tag: d.score_tag as string | undefined,
        score_breakdown: d.score_breakdown as Record<string, number> | undefined,
        performance_detail: d.performance_detail as PerformanceDetail | undefined,
        qualification_detail: d.qualification_detail as QualificationDetail | undefined,
        competition_detail: d.competition_detail as CompetitionDetail | undefined,
      });
    }).catch(() => {});
  }, [proposalId]);

  // 포지셔닝 변경 영향 미리보기
  const [impactInfo, setImpactInfo] = useState<{ affected_steps: number[]; message: string } | null>(null);
  useEffect(() => {
    if (posOverride && posOverride !== workflowState.positioning) {
      api.workflow.impact(proposalId, "go_no_go").then((res) => {
        setImpactInfo(res);
      }).catch(() => setImpactInfo(null));
    } else {
      setImpactInfo(null);
    }
  }, [posOverride, workflowState.positioning, proposalId]);

  async function handleSubmit(approved: boolean) {
    setSubmitting(true);
    try {
      const data: WorkflowResumeData = {
        approved,
        decision: approved ? "go" : "no_go",
        feedback: feedback || undefined,
        positioning_override:
          posOverride !== workflowState.positioning ? posOverride : undefined,
      };
      await api.workflow.resume(proposalId, data);
      onStateChange?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "요청 실패");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleQuickApprove() {
    setSubmitting(true);
    try {
      const data: WorkflowResumeData = {
        approved: true,
        quick_approve: true,
        decision: "go",
        positioning_override:
          posOverride !== workflowState.positioning ? posOverride : undefined,
      };
      await api.workflow.resume(proposalId, data);
      onStateChange?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "요청 실패");
    } finally {
      setSubmitting(false);
    }
  }

  const totalScore = analysis?.win_probability ?? 0;
  const tag = analysis?.score_tag ? TAG_LABELS[analysis.score_tag] : null;
  const breakdown = analysis?.score_breakdown;
  const isFatal = analysis?.score_tag === "disqualified";

  return (
    <div className={`bg-[#1c1c1c] rounded-2xl border border-amber-500/30 p-5 ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
        <h2 className="text-sm font-semibold text-[#ededed]">Go/No-Go 의사결정</h2>
        <span className="text-[10px] text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded">
          승인 대기
        </span>
      </div>

      <p className="text-xs text-[#8c8c8c] mb-4">이 입찰에 자원을 투입할 가치가 있는가?</p>

      {/* Fatal 배너 */}
      {isFatal && analysis?.fatal_flaw && (
        <div className="mb-4 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3">
          <p className="text-xs font-semibold text-red-400 mb-1">참가자격 미달</p>
          <p className="text-[11px] text-[#ededed]">{analysis.fatal_flaw}</p>
        </div>
      )}

      {/* 합산 점수 + 태그 */}
      {analysis && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <span className={`text-2xl font-bold ${scoreColor(totalScore)}`}>{totalScore}</span>
              <span className="text-xs text-[#8c8c8c]">/ 100</span>
            </div>
            {tag && (
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded border ${tag.color}`}>
                {tag.text}
              </span>
            )}
          </div>
          {/* 전체 진행바 + 70점 컷라인 */}
          <div className="relative h-2 bg-[#262626] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${scoreColor(totalScore).replace("text-", "bg-")}`}
              style={{ width: `${totalScore}%` }}
            />
            <div
              className="absolute top-0 h-full w-px bg-amber-500/60"
              style={{ left: "70%" }}
              title="70점 컷라인"
            />
          </div>
          <p className="text-[9px] text-[#5c5c5c] mt-1 text-right">70점 컷라인</p>
        </div>
      )}

      {/* 4축 바 차트 */}
      {breakdown && (
        <div className="mb-4 space-y-2">
          {AXES.map((axis) => {
            const val = breakdown[axis.key] ?? 0;
            const pct = axis.max > 0 ? (val / axis.max) * 100 : 0;
            return (
              <div key={axis.key} className="flex items-center gap-2">
                <span className="text-[10px] text-[#8c8c8c] w-14 shrink-0">{axis.label}</span>
                <div className="flex-1 h-1.5 bg-[#262626] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${barColor(val, axis.max)}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="text-[10px] text-[#8c8c8c] w-10 text-right">{val}/{axis.max}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* 유사실적 상세 (접기/펼치기) */}
      {analysis?.performance_detail && (
        <CollapsibleSection
          title="유사실적 상세"
          expanded={expandPerf}
          onToggle={() => setExpandPerf(!expandPerf)}
          score={analysis.performance_detail.score}
          max={30}
          isFatal={analysis.performance_detail.is_fatal}
        >
          {analysis.performance_detail.required_items?.map((item, i) => (
            <div key={i} className="mb-2">
              <p className="text-[10px] text-[#8c8c8c]">
                {item.is_met ? "✅" : "❌"} {item.raw_text}
                <span className="text-[#5c5c5c]"> ({item.matched_count}/{item.min_count}건)</span>
              </p>
              {item.matched_projects?.slice(0, 3).map((p, j) => (
                <p key={j} className="text-[10px] text-[#5c5c5c] pl-4">
                  · {p.year} {p.title} ({formatAmount(p.amount)})
                </p>
              ))}
            </div>
          ))}
          {(analysis.performance_detail.same_client_wins ?? 0) > 0 && (
            <p className="text-[10px] text-[#3ecf8e]">
              동일 발주기관 수주: {analysis.performance_detail.same_client_wins}건
            </p>
          )}
        </CollapsibleSection>
      )}

      {/* 자격 적격성 상세 */}
      {analysis?.qualification_detail && (
        <CollapsibleSection
          title="자격 적격성"
          expanded={expandQual}
          onToggle={() => setExpandQual(!expandQual)}
          score={analysis.qualification_detail.score}
          max={30}
          isFatal={analysis.qualification_detail.is_fatal}
        >
          {analysis.qualification_detail.summary && (
            <p className="text-[10px] text-[#8c8c8c] mb-1">{analysis.qualification_detail.summary}</p>
          )}
          {analysis.qualification_detail.mandatory?.map((m, i) => (
            <p key={i} className="text-[10px] text-[#8c8c8c]">
              {m.status === "met" ? "✅" : m.status === "partial" ? "⚠️" : "❌"} {m.requirement}
              {m.matched_capability && <span className="text-[#5c5c5c]"> → {m.matched_capability}</span>}
            </p>
          ))}
          {analysis.qualification_detail.preferred && analysis.qualification_detail.preferred.length > 0 && (
            <>
              <p className="text-[9px] text-[#5c5c5c] mt-1 uppercase">가점 항목</p>
              {analysis.qualification_detail.preferred.map((p, i) => (
                <p key={i} className="text-[10px] text-[#8c8c8c]">
                  {p.status === "met" ? "✅" : "⬜"} {p.requirement}
                </p>
              ))}
            </>
          )}
        </CollapsibleSection>
      )}

      {/* 경쟁 강도 상세 */}
      {analysis?.competition_detail && (
        <CollapsibleSection
          title="경쟁 강도"
          expanded={expandComp}
          onToggle={() => setExpandComp(!expandComp)}
          score={analysis.competition_detail.score}
          max={20}
        >
          <p className="text-[10px] text-[#8c8c8c]">
            예상 참여: {analysis.competition_detail.estimated_competitors ?? "?"}개사
            ({analysis.competition_detail.intensity_level === "low" ? "낮음" : analysis.competition_detail.intensity_level === "high" ? "높음" : "보통"})
          </p>
          {analysis.competition_detail.our_win_rate_at_client != null && (
            <p className="text-[10px] text-[#8c8c8c]">
              해당 기관 자사 승률: {Math.round(analysis.competition_detail.our_win_rate_at_client * 100)}%
            </p>
          )}
          {analysis.competition_detail.top_competitors?.map((c, i) => (
            <p key={i} className="text-[10px] text-[#5c5c5c] pl-2">
              · {c.name}: {c.head_to_head}
            </p>
          ))}
        </CollapsibleSection>
      )}

      {/* 강점 / 리스크 */}
      {analysis && (
        <div className="grid grid-cols-2 gap-2 mb-4">
          {analysis.strengths && analysis.strengths.length > 0 && (
            <div>
              <p className="text-[9px] text-[#3ecf8e] uppercase tracking-wider mb-1">강점</p>
              {analysis.strengths.slice(0, 3).map((s, i) => (
                <p key={i} className="text-[10px] text-[#8c8c8c] leading-relaxed">+ {s}</p>
              ))}
            </div>
          )}
          {analysis.risks && analysis.risks.length > 0 && (
            <div>
              <p className="text-[9px] text-red-400 uppercase tracking-wider mb-1">리스크</p>
              {analysis.risks.slice(0, 3).map((r, i) => (
                <p key={i} className="text-[10px] text-[#8c8c8c] leading-relaxed">- {r}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* AI 추천 + 핵심 승부수 */}
      {analysis?.recommendation && !isFatal && (
        <div className="bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 mb-4">
          <p className="text-[10px] text-[#8c8c8c]">
            AI 추천: <span className={analysis.recommendation === "go" ? "text-[#3ecf8e] font-bold" : "text-red-400 font-bold"}>{analysis.recommendation.toUpperCase()}</span>
          </p>
        </div>
      )}

      {analysis?.strategic_focus && !isFatal && (
        <div className="bg-[#3ecf8e]/5 border border-[#3ecf8e]/20 rounded-lg px-3 py-2 mb-4">
          <p className="text-[9px] text-[#3ecf8e] uppercase tracking-wider mb-0.5">핵심 승부수</p>
          <p className="text-[10px] text-[#ededed]">{analysis.strategic_focus}</p>
        </div>
      )}

      {/* 포지셔닝 선택 */}
      <div className="mb-4">
        <p className="text-[10px] text-[#8c8c8c] mb-2 uppercase tracking-wider">포지셔닝 추천</p>
        <div className="flex gap-2">
          {POS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPosOverride(opt.value)}
              className={`flex-1 py-2 text-xs font-medium rounded-lg border transition-colors ${
                posOverride === opt.value
                  ? "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/40"
                  : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c]"
              }`}
            >
              {opt.icon} {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* 포지셔닝 변경 영향 */}
      {impactInfo && (
        <div className="mb-4 bg-amber-500/5 border border-amber-500/20 rounded-lg px-3 py-2">
          <p className="text-[10px] text-amber-400 font-medium mb-1">포지셔닝 변경 영향</p>
          <p className="text-[10px] text-[#8c8c8c]">{impactInfo.message}</p>
          {impactInfo.affected_steps.length > 0 && (
            <p className="text-[10px] text-amber-400/70 mt-1">
              재생성 대상: STEP {impactInfo.affected_steps.join(", ")}
            </p>
          )}
        </div>
      )}

      {/* 의사결정 사유 */}
      <div className="mb-4">
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="의사결정 사유 (선택)"
          rows={2}
          className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-xs text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-amber-500/40 resize-none"
        />
      </div>

      {/* No-Go 확인 모달 */}
      {confirmNoGo && (
        <div className="mb-4 bg-red-500/5 border border-red-500/30 rounded-lg p-4">
          <p className="text-xs text-red-400 font-medium mb-2">정말 No-Go 처리하시겠습니까?</p>
          <p className="text-[10px] text-[#8c8c8c] mb-3">No-Go 결정 시 이 프로젝트의 워크플로가 종료됩니다.</p>
          <div className="flex gap-2">
            <button
              onClick={() => setConfirmNoGo(false)}
              className="flex-1 py-1.5 text-xs rounded-lg border border-[#262626] text-[#8c8c8c] hover:bg-[#1c1c1c] transition-colors"
            >
              취소
            </button>
            <button
              onClick={() => { setConfirmNoGo(false); handleSubmit(false); }}
              disabled={submitting}
              className="flex-1 py-1.5 text-xs font-semibold rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30 disabled:opacity-40 transition-colors"
            >
              No-Go 확정
            </button>
          </div>
        </div>
      )}

      {/* 버튼 */}
      <div className="flex gap-2">
        <button
          onClick={() => setConfirmNoGo(true)}
          disabled={submitting || confirmNoGo}
          className="flex-1 py-2.5 text-xs font-semibold rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 disabled:opacity-40 transition-colors"
        >
          No-Go
        </button>
        <button
          onClick={handleQuickApprove}
          disabled={submitting}
          className="flex-1 py-2.5 text-xs font-semibold rounded-lg border border-[#3ecf8e]/30 text-[#3ecf8e] hover:bg-[#3ecf8e]/10 disabled:opacity-40 transition-colors"
        >
          빠른 승인
        </button>
        <button
          onClick={() => handleSubmit(true)}
          disabled={submitting}
          className="flex-1 py-2.5 text-xs font-bold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 disabled:opacity-40 transition-colors"
        >
          Go
        </button>
      </div>
    </div>
  );
}

// ── 헬퍼 컴포넌트 ──

function CollapsibleSection({
  title,
  expanded,
  onToggle,
  score,
  max,
  isFatal,
  children,
}: {
  title: string;
  expanded: boolean;
  onToggle: () => void;
  score: number;
  max: number;
  isFatal?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={`mb-3 border rounded-lg ${isFatal ? "border-red-500/30 bg-red-500/5" : "border-[#262626] bg-[#111111]"}`}>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2 text-left"
      >
        <span className="text-[10px] text-[#8c8c8c] flex items-center gap-1.5">
          <span className={`transition-transform ${expanded ? "rotate-90" : ""}`}>▸</span>
          {title}
          {isFatal && <span className="text-red-400 text-[9px]">(미달)</span>}
        </span>
        <span className={`text-[10px] font-bold ${barColor(score, max).replace("bg-", "text-").replace("500", "400")}`}>
          {score}/{max}
        </span>
      </button>
      {expanded && <div className="px-3 pb-2">{children}</div>}
    </div>
  );
}

function formatAmount(amount: number): string {
  if (!amount) return "-";
  if (amount >= 100_000_000) return `${Math.round(amount / 100_000_000)}억`;
  if (amount >= 10_000) return `${Math.round(amount / 10_000)}만`;
  return `${amount}원`;
}
