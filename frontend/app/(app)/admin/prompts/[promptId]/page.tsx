"use client";

/**
 * 개별 프롬프트 상세 페이지 — 이력 / 편집 / AI 제안 3탭
 *
 * /admin/prompts/[promptId]
 */

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  api,
  type PromptDetail,
  type PromptEffectiveness,
  type PromptSuggestion,
} from "@/lib/api";
import PromptEditor from "@/components/prompt/PromptEditor";
import PreviewPanel from "@/components/prompt/PreviewPanel";

type Tab = "history" | "edit" | "suggest";

export default function PromptDetailPage() {
  const params = useParams();
  const promptId = decodeURIComponent(params.promptId as string);

  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<PromptDetail | null>(null);
  const [effectiveness, setEffectiveness] =
    useState<PromptEffectiveness | null>(null);
  const [tab, setTab] = useState<Tab>("history");

  // 편집 상태
  const [editText, setEditText] = useState("");
  const [editReason, setEditReason] = useState("");
  const [saving, setSaving] = useState(false);

  // AI 제안 상태
  const [suggestions, setSuggestions] = useState<PromptSuggestion | null>(null);
  const [suggesting, setSuggesting] = useState(false);

  // 이력 확장
  const [expandedVersion, setExpandedVersion] = useState<number | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    const [detailRes, effRes] = await Promise.allSettled([
      api.prompts.detail(promptId),
      api.prompts.effectiveness(promptId),
    ]);
    if (detailRes.status === "fulfilled") {
      setDetail(detailRes.value);
      const activeV = detailRes.value.versions.find(
        (v) => v.status === "active",
      );
      if (activeV) setEditText(activeV.content_text);
    }
    if (effRes.status === "fulfilled") setEffectiveness(effRes.value);
    setLoading(false);
  }, [promptId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSaveCandidate = async () => {
    if (!editReason.trim()) {
      alert("변경 사유를 입력하세요.");
      return;
    }
    setSaving(true);
    try {
      const result = await api.prompts.createCandidate(
        promptId,
        editText,
        editReason,
      );
      if (result.version) {
        alert(`후보 v${result.version} 등록 완료`);
        setEditReason("");
        fetchData();
      }
    } catch {
      alert("등록 실패");
    }
    setSaving(false);
  };

  const handleSuggest = async () => {
    setSuggesting(true);
    try {
      const result = await api.prompts.suggestImprovement(promptId);
      setSuggestions(result);
    } catch {
      setSuggestions({ error: "개선 제안 요청 실패" });
    }
    setSuggesting(false);
  };

  const handleApplySuggestion = (text: string) => {
    setEditText(text);
    setTab("edit");
  };

  const handleCreateCandidate = async (text: string, title: string) => {
    try {
      const result = await api.prompts.createCandidate(
        promptId,
        text,
        `AI 제안: ${title}`,
      );
      if (result.version) {
        alert(`후보 v${result.version} 등록 완료`);
        fetchData();
      }
    } catch {
      alert("등록 실패");
    }
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/admin/prompts"
              className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
            >
              &larr; 프롬프트 목록
            </Link>
            <h1 className="text-sm font-semibold font-mono">{promptId}</h1>
          </div>
          <Link
            href={`/admin/prompts/${encodeURIComponent(promptId)}/simulate`}
            className="px-3 py-1.5 bg-[#3ecf8e] text-black rounded-lg text-xs font-medium hover:bg-[#35b87d] transition-colors"
          >
            시뮬레이션
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            로딩 중...
          </div>
        )}

        {!loading && detail && (
          <>
            {/* 성과 요약 */}
            {effectiveness && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <MetricCard
                  label="사용 횟수"
                  value={effectiveness.proposals_used}
                />
                <MetricCard
                  label="승률"
                  value={
                    effectiveness.win_rate != null
                      ? `${effectiveness.win_rate}%`
                      : "-"
                  }
                />
                <MetricCard
                  label="평균 품질"
                  value={effectiveness.avg_quality_score?.toFixed(1) ?? "-"}
                />
                <MetricCard
                  label="수정율"
                  value={
                    effectiveness.avg_edit_ratio != null
                      ? `${(effectiveness.avg_edit_ratio * 100).toFixed(1)}%`
                      : "-"
                  }
                />
                <MetricCard
                  label="평균 토큰"
                  value={`${effectiveness.avg_input_tokens ?? 0}/${effectiveness.avg_output_tokens ?? 0}`}
                />
              </div>
            )}

            {/* 탭 */}
            <div className="flex gap-1 bg-[#1c1c1c] rounded-lg p-1 w-fit">
              {[
                {
                  id: "history" as Tab,
                  label: `이력 (${detail.total_versions})`,
                },
                { id: "edit" as Tab, label: "편집" },
                { id: "suggest" as Tab, label: "AI 제안" },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    tab === t.id
                      ? "bg-[#262626] text-[#ededed]"
                      : "text-[#8c8c8c] hover:text-[#ededed]"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* 이력 탭 */}
            {tab === "history" && (
              <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 space-y-3">
                {detail.versions.map((v) => (
                  <div
                    key={v.version}
                    className={`rounded-lg border p-3 ${
                      v.status === "active"
                        ? "border-[#3ecf8e] bg-[#111]"
                        : v.status === "candidate"
                          ? "border-[#f5a623] bg-[#111]"
                          : "border-[#262626] bg-[#0f0f0f]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold">v{v.version}</span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded ${
                            v.status === "active"
                              ? "bg-[#1a3a2a] text-[#3ecf8e]"
                              : v.status === "candidate"
                                ? "bg-[#3a2a1a] text-[#f5a623]"
                                : "bg-[#1a1a1a] text-[#8c8c8c]"
                          }`}
                        >
                          {v.status}
                        </span>
                        <span className="text-xs text-[#8c8c8c]">
                          {v.created_by} &middot;{" "}
                          {new Date(v.created_at).toLocaleDateString("ko")}
                        </span>
                      </div>
                      <button
                        onClick={() =>
                          setExpandedVersion(
                            expandedVersion === v.version ? null : v.version,
                          )
                        }
                        className="text-xs text-[#8c8c8c] hover:text-[#ededed]"
                      >
                        {expandedVersion === v.version ? "접기" : "내용 보기"}
                      </button>
                    </div>
                    {v.change_reason && (
                      <div className="text-xs text-[#8c8c8c] mt-1">
                        {v.change_reason}
                      </div>
                    )}
                    {expandedVersion === v.version && (
                      <pre className="mt-3 p-3 bg-[#0a0a0a] rounded text-xs text-[#8c8c8c] overflow-x-auto max-h-96 whitespace-pre-wrap">
                        {v.content_text}
                      </pre>
                    )}
                  </div>
                ))}
              </section>
            )}

            {/* 편집 탭 — PromptEditor + PreviewPanel 컴포넌트 사용 */}
            {tab === "edit" && (
              <section className="space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                    <PromptEditor value={editText} onChange={setEditText} />
                  </div>
                  <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                    <PreviewPanel promptText={editText} />
                  </div>
                </div>

                {/* 저장 바 */}
                <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-4 flex items-center gap-4">
                  <input
                    type="text"
                    value={editReason}
                    onChange={(e) => setEditReason(e.target.value)}
                    placeholder="변경 사유 (필수)"
                    className="flex-1 bg-[#0a0a0a] rounded-lg px-3 py-2 text-xs border border-[#262626] focus:border-[#3ecf8e] focus:outline-none"
                  />
                  <button
                    onClick={handleSaveCandidate}
                    disabled={saving || !editReason.trim()}
                    className="px-4 py-2 bg-[#3ecf8e] text-black rounded-lg text-xs font-medium hover:bg-[#35b87d] disabled:opacity-50 transition-colors"
                  >
                    {saving ? "저장 중..." : "후보 저장 (candidate)"}
                  </button>
                  <Link
                    href={`/admin/prompts/${encodeURIComponent(promptId)}/simulate`}
                    className="px-4 py-2 bg-[#262626] hover:bg-[#333] rounded-lg text-xs transition-colors"
                  >
                    시뮬레이션
                  </Link>
                </div>
              </section>
            )}

            {/* AI 제안 탭 */}
            {tab === "suggest" && (
              <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold">AI 개선 제안</h2>
                  <button
                    onClick={handleSuggest}
                    disabled={suggesting}
                    className="px-4 py-1.5 bg-[#3ecf8e] text-black rounded-lg text-xs font-medium hover:bg-[#35b87d] disabled:opacity-50 transition-colors"
                  >
                    {suggesting ? "분석 중..." : "개선 제안 요청"}
                  </button>
                </div>

                {suggestions?.error && (
                  <div className="text-xs text-[#ff6b6b]">
                    {suggestions.error}
                  </div>
                )}
                {suggestions?.analysis && (
                  <div className="text-xs text-[#8c8c8c] mb-4">
                    {suggestions.analysis}
                  </div>
                )}

                {suggestions?.suggestions && (
                  <div className="space-y-4">
                    {suggestions.suggestions.map((s, i) => (
                      <div
                        key={i}
                        className="bg-[#111] rounded-lg border border-[#262626] p-4"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-xs font-semibold">{s.title}</h3>
                          <div className="flex gap-2">
                            <button
                              onClick={() =>
                                handleApplySuggestion(s.prompt_text)
                              }
                              className="px-3 py-1 bg-[#262626] hover:bg-[#333] rounded text-xs transition-colors"
                            >
                              편집기 적용
                            </button>
                            <button
                              onClick={() =>
                                handleCreateCandidate(s.prompt_text, s.title)
                              }
                              className="px-3 py-1 bg-[#1a3a2a] hover:bg-[#2a4a3a] text-[#3ecf8e] rounded text-xs transition-colors"
                            >
                              후보 등록
                            </button>
                          </div>
                        </div>
                        <p className="text-xs text-[#8c8c8c] mb-2">
                          {s.rationale}
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {s.key_changes.map((c, j) => (
                            <span
                              key={j}
                              className="text-xs bg-[#1a1a1a] px-2 py-0.5 rounded text-[#8c8c8c]"
                            >
                              {c}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-3">
      <div className="text-[#8c8c8c] text-xs">{label}</div>
      <div className="text-lg font-bold mt-0.5">{value}</div>
    </div>
  );
}
