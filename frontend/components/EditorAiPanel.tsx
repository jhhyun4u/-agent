"use client";

/**
 * EditorAiPanel — 우측 AI 어시스턴트 패널 (§13-10)
 *
 * - 요건 충족률 게이지
 * - Win Strategy 반영도 체크리스트
 * - AI 질문 입력 (aiAssist / regenerateSection)
 * - KB 출처 참조
 * - 변경 이력
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { api, type ComplianceItem } from "@/lib/api";
import AiSuggestionDiff from "@/components/AiSuggestionDiff";

// ── 타입 ──

export interface StrategyCheck {
  label: string;
  met: boolean;
}

export interface KbReference {
  id: string;
  label: string;
}

export interface ChangeEntry {
  time: string;
  description: string;
}

const AI_MODES = [
  { value: "improve", label: "개선" },
  { value: "shorten", label: "축약" },
  { value: "expand", label: "확장" },
  { value: "formalize", label: "공식화" },
] as const;

type AiMode = (typeof AI_MODES)[number]["value"];

interface EditorAiPanelProps {
  proposalId: string;
  complianceItems: ComplianceItem[];
  strategyChecks: StrategyCheck[];
  kbReferences: KbReference[];
  changes: ChangeEntry[];
  activeSectionId?: string | null;
  currentContent?: string;
  onApplySuggestion?: (html: string) => void;
  className?: string;
}

export default function EditorAiPanel({
  proposalId,
  complianceItems,
  strategyChecks,
  kbReferences,
  changes,
  activeSectionId,
  currentContent,
  onApplySuggestion,
  className = "",
}: EditorAiPanelProps) {
  // 충족률 계산
  const total = complianceItems.length;
  const met = complianceItems.filter(
    (i) => i.status === "met" || i.status === "partial"
  ).length;
  const rate = total > 0 ? Math.round((met / total) * 100) : 0;

  // AI 질문 상태
  const [aiQuery, setAiQuery] = useState("");
  const [aiMode, setAiMode] = useState<AiMode>("improve");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<{
    suggestion: string;
    explanation: string;
  } | null>(null);
  const [aiError, setAiError] = useState("");

  // 섹션 재생성 상태
  const [regenLoading, setRegenLoading] = useState(false);
  const [regenResult, setRegenResult] = useState("");

  // AI 응답 대기 경과 시간
  const [aiElapsed, setAiElapsed] = useState(0);
  const aiTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 타이머 정리
  useEffect(() => {
    return () => { if (aiTimerRef.current) clearInterval(aiTimerRef.current); };
  }, []);

  const handleAiAssist = useCallback(async () => {
    if (!aiQuery.trim()) return;
    setAiLoading(true);
    setAiError("");
    setAiResult(null);
    setAiElapsed(0);
    aiTimerRef.current = setInterval(() => setAiElapsed(prev => prev + 1), 1000);
    try {
      const result = await api.artifacts.aiAssist(
        proposalId,
        aiQuery,
        aiMode,
        activeSectionId ?? ""
      );
      setAiResult({ suggestion: result.suggestion, explanation: result.explanation });
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "AI 요청 실패");
    } finally {
      if (aiTimerRef.current) { clearInterval(aiTimerRef.current); aiTimerRef.current = null; }
      setAiLoading(false);
    }
  }, [proposalId, aiQuery, aiMode, activeSectionId]);

  const handleRegenerate = useCallback(async () => {
    if (!activeSectionId) return;
    setRegenLoading(true);
    setRegenResult("");
    setAiElapsed(0);
    aiTimerRef.current = setInterval(() => setAiElapsed(prev => prev + 1), 1000);
    try {
      const result = await api.artifacts.regenerateSection(
        proposalId,
        "proposal",
        activeSectionId,
        aiQuery || ""
      );
      setRegenResult(`${result.section_title} 재생성 완료`);
    } catch (e) {
      setRegenResult(e instanceof Error ? e.message : "재생성 실패");
    } finally {
      if (aiTimerRef.current) { clearInterval(aiTimerRef.current); aiTimerRef.current = null; }
      setRegenLoading(false);
    }
  }, [proposalId, activeSectionId, aiQuery]);

  return (
    <div className={`flex flex-col h-full overflow-hidden ${className}`}>
      <div className="flex-1 overflow-y-auto space-y-4">
        {/* 요건 충족률 게이지 */}
        <section>
          <h3 className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium px-3 py-2">
            요건 충족률
          </h3>
          <div className="px-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-lg font-bold text-[#ededed]">{rate}%</span>
              <span className="text-[10px] text-[#8c8c8c]">
                {met}/{total} 충족
              </span>
            </div>
            <div className="h-2 bg-[#262626] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  rate >= 80
                    ? "bg-[#3ecf8e]"
                    : rate >= 60
                    ? "bg-amber-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${rate}%` }}
              />
            </div>
          </div>
        </section>

        {/* Win Strategy 반영도 */}
        {strategyChecks.length > 0 && (
          <section>
            <h3 className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium px-3 py-2">
              Win Strategy 반영
            </h3>
            <div className="space-y-1 px-3">
              {strategyChecks.map((check) => (
                <div
                  key={check.label}
                  className="flex items-center gap-2 text-xs"
                >
                  <span>{check.met ? "✅" : "⚠️"}</span>
                  <span
                    className={
                      check.met ? "text-[#8c8c8c]" : "text-amber-400"
                    }
                  >
                    {check.label}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* KB 출처 참조 */}
        {kbReferences.length > 0 && (
          <section>
            <h3 className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium px-3 py-2">
              출처 참조
            </h3>
            <div className="space-y-1 px-3">
              {kbReferences.map((ref) => (
                <div
                  key={ref.id}
                  className="flex items-center gap-1.5 text-[10px]"
                >
                  <span className="text-[#5c5c5c]">•</span>
                  <span className="text-[#3ecf8e]">{ref.id}</span>
                  <span className="text-[#8c8c8c] truncate">{ref.label}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 변경 이력 */}
        {changes.length > 0 && (
          <section>
            <h3 className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium px-3 py-2">
              변경 이력
            </h3>
            <div className="space-y-1 px-3">
              {changes.slice(0, 10).map((entry, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 text-[10px]"
                >
                  <span className="text-[#5c5c5c] shrink-0">{entry.time}</span>
                  <span className="text-[#8c8c8c]">{entry.description}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      {/* AI 질문 입력 (하단 고정) */}
      <div className="border-t border-[#262626] px-3 py-3 space-y-2 shrink-0">
        <h3 className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium">
          AI에게 질문하기
        </h3>

        {/* 모드 선택 */}
        <div className="flex gap-1">
          {AI_MODES.map((mode) => (
            <button
              key={mode.value}
              onClick={() => setAiMode(mode.value)}
              className={`px-2 py-0.5 text-[9px] font-medium rounded transition-colors ${
                aiMode === mode.value
                  ? "bg-[#3ecf8e]/15 text-[#3ecf8e]"
                  : "text-[#5c5c5c] hover:text-[#8c8c8c]"
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {/* 입력 + 전송 */}
        <div className="flex gap-1.5">
          <textarea
            value={aiQuery}
            onChange={(e) => setAiQuery(e.target.value)}
            placeholder="텍스트 또는 지시사항 입력..."
            rows={2}
            className="flex-1 bg-[#111111] border border-[#262626] rounded-lg px-2.5 py-1.5 text-[10px] text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40 resize-none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                handleAiAssist();
              }
            }}
          />
        </div>

        <div className="flex gap-1.5">
          <button
            onClick={handleAiAssist}
            disabled={aiLoading || !aiQuery.trim()}
            className="flex-1 py-1.5 text-[10px] font-semibold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 disabled:opacity-40 transition-colors"
          >
            {aiLoading ? `분석 중 (${aiElapsed}s)` : "AI 제안"}
          </button>
          {activeSectionId && (
            <button
              onClick={handleRegenerate}
              disabled={regenLoading}
              className="py-1.5 px-2.5 text-[10px] font-medium rounded-lg border border-[#262626] text-[#8c8c8c] hover:bg-[#262626] disabled:opacity-40 transition-colors"
            >
              {regenLoading ? "..." : "섹션 재생성"}
            </button>
          )}
        </div>

        {/* AI 대기 표시 */}
        {(aiLoading || regenLoading) && (
          <div className="flex items-center gap-2 py-1">
            <div className="w-3 h-3 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin shrink-0" />
            <span className="text-[10px] text-[#8c8c8c]">
              AI 분석 중... {aiElapsed}초 <span className="text-[#5c5c5c]">(보통 5~15초)</span>
            </span>
          </div>
        )}

        {/* AI 결과 — 인라인 diff */}
        {aiResult && currentContent && onApplySuggestion ? (
          <AiSuggestionDiff
            original={currentContent}
            suggestion={aiResult.suggestion}
            explanation={aiResult.explanation}
            onAccept={() => onApplySuggestion(aiResult.suggestion)}
            onReject={() => setAiResult(null)}
          />
        ) : aiResult ? (
          <div className="bg-[#111111] border border-[#3ecf8e]/20 rounded-lg px-2.5 py-2 space-y-1.5">
            <p className="text-[10px] text-[#8c8c8c]">{aiResult.explanation}</p>
            <div className="text-[10px] text-[#ededed] leading-relaxed max-h-24 overflow-y-auto whitespace-pre-wrap">
              {aiResult.suggestion}
            </div>
          </div>
        ) : null}
        {aiError && (
          <p className="text-[10px] text-red-400">{aiError}</p>
        )}
        {regenResult && (
          <p className="text-[10px] text-[#3ecf8e]">{regenResult}</p>
        )}
      </div>
    </div>
  );
}
