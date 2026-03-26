"use client";

/**
 * ArtifactReviewPanel — Claude Desktop 스타일 산출물 뷰어
 *
 * 워크플로 노드 완료 시 결과물 파일을 오른쪽 창에서 읽을 수 있도록 표시.
 * 순수 읽기 전용 — 승인/재작업 등 액션은 중앙 WorkflowPanel에서 처리.
 */

import { useEffect, useState } from "react";
import { api, type WorkflowState } from "@/lib/api";

// ── 노드 → 아티팩트 매핑 ──

interface ArtifactConfig {
  title: string;
  artifactKey: string;
  icon: string;
  step: number;
}

const ARTIFACT_MAP: Record<string, ArtifactConfig> = {
  review_search:   { title: "공고 검색 결과",  artifactKey: "search_results",     icon: "S", step: 1 },
  review_rfp:      { title: "RFP 분석 결과",   artifactKey: "rfp_analyze",        icon: "R", step: 1 },
  review_gng:      { title: "Go/No-Go 판정",   artifactKey: "go_no_go",           icon: "G", step: 1 },
  review_strategy: { title: "제안전략",         artifactKey: "strategy",           icon: "W", step: 2 },
  review_bid_plan: { title: "입찰가격 계획",    artifactKey: "bid_plan",           icon: "$", step: 2 },
  review_plan:     { title: "제안계획서",       artifactKey: "plan",               icon: "P", step: 3 },
  review_section:  { title: "제안서 섹션",      artifactKey: "proposal",           icon: "D", step: 4 },
  review_proposal: { title: "제안서 최종본",    artifactKey: "proposal",           icon: "D", step: 4 },
  review_ppt:      { title: "PPT 발표자료",     artifactKey: "ppt_storyboard",     icon: "T", step: 5 },
  // v4.0: 분기 워크플로 신규 리뷰 게이트
  review_submission_plan: { title: "제출서류 계획",  artifactKey: "submission_plan",    icon: "F", step: 3 },
  review_cost_sheet:      { title: "산출내역서",     artifactKey: "cost_sheet",         icon: "C", step: 5 },
  review_submission:      { title: "제출서류 확인",  artifactKey: "submission_checklist", icon: "V", step: 6 },
  review_mock_eval:       { title: "모의 평가",      artifactKey: "mock_evaluation",    icon: "E", step: 6 },
  review_eval_result:     { title: "평가결과",       artifactKey: "eval_result",        icon: "7", step: 7 },
};

const ICON_COLORS: Record<string, { bg: string; text: string }> = {
  S: { bg: "bg-blue-500/15",    text: "text-blue-400" },
  R: { bg: "bg-purple-500/15",  text: "text-purple-400" },
  G: { bg: "bg-emerald-500/15", text: "text-emerald-400" },
  W: { bg: "bg-amber-500/15",   text: "text-amber-400" },
  $: { bg: "bg-amber-500/15",   text: "text-amber-400" },
  P: { bg: "bg-cyan-500/15",    text: "text-cyan-400" },
  D: { bg: "bg-blue-500/15",    text: "text-blue-400" },
  T: { bg: "bg-indigo-500/15",  text: "text-indigo-400" },
  F: { bg: "bg-pink-500/15",    text: "text-pink-400" },
  C: { bg: "bg-green-500/15",   text: "text-green-400" },
  V: { bg: "bg-teal-500/15",    text: "text-teal-400" },
  E: { bg: "bg-violet-500/15",  text: "text-violet-400" },
  "7": { bg: "bg-rose-500/15",  text: "text-rose-400" },
};

// ── Props ──

interface ArtifactReviewPanelProps {
  proposalId: string;
  reviewNode: string;
  workflowState: WorkflowState;
}

