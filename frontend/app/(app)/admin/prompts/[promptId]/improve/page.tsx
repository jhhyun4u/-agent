"use client";

/**
 * 개선 워크벤치 — 4스텝 워크플로
 *
 * /admin/prompts/[promptId]/improve
 * STEP 1: 문제파악 (자동 패턴 분석)
 * STEP 2: AI 개선안 생성
 * STEP 3: 시뮬레이션 비교
 * STEP 4: A/B 실험
 */

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  api,
  type PromptAnalysis,
  type PromptSuggestion,
} from "@/lib/api";
import StepProgress, { type StepId } from "@/components/prompt/StepProgress";
import EditPatternChart from "@/components/prompt/EditPatternChart";
import WinLossComparison from "@/components/prompt/WinLossComparison";
import TrendChart from "@/components/prompt/TrendChart";
import SimulationRunner from "@/components/prompt/SimulationRunner";
import CompareView from "@/components/prompt/CompareView";

export default function ImprovementWorkbench() {
  const params = useParams();
  const promptId = decodeURIComponent(params.promptId as string);

  const [step, setStep] = useState<StepId>("diagnose");
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<PromptAnalysis | null>(null);
  const [suggestions, setSuggestions] = useState<PromptSuggestion | null>(null);
  const [suggesting, setSuggesting] = useState(false);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.prompts.analysis(promptId);
      setAnalysis(result);
    } catch {
      setAnalysis(null);
    }
    setLoading(false);
  }, [promptId]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const handleSuggest = async () => {
    setSuggesting(true);
    try {
      const result = await api.prompts.suggestImprovement(promptId);
      setSuggestions(result);
      setStep("suggest");
    } catch {
      setSuggestions({ error: "개선 제안 요청 실패" });
    }
    setSuggesting(false);
  };

  const handleApplyAndSimulate = (text: string) => {
    setStep("simulate");
    // SimulationRunner에 promptText 전달은 state로 관리
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link href="/admin/prompts" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">
            &larr; 대시보드
          </Link>
          <h1 className="text-sm font-semibold">
            {analysis?.label || promptId} 개선
          </h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* 스텝 진행 표시기 */}
        <StepProgress currentStep={step} onStepClick={setStep} />

        {loading && (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            패턴 분석 중...
          </div>
        )}

        {!loading && analysis && (
          <>
            {/* ═══ STEP 1: 문제파악 ═══ */}
            {step === "diagnose" && (
              <div className="space-y-4">
                {/* 핵심 수치 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <MetricCard
                    label="수정율"
                    value={`${((analysis.metrics.avg_edit_ratio || 0) * 100).toFixed(0)}%`}
                    alert={(analysis.metrics.avg_edit_ratio || 0) > 0.5}
                  />
                  <MetricCard label="품질" value={`${analysis.metrics.avg_quality || "-"}점`} />
                  <MetricCard label="수주율" value={`${analysis.metrics.win_rate || "-"}%`} />
                  <MetricCard label="사용 횟수" value={`${analysis.metrics.proposals_used}건`} />
                </div>

                {/* 수정 패턴 */}
                <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                  <EditPatternChart patterns={analysis.edit_patterns} />
                </section>

                {/* 수주/패찰 비교 */}
                {analysis.win_loss_comparison && (analysis.win_loss_comparison.win_count > 0 || analysis.win_loss_comparison.loss_count > 0) && (
                  <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                    <WinLossComparison data={analysis.win_loss_comparison} />
                  </section>
                )}

                {/* 리뷰 피드백 */}
                {analysis.feedback_summary.keywords.length > 0 && (
                  <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                    <h3 className="text-xs font-semibold mb-3">리뷰 피드백 요약</h3>
                    <div className="space-y-1">
                      {analysis.feedback_summary.keywords.map((k) => (
                        <div key={k.word} className="text-xs text-[#8c8c8c]">
                          &quot;{k.word}&quot; ({k.count}회)
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* 추이 */}
                {analysis.trend.length >= 2 && (
                  <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                    <TrendChart data={analysis.trend} metric="quality" />
                  </section>
                )}

                {/* 가설 + 다음 스텝 */}
                <section className="bg-[#1a3a2a] rounded-2xl border border-[#2a4a3a] p-5">
                  <h3 className="text-xs font-semibold text-[#3ecf8e] mb-2">AI 가설</h3>
                  <p className="text-sm">{analysis.hypothesis}</p>
                  <button
                    onClick={handleSuggest}
                    disabled={suggesting}
                    className="mt-4 px-6 py-2 bg-[#3ecf8e] text-black rounded-lg text-xs font-bold hover:bg-[#35b87d] disabled:opacity-50 transition-colors"
                  >
                    {suggesting ? "개선안 생성 중..." : "AI 개선안 생성 →"}
                  </button>
                </section>
              </div>
            )}

            {/* ═══ STEP 2: 개선안 ═══ */}
            {step === "suggest" && (
              <div className="space-y-4">
                {suggestions?.error && (
                  <div className="text-xs text-[#ff6b6b]">{suggestions.error}</div>
                )}
                {suggestions?.analysis && (
                  <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                    <h3 className="text-xs font-semibold mb-2">분석</h3>
                    <p className="text-xs text-[#8c8c8c]">{suggestions.analysis}</p>
                  </div>
                )}
                {suggestions?.suggestions && (
                  <div className="space-y-3">
                    {suggestions.suggestions.map((s, i) => (
                      <div key={i} className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-sm font-semibold">
                            개선안 {String.fromCharCode(65 + i)}: {s.title}
                          </h3>
                        </div>
                        <p className="text-xs text-[#8c8c8c] mb-3">{s.rationale}</p>
                        <div className="flex flex-wrap gap-1 mb-3">
                          {s.key_changes.map((c, j) => (
                            <span key={j} className="text-xs bg-[#262626] px-2 py-0.5 rounded">{c}</span>
                          ))}
                        </div>
                        <div className="flex gap-2">
                          <Link
                            href={`/admin/prompts/${encodeURIComponent(promptId)}`}
                            className="px-3 py-1.5 bg-[#262626] hover:bg-[#333] rounded-lg text-xs transition-colors"
                          >
                            편집기에서 보기
                          </Link>
                          <button
                            onClick={() => handleApplyAndSimulate(s.prompt_text)}
                            className="px-3 py-1.5 bg-[#3ecf8e] text-black rounded-lg text-xs font-medium hover:bg-[#35b87d] transition-colors"
                          >
                            시뮬레이션 →
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {!suggestions && (
                  <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-8 text-center">
                    <button
                      onClick={handleSuggest}
                      disabled={suggesting}
                      className="px-6 py-2 bg-[#3ecf8e] text-black rounded-lg text-xs font-bold hover:bg-[#35b87d] disabled:opacity-50"
                    >
                      {suggesting ? "생성 중..." : "AI 개선안 생성"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ═══ STEP 3: 시뮬레이션 ═══ */}
            {step === "simulate" && (
              <div className="space-y-4">
                <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                  <h3 className="text-xs font-semibold mb-2">단독 실행</h3>
                  <SimulationRunner promptId={promptId} />
                </div>
                <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                  <h3 className="text-xs font-semibold mb-2">A vs B 비교</h3>
                  <CompareView promptId={promptId} />
                </div>
                <button
                  onClick={() => setStep("experiment")}
                  className="px-6 py-2 bg-[#3ecf8e] text-black rounded-lg text-xs font-bold hover:bg-[#35b87d] transition-colors"
                >
                  A/B 실험으로 →
                </button>
              </div>
            )}

            {/* ═══ STEP 4: 실험 ═══ */}
            {step === "experiment" && (
              <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 text-center">
                <h3 className="text-sm font-semibold mb-4">A/B 실험</h3>
                <p className="text-xs text-[#8c8c8c] mb-4">
                  시뮬레이션에서 선택한 개선안을 실제 제안서에서 A/B 테스트합니다.
                </p>
                <Link
                  href="/admin/prompts/experiments"
                  className="inline-block px-6 py-2 bg-[#3ecf8e] text-black rounded-lg text-xs font-bold hover:bg-[#35b87d] transition-colors"
                >
                  A/B 실험 대시보드 →
                </Link>
              </div>
            )}
          </>
        )}

        {!loading && !analysis && (
          <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-8 text-center">
            <div className="text-[#8c8c8c] text-sm">이 프롬프트의 분석 데이터가 없습니다.</div>
            <Link href="/admin/prompts" className="inline-block mt-4 text-xs text-[#3ecf8e] hover:underline">
              대시보드로 돌아가기
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}

function MetricCard({ label, value, alert }: { label: string; value: string; alert?: boolean }) {
  return (
    <div className={`rounded-xl border p-3 ${alert ? "bg-[#2a1a1a] border-[#4a2020]" : "bg-[#1c1c1c] border-[#262626]"}`}>
      <div className="text-[#8c8c8c] text-xs">{label}</div>
      <div className={`text-lg font-bold mt-0.5 ${alert ? "text-[#ff6b6b]" : ""}`}>{value}</div>
    </div>
  );
}
