"use client";

/**
 * StepArtifactViewer — STEP별 산출물 렌더러 + 타임트래블 버튼
 *
 * 완료된 STEP 클릭 시 산출물 패널 표시.
 * artifact key별 렌더링 분기.
 */

import { useCallback, useEffect, useState } from "react";
import { api, WORKFLOW_STEPS } from "@/lib/api";

interface StepArtifactViewerProps {
  proposalId: string;
  stepIndex: number;
  onGoto?: (step: string) => void;
  className?: string;
}

// STEP → artifact key 매핑
const STEP_ARTIFACTS: Record<number, { key: string; label: string }[]> = {
  0: [{ key: "search_results", label: "공고 검색 결과" }],
  1: [
    { key: "rfp_analyze", label: "RFP 분석" },
    { key: "research_gather", label: "리서치 결과" },
    { key: "go_no_go", label: "Go/No-Go 판정" },
  ],
  2: [{ key: "strategy", label: "제안 전략" }],
  3: [
    { key: "plan", label: "실행 계획" },
  ],
  4: [
    { key: "proposal", label: "제안서 섹션" },
    { key: "self_review", label: "자가진단" },
  ],
  5: [
    { key: "presentation_strategy", label: "발표 전략" },
    { key: "ppt_storyboard", label: "PPT 스토리보드" },
  ],
};

