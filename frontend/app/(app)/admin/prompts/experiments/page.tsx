"use client";

/**
 * A/B 실험 대시보드
 *
 * /admin/prompts/experiments
 * - 진행 중 실험: 실시간 메트릭 비교
 * - 완료된 실험: 결과 + 교훈
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  type PromptExperiment,
  type ExperimentEvaluation,
} from "@/lib/api";

export default function ExperimentsPage() {
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<PromptExperiment[]>([]);
  const [completed, setCompleted] = useState<PromptExperiment[]>([]);
  const [evaluating, setEvaluating] = useState<string | null>(null);
  const [evalResult, setEvalResult] = useState<ExperimentEvaluation | null>(
    null,
  );

  const fetchData = useCallback(async () => {
    setLoading(true);
    const [runRes, compRes] = await Promise.allSettled([
      api.prompts.experiments.list("running"),
      api.prompts.experiments.list("completed"),
    ]);
    if (runRes.status === "fulfilled") setRunning(runRes.value.experiments);
    if (compRes.status === "fulfilled") setCompleted(compRes.value.experiments);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleEvaluate = async (id: string) => {
    setEvaluating(id);
    try {
      const result = await api.prompts.experiments.evaluate(id);
      setEvalResult(result);
    } catch {
      alert("평가 실패");
    }
    setEvaluating(null);
  };

  const handlePromote = async (id: string) => {
    if (!confirm("후보 프롬프트를 활성화하시겠습니까?")) return;
    try {
      await api.prompts.experiments.promote(id);
      alert("승격 완료");
      fetchData();
    } catch {
      alert("승격 실패");
    }
  };

  const handleRollback = async (id: string) => {
    if (!confirm("실험을 롤백하시겠습니까?")) return;
    try {
      await api.prompts.experiments.rollback(id);
      alert("롤백 완료");
      fetchData();
    } catch {
      alert("롤백 실패");
    }
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link
            href="/admin/prompts"
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
          >
            &larr; 프롬프트 대시보드
          </Link>
          <h1 className="text-sm font-semibold">A/B 실험 관리</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            로딩 중...
          </div>
        )}

        {!loading && (
          <>
            {/* 진행 중 실험 */}
            <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
              <h2 className="text-sm font-semibold mb-4">
                진행 중 ({running.length})
              </h2>
              {running.length === 0 ? (
                <div className="text-xs text-[#8c8c8c]">
                  진행 중인 실험이 없습니다.
                </div>
              ) : (
                <div className="space-y-4">
                  {running.map((exp) => (
                    <div
                      key={exp.id}
                      className="bg-[#111] rounded-lg border border-[#262626] p-4"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <div className="text-xs font-semibold">
                            {exp.experiment_name}
                          </div>
                          <div className="text-xs text-[#8c8c8c] mt-0.5">
                            <span className="font-mono">{exp.prompt_id}</span>{" "}
                            &middot; v{exp.baseline_version} vs v
                            {exp.candidate_version} &middot; {exp.traffic_pct}%
                            트래픽
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEvaluate(exp.id)}
                            disabled={evaluating === exp.id}
                            className="px-3 py-1 bg-[#262626] hover:bg-[#333] rounded text-xs transition-colors disabled:opacity-50"
                          >
                            {evaluating === exp.id ? "평가 중..." : "평가"}
                          </button>
                          <button
                            onClick={() => handlePromote(exp.id)}
                            className="px-3 py-1 bg-[#1a3a2a] hover:bg-[#2a4a3a] text-[#3ecf8e] rounded text-xs transition-colors"
                          >
                            승격
                          </button>
                          <button
                            onClick={() => handleRollback(exp.id)}
                            className="px-3 py-1 bg-[#3a1a1a] hover:bg-[#4a2a2a] text-[#ff6b6b] rounded text-xs transition-colors"
                          >
                            롤백
                          </button>
                        </div>
                      </div>

                      {evalResult?.experiment_id === exp.id && (
                        <div className="mt-3 p-3 bg-[#0a0a0a] rounded text-xs">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <div className="text-[#8c8c8c] mb-1">
                                Baseline v{exp.baseline_version}
                              </div>
                              <div>
                                샘플:{" "}
                                {(evalResult.baseline as Record<string, number>)
                                  ?.samples ?? 0}
                              </div>
                            </div>
                            <div>
                              <div className="text-[#f5a623] mb-1">
                                Candidate v{exp.candidate_version}
                              </div>
                              <div>
                                샘플:{" "}
                                {(
                                  evalResult.candidate as Record<string, number>
                                )?.samples ?? 0}
                              </div>
                            </div>
                          </div>
                          {evalResult.recommendation && (
                            <div className="mt-2 pt-2 border-t border-[#262626]">
                              <span
                                className={`px-2 py-0.5 rounded text-xs ${
                                  evalResult.recommendation === "promote"
                                    ? "bg-[#1a3a2a] text-[#3ecf8e]"
                                    : evalResult.recommendation === "rollback"
                                      ? "bg-[#3a1a1a] text-[#ff6b6b]"
                                      : "bg-[#1a1a1a] text-[#8c8c8c]"
                                }`}
                              >
                                {evalResult.recommendation === "promote"
                                  ? "승격 권장"
                                  : evalResult.recommendation === "rollback"
                                    ? "롤백 권장"
                                    : "계속 진행"}
                              </span>
                              {evalResult.improvement != null && (
                                <span className="ml-2 text-[#8c8c8c]">
                                  개선도:{" "}
                                  {evalResult.improvement > 0 ? "+" : ""}
                                  {evalResult.improvement}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* 완료된 실험 */}
            <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
              <h2 className="text-sm font-semibold mb-4">
                완료된 실험 ({completed.length})
              </h2>
              {completed.length === 0 ? (
                <div className="text-xs text-[#8c8c8c]">
                  완료된 실험이 없습니다.
                </div>
              ) : (
                <div className="space-y-3">
                  {completed.map((exp) => (
                    <div
                      key={exp.id}
                      className="bg-[#111] rounded-lg border border-[#262626] p-3"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold">
                            {exp.experiment_name}
                          </span>
                          <span className="ml-2 text-xs text-[#8c8c8c]">
                            {exp.conclusion}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {exp.promoted_version && (
                            <span className="text-xs text-[#3ecf8e]">
                              v{exp.promoted_version} 승격
                            </span>
                          )}
                          <span className="text-xs text-[#8c8c8c]">
                            {exp.ended_at
                              ? new Date(exp.ended_at).toLocaleDateString("ko")
                              : ""}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