export default function ArtifactReviewPanel({
  proposalId,
  reviewNode,
  workflowState,
}: ArtifactReviewPanelProps) {
  const config = ARTIFACT_MAP[reviewNode];
  const [artifactData, setArtifactData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!config) return;
    setLoading(true);
    api.artifacts
      .get(proposalId, config.artifactKey)
      .then((res) => setArtifactData(res.data as Record<string, unknown>))
      .catch(() => setArtifactData(null))
      .finally(() => setLoading(false));
  }, [proposalId, config]);

  if (!config) return null;

  const iconColor = ICON_COLORS[config.icon] ?? { bg: "bg-[#262626]", text: "text-[#8c8c8c]" };

  // 섹션 리뷰 진행률
  const sectionProgress =
    reviewNode === "review_section" &&
    workflowState.current_section_index != null &&
    workflowState.total_sections != null
      ? { current: workflowState.current_section_index + 1, total: workflowState.total_sections }
      : null;

  return (
    <div className="flex flex-col h-full bg-[#111111]">
      {/* ═══ 헤더 ═══ */}
      <div className="shrink-0 border-b border-[#262626]">
        <div className="px-4 py-3 flex items-center gap-3">
          <span
            className={`w-8 h-8 rounded-lg ${iconColor.bg} ${iconColor.text} flex items-center justify-center text-sm font-bold shrink-0`}
          >
            {config.icon}
          </span>
          <div className="flex-1 min-w-0">
            <h2 className="text-sm font-semibold text-[#ededed] truncate">
              {config.title}
            </h2>
            <p className="text-[10px] text-[#8c8c8c]">
              STEP {config.step}
              {sectionProgress && (
                <span className="ml-2 text-[#5c5c5c]">
                  {sectionProgress.current}/{sectionProgress.total} 섹션
                </span>
              )}
            </p>
          </div>
        </div>

        {sectionProgress && (
          <div className="px-4 pb-2">
            <div className="h-1 bg-[#262626] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#3ecf8e]/60 rounded-full transition-all duration-300"
                style={{ width: `${(sectionProgress.current / sectionProgress.total) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* ═══ 콘텐츠 ═══ */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="relative w-10 h-10">
              <div className="absolute inset-0 rounded-full border-2 border-[#262626]" />
              <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#3ecf8e] animate-spin" />
            </div>
            <span className="text-xs text-[#5c5c5c]">불러오는 중...</span>
          </div>
        ) : !artifactData ? (
          <div className="flex flex-col items-center justify-center py-16 gap-2">
            <span className="text-[#363636] text-lg">---</span>
            <span className="text-xs text-[#5c5c5c]">산출물이 아직 생성되지 않았습니다</span>
          </div>
        ) : (
          <div className="p-4">
            <ArtifactContent artifactKey={config.artifactKey} data={artifactData} proposalId={proposalId} />
          </div>
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// 콘텐츠 렌더러
// ══════════════════════════════════════════════════════════

function ArtifactContent({ artifactKey, data, proposalId }: { artifactKey: string; data: Record<string, unknown>; proposalId?: string }) {
  switch (artifactKey) {
    case "go_no_go":        return <GoNoGoContent data={data} />;
    case "rfp_analyze":     return <RfpAnalyzeContent data={data} />;
    case "search_results":  return <SearchResultsContent data={data} />;
    case "strategy":        return <StrategyContent data={data} />;
    case "bid_plan":        return <BidPlanContent data={data} />;
    case "plan":            return <PlanContent data={data} />;
    case "proposal":        return <ProposalContent data={data} proposalId={proposalId} />;
    case "self_review":     return <SelfReviewContent data={data} />;
    case "ppt_storyboard":  return <PptStoryboardContent data={data} />;
    default:                return <GenericContent data={data} />;
  }
}

// ── 공통 UI 블록 ──

function Section({ title, children, variant = "default" }: {
  title: string;
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger";
}) {
  const border = { default: "border-[#262626]", success: "border-[#3ecf8e]/20", warning: "border-amber-500/20", danger: "border-red-500/20" };
  const titleColor = { default: "text-[#8c8c8c]", success: "text-[#3ecf8e]", warning: "text-amber-400", danger: "text-red-400" };
  return (
    <div className={`border ${border[variant]} rounded-xl p-3.5 mb-3`}>
      <p className={`text-[10px] font-semibold uppercase tracking-wider mb-2 ${titleColor[variant]}`}>{title}</p>
      {children}
    </div>
  );
}

function KV({ label, value, cls }: { label: string; value: React.ReactNode; cls?: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-[11px] text-[#8c8c8c]">{label}</span>
      <span className={`text-[11px] font-medium ${cls ?? "text-[#ededed]"}`}>{value}</span>
    </div>
  );
}

function Tag({ children, color = "default" }: { children: React.ReactNode; color?: "default" | "green" | "amber" | "red" | "blue" }) {
  const m = { default: "bg-[#262626] text-[#8c8c8c]", green: "bg-[#3ecf8e]/10 text-[#3ecf8e]", amber: "bg-amber-500/10 text-amber-400", red: "bg-red-500/10 text-red-400", blue: "bg-blue-500/10 text-blue-400" };
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium ${m[color]}`}>{children}</span>;
}

function Bullets({ items, color = "text-[#8c8c8c]" }: { items: string[]; color?: string }) {
  return (
    <ul className="space-y-1">
      {items.map((t, i) => (
        <li key={i} className={`text-[11px] ${color} flex gap-2`}>
          <span className="shrink-0 mt-0.5">&#8226;</span><span>{t}</span>
        </li>
      ))}
    </ul>
  );
}

// ── Go/No-Go ──

function GoNoGoContent({ data }: { data: Record<string, unknown> }) {
  const score = data.feasibility_score as number | undefined;
  const positioning = data.positioning as string | undefined;
  const recommendation = data.recommendation as string | undefined;
  const fatalFlaw = data.fatal_flaw as string | null;
  const strategicFocus = data.strategic_focus as string | null;
  const pros = data.pros as string[] | undefined;
  const risks = data.risks as string[] | undefined;
  const scoreTag = data.score_tag as string | undefined;
  const breakdown = data.score_breakdown as Record<string, number> | undefined;
  const sc = (score ?? 0) >= 85 ? "text-[#3ecf8e]" : (score ?? 0) >= 70 ? "text-amber-400" : "text-red-400";

  // v4.0 4축 바 차트
  const axes = breakdown ? [
    { label: "유사실적", score: breakdown.similar_performance ?? 0, max: 30 },
    { label: "자격적격", score: breakdown.qualification ?? 0, max: 30 },
    { label: "경쟁강도", score: breakdown.competition ?? 0, max: 20 },
    { label: "전략가산", score: breakdown.strategic ?? 0, max: 20 },
  ] : [];

  const tagLabels: Record<string, string> = {
    priority: "적극 참여",
    standard: "일반 참여",
    below_threshold: "기준 미달",
    disqualified: "자격 미달",
  };

  return (
    <div>
      <div className="flex items-center gap-4 mb-4 pb-4 border-b border-[#262626]">
        {score != null && (
          <div className="text-center">
            <p className={`text-3xl font-bold ${sc}`}>{score}</p>
            <p className="text-[10px] text-[#8c8c8c] mt-0.5">합산 점수</p>
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          {positioning && <Tag color="blue">{positioning}</Tag>}
          {recommendation && <Tag color={recommendation === "go" ? "green" : "red"}>{recommendation.toUpperCase()}</Tag>}
          {scoreTag && tagLabels[scoreTag] && (
            <Tag color={scoreTag === "priority" ? "green" : scoreTag === "standard" ? "amber" : "red"}>
              {tagLabels[scoreTag]}
            </Tag>
          )}
        </div>
      </div>
      {/* 4축 바 차트 */}
      {axes.length > 0 && (
        <div className="mb-4 space-y-1.5">
          {axes.map((a) => {
            const pct = a.max > 0 ? (a.score / a.max) * 100 : 0;
            const color = pct >= 70 ? "bg-[#3ecf8e]" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
            return (
              <div key={a.label} className="flex items-center gap-2">
                <span className="text-[10px] text-[#8c8c8c] w-14 shrink-0">{a.label}</span>
                <div className="flex-1 h-1.5 bg-[#0f0f0f] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="text-[10px] text-[#8c8c8c] w-10 text-right">{a.score}/{a.max}</span>
              </div>
            );
          })}
        </div>
      )}
      {fatalFlaw && <Section title="치명적 결격 사유" variant="danger"><p className="text-xs text-[#ededed] leading-relaxed">{fatalFlaw}</p></Section>}
      {strategicFocus && <Section title="핵심 승부수" variant="success"><p className="text-xs text-[#ededed] leading-relaxed">{strategicFocus}</p></Section>}
      {pros && pros.length > 0 && <Section title="강점"><Bullets items={pros} color="text-[#3ecf8e]" /></Section>}
      {risks && risks.length > 0 && <Section title="리스크" variant="warning"><Bullets items={risks} color="text-amber-400" /></Section>}
    </div>
  );
}

// ── RFP 분석 ──

function RfpAnalyzeContent({ data }: { data: Record<string, unknown> }) {
  const caseType = data.case_type as string | undefined;
  const hotButtons = data.hot_buttons as string[] | undefined;
  const evalItems = data.eval_items as Array<{ item: string; weight: number }> | undefined;
  const mandatoryReqs = data.mandatory_reqs as string[] | undefined;
  const scope = data.scope_summary as string | undefined;

  return (
    <div>
      <div className="mb-4 pb-3 border-b border-[#262626]">
        <KV label="케이스 유형" value={caseType || "A"} />
      </div>
      {scope && <Section title="프로젝트 범위"><p className="text-xs text-[#ededed] leading-relaxed">{scope}</p></Section>}
      {evalItems && evalItems.length > 0 && (
        <Section title={`평가항목 (${evalItems.length}개)`}>
          <div className="space-y-1.5">
            {evalItems.map((e, i) => (
              <div key={i} className="flex items-center justify-between bg-[#0f0f0f] rounded-lg px-3 py-2">
                <span className="text-[11px] text-[#ededed]">{e.item}</span>
                <span className="text-[11px] font-bold text-[#3ecf8e]">{e.weight}점</span>
              </div>
            ))}
          </div>
        </Section>
      )}
      {hotButtons && hotButtons.length > 0 && (
        <Section title="핫버튼" variant="warning">
          <div className="flex flex-wrap gap-1.5">{hotButtons.map((h, i) => <Tag key={i} color="amber">{h}</Tag>)}</div>
        </Section>
      )}
      {mandatoryReqs && mandatoryReqs.length > 0 && <Section title="필수 요건" variant="danger"><Bullets items={mandatoryReqs} color="text-red-400" /></Section>}
    </div>
  );
}

// ── 전략 ──

function StrategyContent({ data }: { data: Record<string, unknown> }) {
  const winTheme = data.win_theme as string | undefined;
  const ghostTheme = data.ghost_theme as string | undefined;
  const keyMessages = data.key_messages as string[] | undefined;
  const swot = data.swot as Record<string, string[]> | undefined;
  const alternatives = data.alternatives as Array<{ alt_id: string; win_theme: string }> | undefined;

  return (
    <div>
      {winTheme && (
        <Section title="Win Theme" variant="success">
          <p className="text-sm font-medium text-[#ededed] leading-relaxed">{winTheme}</p>
        </Section>
      )}
      {ghostTheme && <Section title="Ghost Theme"><p className="text-xs text-[#8c8c8c] leading-relaxed">{ghostTheme}</p></Section>}
      {keyMessages && keyMessages.length > 0 && (
        <Section title="핵심 메시지">
          <ol className="space-y-1.5">
            {keyMessages.map((m, i) => (
              <li key={i} className="flex gap-2 text-[11px]">
                <span className="shrink-0 w-5 h-5 rounded-full bg-[#3ecf8e]/10 text-[#3ecf8e] flex items-center justify-center text-[10px] font-bold">{i + 1}</span>
                <span className="text-[#ededed] leading-relaxed pt-0.5">{m}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}
      {swot && (
        <Section title="SWOT 분석">
          <div className="grid grid-cols-2 gap-2">
            {(["strengths", "weaknesses", "opportunities", "threats"] as const).map((key) => {
              const items = swot[key];
              if (!items || items.length === 0) return null;
              const cfg: Record<string, { l: string; c: string }> = { strengths: { l: "S", c: "text-[#3ecf8e]" }, weaknesses: { l: "W", c: "text-red-400" }, opportunities: { l: "O", c: "text-blue-400" }, threats: { l: "T", c: "text-amber-400" } };
              const { l, c } = cfg[key];
              return (
                <div key={key} className="bg-[#0f0f0f] rounded-lg p-2.5">
                  <p className={`text-[10px] font-bold ${c} mb-1`}>{l}</p>
                  {items.map((it, i) => <p key={i} className="text-[10px] text-[#8c8c8c] leading-relaxed">{it}</p>)}
                </div>
              );
            })}
          </div>
        </Section>
      )}
      {alternatives && alternatives.length > 1 && (
        <Section title={`전략 대안 (${alternatives.length}개)`}>
          {alternatives.map((a) => (
            <div key={a.alt_id} className="bg-[#0f0f0f] rounded-lg px-3 py-2 mb-1.5">
              <span className="text-[10px] font-bold text-[#3ecf8e]">{a.alt_id}: </span>
              <span className="text-[11px] text-[#ededed]">{a.win_theme}</span>
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}

// ── 실행 계획 ──

function PlanContent({ data }: { data: Record<string, unknown> }) {
  const team = data.team as Array<{ role: string; grade: string; mm: number }> | undefined;
  const storylines = data.storylines as Record<string, unknown> | undefined;
  const bidPrice = data.bid_price as Record<string, unknown> | undefined;

  return (
    <div>
      {team && team.length > 0 && (
        <Section title={`팀 구성 (${team.length}명)`}>
          <div className="space-y-1">
            {team.map((t, i) => (
              <div key={i} className="flex items-center justify-between bg-[#0f0f0f] rounded-lg px-3 py-2">
                <span className="text-[11px] text-[#ededed] font-medium">{t.role}</span>
                <span className="text-[11px] text-[#8c8c8c]">{t.grade} · {t.mm} M/M</span>
              </div>
            ))}
          </div>
        </Section>
      )}
      {storylines && (storylines as any).overall_narrative && (
        <Section title="전체 스토리라인" variant="success">
          <p className="text-xs text-[#ededed] leading-relaxed">{(storylines as any).overall_narrative}</p>
        </Section>
      )}
      {storylines && (storylines as any).sections && (
        <Section title="섹션별 스토리">
          <div className="space-y-2">
            {((storylines as any).sections as Array<{ title: string; key_message: string }> || []).map((sec, i) => (
              <div key={i} className="bg-[#0f0f0f] rounded-lg px-3 py-2.5">
                <p className="text-[11px] font-medium text-[#ededed] mb-0.5">{sec.title}</p>
                <p className="text-[10px] text-[#8c8c8c] leading-relaxed">{sec.key_message}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
      {bidPrice && (bidPrice as any).total_cost && (
        <Section title="예산 요약">
          <KV label="총 예산" value={`${Number((bidPrice as any).total_cost).toLocaleString()}원`} cls="text-[#3ecf8e] font-bold" />
        </Section>
      )}
    </div>
  );
}

// ── 공고 검색 결과 (GAP-04) ──

function SearchResultsContent({ data }: { data: Record<string, unknown> }) {
  const results = data.results as Array<{ bid_no: string; title: string; org: string; deadline?: string; budget?: number }> | undefined;
  const total = data.total_count as number | undefined;

  return (
    <div>
      {total != null && <div className="mb-3 pb-3 border-b border-[#262626]"><KV label="검색 건수" value={`${total}건`} /></div>}
      {results && results.length > 0 ? (
        <div className="space-y-2">
          {results.map((r, i) => (
            <div key={i} className="border border-[#262626] rounded-xl px-3.5 py-2.5">
              <p className="text-xs font-medium text-[#ededed] mb-1">{r.title}</p>
              <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                <span className="text-[10px] text-[#8c8c8c]">{r.bid_no}</span>
                <span className="text-[10px] text-[#8c8c8c]">{r.org}</span>
                {r.deadline && <span className="text-[10px] text-amber-400">{r.deadline}</span>}
                {r.budget && <span className="text-[10px] text-[#3ecf8e]">{r.budget.toLocaleString()}원</span>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <GenericContent data={data} />
      )}
    </div>
  );
}

// ── 입찰가격 계획 (GAP-05) ──

function BidPlanContent({ data }: { data: Record<string, unknown> }) {
  const targetPrice = data.target_price as number | undefined;
  const strategy = data.pricing_strategy as string | undefined;
  const costBasis = data.cost_basis as Record<string, unknown> | undefined;
  const laborCost = data.labor_cost as number | undefined;
  const directCost = data.direct_cost as number | undefined;
  const overhead = data.overhead as number | undefined;
  const profit = data.profit as number | undefined;

  return (
    <div>
      {targetPrice && (
        <div className="text-center mb-4 pb-4 border-b border-[#262626]">
          <p className="text-3xl font-bold text-[#3ecf8e]">{targetPrice.toLocaleString()}원</p>
          <p className="text-[10px] text-[#8c8c8c] mt-1">목표 투찰가</p>
        </div>
      )}
      {strategy && <Section title="가격 전략"><p className="text-xs text-[#ededed] leading-relaxed">{strategy}</p></Section>}
      <Section title="비용 구성">
        {laborCost && <KV label="인건비" value={`${laborCost.toLocaleString()}원`} />}
        {directCost && <KV label="직접경비" value={`${directCost.toLocaleString()}원`} />}
        {overhead && <KV label="간접경비" value={`${overhead.toLocaleString()}원`} />}
        {profit && <KV label="이윤" value={`${profit.toLocaleString()}원`} />}
      </Section>
      {costBasis && <GenericContent data={costBasis as Record<string, unknown>} />}
    </div>
  );
}

// ── 제안서 (GAP-02: AI 이슈 플래그 추가) ──

function ProposalContent({ data, proposalId }: { data: Record<string, unknown>; proposalId?: string }) {
  const sections = data.sections as Array<{ title: string; content: string }> | undefined;
  const summary = data.summary as string | undefined;
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  // GAP-02: AI issue flags — self_review에서 취약 섹션 자동 표시
  const [aiIssues, setAiIssues] = useState<Array<{ section: string; score: number; issue: string }>>([]);
  useEffect(() => {
    if (!proposalId) return;
    api.artifacts.get(proposalId, "self_review").then((a) => {
      const d = a.data as Record<string, unknown>;
      const scores = d.section_scores as Array<{ section: string; score: number; issue?: string }> | undefined;
      if (Array.isArray(scores)) {
        setAiIssues(scores.filter((s) => s.score < 70).map((s) => ({ section: s.section, score: s.score, issue: s.issue ?? "자가진단 점수 미달" })));
      }
    }).catch(() => {});
  }, [proposalId]);

  // 섹션별 이슈 매핑
  const issueMap = new Map(aiIssues.map((i) => [i.section, i]));

  return (
    <div>
      {summary && <Section title="요약"><p className="text-xs text-[#ededed] leading-relaxed">{summary}</p></Section>}

      {/* GAP-02: AI 이슈 플래그 배너 */}
      {aiIssues.length > 0 && (
        <Section title={`AI 이슈 (${aiIssues.length}건)`} variant="warning">
          <div className="space-y-1">
            {aiIssues.map((issue, i) => (
              <div key={i} className="flex items-center gap-2 text-[10px]">
                <span className="text-red-400 font-bold shrink-0">{issue.score}점</span>
                <span className="text-[#ededed]">{issue.section}</span>
                <span className="text-[#8c8c8c] truncate">{issue.issue}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {sections && sections.length > 0 ? (
        <div className="space-y-2">
          {sections.map((sec, i) => {
            const issue = issueMap.get(sec.title);
            return (
              <div key={i} className={`border rounded-xl overflow-hidden ${issue ? "border-red-500/30" : "border-[#262626]"}`}>
                <button
                  onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                  className="w-full flex items-center justify-between px-3.5 py-2.5 hover:bg-[#1c1c1c] transition-colors text-left"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`text-[10px] font-bold rounded w-5 h-5 flex items-center justify-center shrink-0 ${
                      issue ? "text-red-400 bg-red-500/10" : "text-[#3ecf8e] bg-[#3ecf8e]/10"
                    }`}>{i + 1}</span>
                    <span className="text-xs font-medium text-[#ededed] truncate">{sec.title}</span>
                    {issue && <span className="text-[8px] text-red-400 bg-red-500/10 rounded px-1.5 py-0.5 shrink-0">{issue.score}점</span>}
                  </div>
                  <svg className={`w-3.5 h-3.5 text-[#5c5c5c] transition-transform shrink-0 ${expandedIdx === i ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedIdx === i && (
                  <div className="px-3.5 pb-3 border-t border-[#1c1c1c]">
                    {issue && (
                      <div className="mt-2 mb-2 bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2">
                        <p className="text-[10px] text-red-400">{issue.issue}</p>
                      </div>
                    )}
                    <div className="pt-2 text-xs text-[#ededed] leading-relaxed whitespace-pre-wrap">{sec.content}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <GenericContent data={data} />
      )}
    </div>
  );
}

// ── PPT 스토리보드 (GAP-03) ──

function PptStoryboardContent({ data }: { data: Record<string, unknown> }) {
  const slides = data.slides as Array<{ slide_no: number; title: string; content: string; visual_hint?: string }> | undefined;
  const totalSlides = data.total_slides as number | undefined;
  const strategy = data.presentation_strategy as string | undefined;

  return (
    <div>
      {strategy && <Section title="발표 전략" variant="success"><p className="text-xs text-[#ededed] leading-relaxed">{strategy}</p></Section>}
      {totalSlides && <div className="mb-3"><KV label="슬라이드 수" value={`${totalSlides}장`} /></div>}
      {slides && slides.length > 0 ? (
        <div className="space-y-2">
          {slides.map((s) => (
            <div key={s.slide_no} className="border border-[#262626] rounded-xl px-3.5 py-2.5">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 rounded w-5 h-5 flex items-center justify-center shrink-0">{s.slide_no}</span>
                <span className="text-xs font-medium text-[#ededed]">{s.title}</span>
              </div>
              <p className="text-[10px] text-[#8c8c8c] leading-relaxed">{s.content}</p>
              {s.visual_hint && <p className="text-[10px] text-indigo-400/60 mt-1">{s.visual_hint}</p>}
            </div>
          ))}
        </div>
      ) : (
        <GenericContent data={data} />
      )}
    </div>
  );
}

// ── 자가진단 ──

function SelfReviewContent({ data }: { data: Record<string, unknown> }) {
  const total = data.total as number | undefined;
  const axes = [
    { label: "컴플라이언스", score: data.compliance_score as number | undefined, max: 25 },
    { label: "전략 일관성",  score: data.strategy_score as number | undefined,    max: 25 },
    { label: "작성 품질",    score: data.quality_score as number | undefined,     max: 25 },
    { label: "근거 신뢰성",  score: (data.trustworthiness as Record<string, unknown>)?.trustworthiness_score as number | undefined, max: 25 },
  ];
  const tc = (total ?? 0) >= 80 ? "text-[#3ecf8e]" : (total ?? 0) >= 60 ? "text-amber-400" : "text-red-400";

  return (
    <div>
      {total != null && (
        <div className="text-center mb-4 pb-4 border-b border-[#262626]">
          <p className={`text-4xl font-bold ${tc}`}>{total}</p>
          <p className="text-[10px] text-[#8c8c8c] mt-1">/ 100점</p>
        </div>
      )}
      <div className="space-y-3">
        {axes.map((a) => {
          const pct = ((a.score ?? 0) / a.max) * 100;
          const bc = pct >= 80 ? "bg-[#3ecf8e]" : pct >= 60 ? "bg-amber-500" : "bg-red-500";
          return (
            <div key={a.label}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] text-[#8c8c8c]">{a.label}</span>
                <span className="text-[11px] font-bold text-[#ededed]">{a.score ?? 0}/{a.max}</span>
              </div>
              <div className="h-2 bg-[#1c1c1c] rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${bc} transition-all duration-500`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── 범용 (키-값 + JSON) ──

function GenericContent({ data }: { data: Record<string, unknown> }) {
  const [expanded, setExpanded] = useState(false);
  const entries = Object.entries(data);
  if (entries.length === 0) return <p className="text-xs text-[#5c5c5c] text-center py-8">데이터 없음</p>;

  const simple = entries.filter(([, v]) => typeof v === "string" || typeof v === "number" || typeof v === "boolean");
  const complex = entries.filter(([, v]) => typeof v !== "string" && typeof v !== "number" && typeof v !== "boolean" && v !== null);

  return (
    <div>
      {simple.length > 0 && <Section title="요약">{simple.map(([k, v]) => <KV key={k} label={k} value={String(v)} />)}</Section>}
      {complex.length > 0 && (
        <div>
          <button onClick={() => setExpanded(!expanded)} className="text-[10px] text-[#3ecf8e] hover:underline mb-2">
            {expanded ? "▾ 상세 데이터 접기" : "▸ 상세 데이터 보기"}
          </button>
          {expanded && (
            <pre className="text-[10px] text-[#8c8c8c] whitespace-pre-wrap break-words font-mono bg-[#0f0f0f] rounded-xl p-3 max-h-[400px] overflow-auto leading-relaxed">
              {JSON.stringify(Object.fromEntries(complex), null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