export default function StepArtifactViewer({
  proposalId,
  stepIndex,
  onGoto,
  className = "",
}: StepArtifactViewerProps) {
  const [activeArtifact, setActiveArtifact] = useState<string | null>(null);
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [impactInfo, setImpactInfo] = useState<{
    downstream_count: number;
    affected_steps: number[];
    message: string;
  } | null>(null);

  const artifacts = STEP_ARTIFACTS[stepIndex] || [];

  // 산출물 로드
  const loadArtifact = useCallback(
    async (key: string) => {
      if (activeArtifact === key) {
        setActiveArtifact(null);
        setData(null);
        return;
      }
      setActiveArtifact(key);
      setLoading(true);
      try {
        const result = await api.artifacts.get(proposalId, key);
        setData(result.data as Record<string, unknown>);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [proposalId, activeArtifact]
  );

  // 타임트래블 영향 조회
  const handleGotoCheck = useCallback(async () => {
    const stepDef = WORKFLOW_STEPS[stepIndex];
    if (!stepDef) return;
    const firstNode = stepDef.nodes[0];
    try {
      const impact = await api.workflow.impact(proposalId, firstNode);
      setImpactInfo(impact);
    } catch {
      setImpactInfo(null);
    }
  }, [proposalId, stepIndex]);

  const handleGotoConfirm = useCallback(async () => {
    const stepDef = WORKFLOW_STEPS[stepIndex];
    if (!stepDef) return;
    onGoto?.(stepDef.nodes[0]);
    setImpactInfo(null);
  }, [stepIndex, onGoto]);

  if (artifacts.length === 0) return null;

  return (
    <div className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] p-4 ${className}`}>
      {/* 산출물 탭 */}
      <div className="flex items-center gap-1.5 mb-3">
        <span className="text-[10px] text-[#8c8c8c] uppercase tracking-wider mr-2">
          STEP {stepIndex} 산출물
        </span>
        {artifacts.map((a) => (
          <button
            key={a.key}
            onClick={() => loadArtifact(a.key)}
            className={`px-2.5 py-1 text-[10px] font-medium rounded-lg border transition-colors ${
              activeArtifact === a.key
                ? "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/40"
                : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
            }`}
          >
            {a.label}
          </button>
        ))}

        {/* 타임트래블 버튼 */}
        {onGoto && (
          <button
            onClick={handleGotoCheck}
            className="ml-auto px-2.5 py-1 text-[10px] font-medium rounded-lg border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-colors"
          >
            이 단계로 돌아가기
          </button>
        )}
      </div>

      {/* 타임트래블 경고 */}
      {impactInfo && (
        <div className="mb-3 bg-amber-500/5 border border-amber-500/20 rounded-lg px-3 py-2">
          <p className="text-[10px] text-amber-400 font-medium mb-1">
            재실행 영향 범위
          </p>
          <p className="text-[10px] text-[#8c8c8c] mb-2">{impactInfo.message}</p>
          <div className="flex gap-2">
            <button
              onClick={() => setImpactInfo(null)}
              className="px-3 py-1 text-[10px] rounded border border-[#262626] text-[#8c8c8c] hover:bg-[#262626]"
            >
              취소
            </button>
            <button
              onClick={handleGotoConfirm}
              className="px-3 py-1 text-[10px] rounded bg-amber-500/15 border border-amber-500/30 text-amber-400 hover:bg-amber-500/25"
            >
              확인 — 돌아가기
            </button>
          </div>
        </div>
      )}

      {/* 산출물 데이터 */}
      {loading && (
        <div className="flex items-center gap-2 py-6 justify-center">
          <div className="w-4 h-4 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin" />
          <span className="text-xs text-[#5c5c5c]">불러오는 중...</span>
        </div>
      )}

      {!loading && activeArtifact && data && (
        <ArtifactRenderer artifactKey={activeArtifact} data={data} />
      )}

      {!loading && activeArtifact && !data && (
        <p className="text-xs text-[#5c5c5c] py-4 text-center">
          산출물이 아직 생성되지 않았습니다.
        </p>
      )}
    </div>
  );
}

// ── 산출물 렌더러 ──

function ArtifactRenderer({
  artifactKey,
  data,
}: {
  artifactKey: string;
  data: Record<string, unknown>;
}) {
  switch (artifactKey) {
    case "go_no_go":
      return <GoNoGoArtifact data={data} />;
    case "rfp_analyze":
      return <RfpAnalyzeArtifact data={data} />;
    case "strategy":
      return <StrategyArtifact data={data} />;
    case "self_review":
      return <SelfReviewArtifact data={data} />;
    case "plan":
      return <PlanArtifact data={data} />;
    default:
      return <GenericArtifact data={data} />;
  }
}

// ── Go/No-Go ──

function GoNoGoArtifact({ data }: { data: Record<string, unknown> }) {
  const score = data.feasibility_score as number | undefined;
  const positioning = data.positioning as string | undefined;
  const pros = data.pros as string[] | undefined;
  const risks = data.risks as string[] | undefined;
  const fatalFlaw = data.fatal_flaw as string | null;
  const strategicFocus = data.strategic_focus as string | null;
  const recommendation = data.recommendation as string | undefined;

  return (
    <div className="space-y-3">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        {score != null && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#8c8c8c]">수주 가능성</span>
            <span className={`text-sm font-bold ${score >= 70 ? "text-[#3ecf8e]" : score >= 50 ? "text-amber-400" : "text-red-400"}`}>
              {score}%
            </span>
          </div>
        )}
        {positioning && (
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#262626] text-[#8c8c8c]">
            {positioning}
          </span>
        )}
        {recommendation && (
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
            recommendation === "go" ? "bg-[#3ecf8e]/15 text-[#3ecf8e]" : "bg-red-500/15 text-red-400"
          }`}>
            {recommendation.toUpperCase()}
          </span>
        )}
      </div>

      {/* fatal_flaw / strategic_focus */}
      {fatalFlaw && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2">
          <p className="text-[9px] text-red-400 uppercase tracking-wider mb-0.5">치명적 결격 사유</p>
          <p className="text-[10px] text-[#ededed]">{fatalFlaw}</p>
        </div>
      )}
      {strategicFocus && (
        <div className="bg-[#3ecf8e]/5 border border-[#3ecf8e]/20 rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#3ecf8e] uppercase tracking-wider mb-0.5">핵심 승부수</p>
          <p className="text-[10px] text-[#ededed]">{strategicFocus}</p>
        </div>
      )}

      {/* 강점 / 리스크 */}
      <div className="grid grid-cols-2 gap-2">
        {pros && pros.length > 0 && (
          <div>
            <p className="text-[9px] text-[#3ecf8e] uppercase mb-1">강점</p>
            {pros.map((p, i) => (
              <p key={i} className="text-[10px] text-[#8c8c8c]">+ {p}</p>
            ))}
          </div>
        )}
        {risks && risks.length > 0 && (
          <div>
            <p className="text-[9px] text-red-400 uppercase mb-1">리스크</p>
            {risks.map((r, i) => (
              <p key={i} className="text-[10px] text-[#8c8c8c]">- {r}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── RFP 분석 ──

function RfpAnalyzeArtifact({ data }: { data: Record<string, unknown> }) {
  const caseType = data.case_type as string | undefined;
  const hotButtons = data.hot_buttons as string[] | undefined;
  const evalItems = data.eval_items as Array<{ item: string; weight: number }> | undefined;
  const mandatoryReqs = data.mandatory_reqs as string[] | undefined;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-[#8c8c8c]">케이스 유형:</span>
        <span className="text-xs font-bold text-[#ededed]">{caseType || "A"}</span>
      </div>

      {evalItems && evalItems.length > 0 && (
        <div>
          <p className="text-[9px] text-[#8c8c8c] uppercase mb-1">평가항목 ({evalItems.length}개)</p>
          <div className="space-y-1">
            {evalItems.map((e, i) => (
              <div key={i} className="flex items-center justify-between bg-[#111111] rounded px-2.5 py-1.5">
                <span className="text-[10px] text-[#ededed]">{e.item}</span>
                <span className="text-[10px] font-bold text-[#3ecf8e]">{e.weight}점</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {hotButtons && hotButtons.length > 0 && (
        <div>
          <p className="text-[9px] text-amber-400 uppercase mb-1">핫버튼</p>
          <div className="flex flex-wrap gap-1">
            {hotButtons.map((h, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                {h}
              </span>
            ))}
          </div>
        </div>
      )}

      {mandatoryReqs && mandatoryReqs.length > 0 && (
        <div>
          <p className="text-[9px] text-red-400 uppercase mb-1">필수 요건</p>
          {mandatoryReqs.map((r, i) => (
            <p key={i} className="text-[10px] text-[#8c8c8c]">- {r}</p>
          ))}
        </div>
      )}
    </div>
  );
}

// ── 전략 ──

function StrategyArtifact({ data }: { data: Record<string, unknown> }) {
  const winTheme = data.win_theme as string | undefined;
  const ghostTheme = data.ghost_theme as string | undefined;
  const keyMessages = data.key_messages as string[] | undefined;
  const alternatives = data.alternatives as Array<{ alt_id: string; win_theme: string }> | undefined;

  return (
    <div className="space-y-3">
      {winTheme && (
        <div className="bg-[#3ecf8e]/5 border border-[#3ecf8e]/20 rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#3ecf8e] uppercase mb-0.5">Win Theme</p>
          <p className="text-[10px] text-[#ededed]">{winTheme}</p>
        </div>
      )}
      {ghostTheme && (
        <div className="bg-[#111111] border border-[#262626] rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#8c8c8c] uppercase mb-0.5">Ghost Theme</p>
          <p className="text-[10px] text-[#8c8c8c]">{ghostTheme}</p>
        </div>
      )}
      {keyMessages && keyMessages.length > 0 && (
        <div>
          <p className="text-[9px] text-[#8c8c8c] uppercase mb-1">핵심 메시지</p>
          {keyMessages.map((m, i) => (
            <p key={i} className="text-[10px] text-[#ededed]">{i + 1}. {m}</p>
          ))}
        </div>
      )}
      {alternatives && alternatives.length > 1 && (
        <div>
          <p className="text-[9px] text-[#8c8c8c] uppercase mb-1">전략 대안 ({alternatives.length}개)</p>
          {alternatives.map((a) => (
            <div key={a.alt_id} className="bg-[#111111] rounded px-2.5 py-1.5 mb-1">
              <span className="text-[10px] font-bold text-[#ededed]">{a.alt_id}: </span>
              <span className="text-[10px] text-[#8c8c8c]">{a.win_theme}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── 자가진단 ──

function SelfReviewArtifact({ data }: { data: Record<string, unknown> }) {
  const total = data.total as number | undefined;
  const compliance = data.compliance_score as number | undefined;
  const strategy = data.strategy_score as number | undefined;
  const quality = data.quality_score as number | undefined;
  const trust = (data.trustworthiness as Record<string, unknown>)?.trustworthiness_score as number | undefined;
  const personas = data.persona_reviews as Record<string, string> | undefined;

  const axes = [
    { label: "컴플라이언스", score: compliance, max: 25 },
    { label: "전략 일관성", score: strategy, max: 25 },
    { label: "작성 품질", score: quality, max: 25 },
    { label: "근거 신뢰성", score: trust, max: 25 },
  ];

  return (
    <div className="space-y-3">
      {total != null && (
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-[#8c8c8c]">총점</span>
          <span className={`text-lg font-bold ${total >= 80 ? "text-[#3ecf8e]" : total >= 60 ? "text-amber-400" : "text-red-400"}`}>
            {total}/100
          </span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        {axes.map((a) => (
          <div key={a.label} className="bg-[#111111] rounded px-2.5 py-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-[#8c8c8c]">{a.label}</span>
              <span className={`text-[10px] font-bold ${(a.score ?? 0) >= 20 ? "text-[#3ecf8e]" : (a.score ?? 0) >= 15 ? "text-amber-400" : "text-red-400"}`}>
                {a.score ?? 0}/{a.max}
              </span>
            </div>
            <div className="h-1.5 bg-[#262626] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${(a.score ?? 0) >= 20 ? "bg-[#3ecf8e]" : (a.score ?? 0) >= 15 ? "bg-amber-500" : "bg-red-500"}`}
                style={{ width: `${((a.score ?? 0) / a.max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {personas && (
        <div className="space-y-1.5">
          <p className="text-[9px] text-[#8c8c8c] uppercase">3-페르소나 시뮬레이션</p>
          {Object.entries(personas).map(([role, review]) => (
            <div key={role} className="bg-[#111111] rounded px-2.5 py-1.5">
              <span className="text-[10px] font-medium text-[#ededed]">{role}: </span>
              <span className="text-[10px] text-[#8c8c8c]">{review}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── 실행 계획 ──

function PlanArtifact({ data }: { data: Record<string, unknown> }) {
  const team = data.team as Array<{ role: string; grade: string; mm: number }> | undefined;
  const storylines = data.storylines as Record<string, unknown> | undefined;
  const bidPrice = data.bid_price as Record<string, unknown> | undefined;
  const qualityCheck = (storylines as any)?.quality_check as Record<string, unknown> | undefined;

  return (
    <div className="space-y-3">
      {team && team.length > 0 && (
        <div>
          <p className="text-[9px] text-[#8c8c8c] uppercase mb-1">팀 구성 ({team.length}명)</p>
          <div className="space-y-1">
            {team.map((t, i) => (
              <div key={i} className="flex items-center justify-between bg-[#111111] rounded px-2.5 py-1.5">
                <span className="text-[10px] text-[#ededed]">{t.role}</span>
                <span className="text-[10px] text-[#8c8c8c]">{t.grade} / {t.mm} M/M</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {storylines && (storylines as any).overall_narrative && (
        <div className="bg-[#3ecf8e]/5 border border-[#3ecf8e]/20 rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#3ecf8e] uppercase mb-0.5">전체 스토리</p>
          <p className="text-[10px] text-[#ededed]">{(storylines as any).overall_narrative}</p>
        </div>
      )}

      {qualityCheck && (
        <div className="bg-[#111111] border border-[#262626] rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#8c8c8c] uppercase mb-1">품질 검증</p>
          {(qualityCheck as any).eval_coverage?.missing?.length > 0 && (
            <p className="text-[10px] text-red-400">누락 평가항목: {(qualityCheck as any).eval_coverage.missing.join(", ")}</p>
          )}
          {(qualityCheck as any).win_theme_coverage && (
            <p className="text-[10px] text-[#8c8c8c]">
              Win Theme 커버: {(qualityCheck as any).win_theme_coverage.sections_with_win_theme}/{(qualityCheck as any).win_theme_coverage.total_sections} 섹션
            </p>
          )}
        </div>
      )}

      {bidPrice && (bidPrice as any).total_cost && (
        <div className="bg-[#111111] rounded px-2.5 py-1.5">
          <span className="text-[10px] text-[#8c8c8c]">총 예산: </span>
          <span className="text-[10px] font-bold text-[#ededed]">
            {Number((bidPrice as any).total_cost).toLocaleString()}원
          </span>
        </div>
      )}
    </div>
  );
}

// ── 범용 렌더러 (JSON 표시) ──

/** JSON 구문 강조 (키: 녹색, 문자열: 주황, 숫자/boolean: 파랑) */
function highlightJson(json: string): React.ReactNode {
  const parts = json.split(/("(?:[^"\\]|\\.)*")/g);
  let nextIsKey = false;
  return parts.map((part, i) => {
    if (part.startsWith('"') && part.endsWith('"')) {
      // 다음 비공백 문자가 : 이면 키
      const rest = parts.slice(i + 1).join("");
      const isKey = /^\s*:/.test(rest);
      if (isKey) {
        nextIsKey = true;
        return <span key={i} className="text-[#3ecf8e]">{part}</span>;
      }
      return <span key={i} className="text-amber-400">{part}</span>;
    }
    // 숫자, true, false, null
    return <span key={i} className="text-[#8c8c8c]">{
      part.replace(/\b(true|false|null|\d+\.?\d*)\b/g, (match) =>
        match === "true" || match === "false" || match === "null" ? match : match
      )
    }</span>;
  });
}

function GenericArtifact({ data }: { data: Record<string, unknown> }) {
  const [expanded, setExpanded] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const json = JSON.stringify(data, null, 2);
  const preview = json.slice(0, 500);

  return (
    <div>
      <pre className="text-[10px] whitespace-pre-wrap break-words leading-relaxed font-mono bg-[#111111] rounded-lg p-3 max-h-[300px] overflow-auto">
        {highlightJson(expanded ? json : preview)}
        {!expanded && json.length > 500 && <span className="text-[#5c5c5c]">...</span>}
      </pre>
      {json.length > 500 && (
        <div className="flex gap-3 mt-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-[10px] text-[#3ecf8e] hover:underline"
          >
            {expanded ? "접기" : "펼치기"}
          </button>
          <button
            onClick={() => setFullscreen(true)}
            className="text-[10px] text-[#8c8c8c] hover:text-[#ededed]"
          >
            전체 화면
          </button>
        </div>
      )}

      {/* 전체화면 모달 */}
      {fullscreen && (
        <div
          className="fixed inset-0 bg-[#0f0f0f]/90 flex items-center justify-center p-8"
          style={{ zIndex: "var(--z-modal, 60)" }}
          onClick={() => setFullscreen(false)}
        >
          <div
            className="bg-[#1c1c1c] border border-[#262626] rounded-xl w-full max-w-4xl max-h-[85vh] overflow-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-[#ededed]">산출물 전체 보기</h3>
              <button
                onClick={() => setFullscreen(false)}
                className="text-[#8c8c8c] hover:text-[#ededed] transition-colors"
                aria-label="닫기"
              >
                ✕
              </button>
            </div>
            <pre className="text-xs text-[#8c8c8c] whitespace-pre-wrap break-words font-mono leading-relaxed">
              {json}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
