"use client";

/**
 * EvaluationView — 모의평가 전체 뷰 (§13-11)
 *
 * 평가위원 3인 점수 카드 + 레이더 차트 + 취약점 TOP 3 + 예상 Q&A
 */

import { useState } from "react";
import Link from "next/link";
import EvaluationRadar from "./EvaluationRadar";
import type { EvaluationSimulation, EvaluatorScore } from "@/lib/api";

// ── 유틸 ──

function scoreColor(score: number): string {
  if (score >= 85) return "text-[#3ecf8e]";
  if (score >= 70) return "text-amber-400";
  return "text-red-400";
}

function scoreBg(score: number): string {
  if (score >= 85) return "bg-[#3ecf8e]/15 border-[#3ecf8e]/30";
  if (score >= 70) return "bg-amber-500/15 border-amber-500/30";
  return "bg-red-500/15 border-red-500/30";
}

const AXIS_LABELS: Record<string, string> = {
  compliance: "적합성",
  strategy: "전략성",
  quality: "품질",
  trustworthiness: "신뢰성",
};

// ── 메인 컴포넌트 ──

interface EvaluationViewProps {
  proposalId: string;
  evaluation: EvaluationSimulation;
  className?: string;
}

export default function EvaluationView({
  proposalId,
  evaluation,
  className = "",
}: EvaluationViewProps) {
  const { evaluators, average_scores, weaknesses, expected_qa } = evaluation;
  const [expandedQa, setExpandedQa] = useState<number | null>(null);

  const avgTotal = average_scores.total;

  return (
    <div className={`space-y-5 ${className}`}>
      {/* ── 종합 점수 헤더 ── */}
      <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-[#ededed]">
            모의평가 결과
          </h2>
          <div className={`text-lg font-bold ${scoreColor(avgTotal)}`}>
            {avgTotal.toFixed(1)}
            <span className="text-xs text-[#8c8c8c] font-normal"> / 100</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* 좌측: 평가위원 카드 */}
          <div className="space-y-3">
            {evaluators.map((ev, idx) => (
              <EvaluatorCard key={idx} evaluator={ev} index={idx} />
            ))}
          </div>

          {/* 우측: 레이더 차트 */}
          <div>
            <EvaluationRadar scores={average_scores} />
          </div>
        </div>
      </div>

      {/* ── 취약점 TOP 3 ── */}
      {weaknesses.length > 0 && (
        <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
          <h3 className="text-sm font-semibold text-[#ededed] mb-3">
            취약점 TOP {Math.min(weaknesses.length, 3)}
          </h3>
          <div className="space-y-2.5">
            {weaknesses.slice(0, 3).map((w, idx) => (
              <div
                key={idx}
                className="flex gap-3 bg-[#111111] border border-[#262626] rounded-xl px-4 py-3"
              >
                <span className="text-xs font-bold text-amber-400 shrink-0 mt-0.5">
                  {idx + 1}.
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-[#ededed] mb-0.5">
                    {w.area} —{" "}
                    <span className="text-[#8c8c8c] font-normal">
                      {w.description}
                    </span>
                  </p>
                  {w.related_section && (
                    <Link
                      href={`/proposals/${proposalId}/edit#${w.related_section}`}
                      className="text-[10px] text-[#3ecf8e] hover:underline"
                    >
                      편집기에서 열기
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 예상 Q&A ── */}
      {expected_qa.length > 0 && (
        <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
          <h3 className="text-sm font-semibold text-[#ededed] mb-3">
            예상 Q&A
          </h3>
          <div className="space-y-2">
            {expected_qa.map((qa, idx) => (
              <div
                key={idx}
                className="bg-[#111111] border border-[#262626] rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setExpandedQa(expandedQa === idx ? null : idx)}
                  className="w-full flex items-center gap-2 px-4 py-3 text-left"
                >
                  <svg
                    className={`w-3 h-3 text-[#8c8c8c] shrink-0 transition-transform ${
                      expandedQa === idx ? "rotate-90" : ""
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  <span className="text-xs font-medium text-[#ededed]">
                    Q{idx + 1}. {qa.question}
                  </span>
                </button>
                {expandedQa === idx && (
                  <div className="px-4 pb-3 pt-0">
                    <div className="pl-5 border-l-2 border-[#3ecf8e]/30">
                      <p className="text-[10px] text-[#8c8c8c] mb-1">
                        모범답변:
                      </p>
                      <p className="text-xs text-[#ededed] leading-relaxed">
                        {qa.answer}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── 평가위원 카드 ──

function EvaluatorCard({
  evaluator,
  index,
}: {
  evaluator: { role: string; scores: EvaluatorScore; comments: string };
  index: number;
}) {
  const icons = ["👤", "👤", "👤"];
  const { scores, role, comments } = evaluator;

  return (
    <div className="bg-[#111111] border border-[#262626] rounded-xl p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-[#ededed]">
          {icons[index] ?? "👤"} 평가위원 {String.fromCharCode(65 + index)} (
          {role})
        </span>
        <span className={`text-sm font-bold ${scoreColor(scores.total)}`}>
          {scores.total}점
        </span>
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        {(Object.keys(AXIS_LABELS) as Array<keyof typeof AXIS_LABELS>).map(
          (key) => {
            const score = scores[key as keyof EvaluatorScore];
            if (typeof score !== "number") return null;
            return (
              <div
                key={key}
                className={`flex items-center justify-between px-2 py-1 rounded border text-[10px] ${scoreBg(score)}`}
              >
                <span className="text-[#8c8c8c]">{AXIS_LABELS[key]}</span>
                <span className={`font-medium ${scoreColor(score)}`}>
                  {score}점
                </span>
              </div>
            );
          },
        )}
      </div>

      {comments && (
        <p className="mt-2 text-[10px] text-[#8c8c8c] leading-relaxed line-clamp-2">
          {comments}
        </p>
      )}
    </div>
  );
}
