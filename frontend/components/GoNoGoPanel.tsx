"use client";

/**
 * GoNoGoPanel — Go/No-Go 의사결정 전용 패널 (§13-3)
 *
 * WorkflowPanel에서 분리된 STEP 1-② 전용 컴포넌트.
 * 포지셔닝 선택 + 의사결정 사유 + Go/No-Go/빠른승인 버튼.
 */

import { useEffect, useState } from "react";
import { api, type WorkflowState, type WorkflowResumeData } from "@/lib/api";

interface GngAnalysis {
  win_probability?: number;
  scores?: Array<{ label: string; score: number }>;
  strengths?: string[];
  risks?: string[];
  recommendation?: string;
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

export default function GoNoGoPanel({
  proposalId,
  workflowState,
  onStateChange,
  className = "",
}: GoNoGoPanelProps) {
  const [posOverride, setPosOverride] = useState(
    workflowState.positioning ?? ""
  );
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // AI 분석 결과 로드 (go_no_go 산출물)
  const [analysis, setAnalysis] = useState<GngAnalysis | null>(null);
  useEffect(() => {
    api.artifacts.get(proposalId, "go_no_go").then((a) => {
      const d = a.data as Record<string, unknown>;
      setAnalysis({
        win_probability: d.win_probability as number | undefined,
        scores: d.scores as GngAnalysis["scores"],
        strengths: d.strengths as string[] | undefined,
        risks: d.risks as string[] | undefined,
        recommendation: d.recommendation as string | undefined,
      });
    }).catch(() => {});
  }, [proposalId]);

  // 포지셔닝 변경 영향 미리보기 (§13-6)
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
          posOverride !== workflowState.positioning
            ? posOverride
            : undefined,
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
          posOverride !== workflowState.positioning
            ? posOverride
            : undefined,
      };
      await api.workflow.resume(proposalId, data);
      onStateChange?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "요청 실패");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className={`bg-[#1c1c1c] rounded-2xl border border-amber-500/30 p-5 ${className}`}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
        <h2 className="text-sm font-semibold text-[#ededed]">
          Go/No-Go 의사결정
        </h2>
        <span className="text-[10px] text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded">
          승인 대기
        </span>
      </div>

      <p className="text-xs text-[#8c8c8c] mb-4">
        이 입찰에 자원을 투입할 가치가 있는가?
      </p>

      {/* 포지셔닝 선택 */}
      <div className="mb-4">
        <p className="text-[10px] text-[#8c8c8c] mb-2 uppercase tracking-wider">
          포지셔닝 추천
        </p>
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

      {/* 포지셔닝 변경 영향 미리보기 (§13-6) */}
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

      {/* AI 분석 결과 (§13-4 보강) */}
      {analysis && (
        <div className="mb-4 space-y-3">
          {/* 수주 가능성 */}
          {analysis.win_probability != null && (
            <div className="flex items-center gap-3">
              <span className="text-[10px] text-[#8c8c8c] uppercase tracking-wider w-16 shrink-0">수주 가능성</span>
              <div className="flex-1 h-2 bg-[#262626] rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${analysis.win_probability >= 70 ? "bg-[#3ecf8e]" : analysis.win_probability >= 50 ? "bg-amber-500" : "bg-red-500"}`}
                  style={{ width: `${analysis.win_probability}%` }}
                />
              </div>
              <span className={`text-xs font-bold ${analysis.win_probability >= 70 ? "text-[#3ecf8e]" : analysis.win_probability >= 50 ? "text-amber-400" : "text-red-400"}`}>
                {analysis.win_probability}%
              </span>
            </div>
          )}

          {/* 항목별 점수 */}
          {analysis.scores && analysis.scores.length > 0 && (
            <div className="grid grid-cols-2 gap-1.5">
              {analysis.scores.map((s) => (
                <div key={s.label} className="flex items-center justify-between bg-[#111111] rounded px-2.5 py-1.5">
                  <span className="text-[10px] text-[#8c8c8c]">{s.label}</span>
                  <span className={`text-[10px] font-bold ${s.score >= 70 ? "text-[#3ecf8e]" : s.score >= 50 ? "text-amber-400" : "text-red-400"}`}>{s.score}</span>
                </div>
              ))}
            </div>
          )}

          {/* 강점 / 리스크 */}
          <div className="grid grid-cols-2 gap-2">
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

          {/* AI 추천 */}
          {analysis.recommendation && (
            <div className="bg-[#111111] border border-[#262626] rounded-lg px-3 py-2">
              <p className="text-[10px] text-[#8c8c8c]">{analysis.recommendation}</p>
            </div>
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

      {/* 버튼 */}
      <div className="flex gap-2">
        <button
          onClick={() => handleSubmit(false)}
          disabled={submitting}
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
