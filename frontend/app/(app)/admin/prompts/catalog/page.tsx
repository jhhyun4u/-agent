"use client";

/**
 * 프롬프트 카탈로그 (v1 이동 + WorkflowMap 추가)
 *
 * /admin/prompts/catalog
 * - 워크플로 맵에서 프롬프트 위치 확인
 * - 6개 카테고리 탭 필터
 * - 전체 프롬프트 테이블
 * - 섹션 히트맵
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  type PromptDashboard,
  type PromptCategory,
  type SectionHeatmapItem,
  type WorkflowMapData,
} from "@/lib/api";
import CategoryTabs, { CAT_STYLE } from "@/components/prompt/CategoryTabs";
import WorkflowMap from "@/components/prompt/WorkflowMap";
import { getPromptLabel, getPromptDescription, normalizePromptId } from "@/components/prompt/promptLabels";

// ── DEV 폴백: 백엔드 미접속 시 시드 데이터 ──
const SEED_SECTION_TYPES = [
  "UNDERSTAND", "STRATEGY", "METHODOLOGY", "TECHNICAL", "MANAGEMENT",
  "PERSONNEL", "TRACK_RECORD", "SECURITY", "MAINTENANCE", "ADDED_VALUE",
];

const SEED_DASHBOARD: PromptDashboard = {
  total_prompts: SEED_SECTION_TYPES.length + 4,
  prompts: [
    ...SEED_SECTION_TYPES.map((id) => ({
      prompt_id: `section.${id}`, version: 1, source_file: "section_prompts.py",
      status: "active", content_hash: "-", metadata: {}, created_at: "2026-03-01", created_by: "system",
    })),
    { prompt_id: "strategy.positioning", version: 1, source_file: "strategy.py", status: "active", content_hash: "-", metadata: {}, created_at: "2026-03-01", created_by: "system" },
    { prompt_id: "plan.story", version: 1, source_file: "plan.py", status: "active", content_hash: "-", metadata: {}, created_at: "2026-03-01", created_by: "system" },
    { prompt_id: "plan.price", version: 1, source_file: "plan.py", status: "active", content_hash: "-", metadata: {}, created_at: "2026-03-01", created_by: "system" },
    { prompt_id: "self_review", version: 1, source_file: "proposal_prompts.py", status: "active", content_hash: "-", metadata: {}, created_at: "2026-03-01", created_by: "system" },
  ],
  effectiveness: [
    { prompt_id: "section.UNDERSTAND", prompt_version: 1, proposals_used: 12, won: 8, lost: 4, win_rate: 66.7, avg_quality_score: 82, avg_input_tokens: 4200, avg_output_tokens: 1800, avg_duration_ms: 3200 },
    { prompt_id: "section.STRATEGY", prompt_version: 1, proposals_used: 12, won: 8, lost: 4, win_rate: 66.7, avg_quality_score: 79, avg_input_tokens: 5100, avg_output_tokens: 2200, avg_duration_ms: 4100 },
    { prompt_id: "section.METHODOLOGY", prompt_version: 1, proposals_used: 10, won: 7, lost: 3, win_rate: 70.0, avg_quality_score: 85, avg_input_tokens: 4800, avg_output_tokens: 2000, avg_duration_ms: 3800 },
    { prompt_id: "section.TECHNICAL", prompt_version: 1, proposals_used: 11, won: 6, lost: 5, win_rate: 54.5, avg_quality_score: 75, avg_input_tokens: 5500, avg_output_tokens: 2500, avg_duration_ms: 4500 },
    { prompt_id: "section.PERSONNEL", prompt_version: 1, proposals_used: 9, won: 6, lost: 3, win_rate: 66.7, avg_quality_score: 80, avg_input_tokens: 3800, avg_output_tokens: 1500, avg_duration_ms: 2800 },
  ],
  edit_stats: [
    { prompt_id: "section.TECHNICAL", edit_count: 18, avg_edit_ratio: 0.62, actions: { rewrite: 8, refine: 10 } },
    { prompt_id: "section.UNDERSTAND", edit_count: 5, avg_edit_ratio: 0.25, actions: { refine: 5 } },
    { prompt_id: "section.STRATEGY", edit_count: 8, avg_edit_ratio: 0.35, actions: { rewrite: 2, refine: 6 } },
    { prompt_id: "section.MAINTENANCE", edit_count: 12, avg_edit_ratio: 0.55, actions: { rewrite: 6, refine: 6 } },
  ],
  running_experiments: [],
};

const SEED_HEATMAP: SectionHeatmapItem[] = SEED_SECTION_TYPES.map((id, i) => ({
  section_id: id,
  usage_count: 12 - i,
  avg_quality: [82, 79, 85, 75, 78, 80, 72, 77, 70, 83][i] ?? 75,
  unique_prompts: 1,
}));

export default function CatalogPage() {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<PromptDashboard | null>(null);
  const [categories, setCategories] = useState<PromptCategory[]>([]);
  const [heatmap, setHeatmap] = useState<SectionHeatmapItem[]>([]);
  const [workflowMap, setWorkflowMap] = useState<WorkflowMapData | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>("all");

  const fetchData = useCallback(async () => {
    setLoading(true);
    const [dashRes, heatRes, catRes, mapRes] = await Promise.allSettled([
      api.prompts.dashboard(),
      api.prompts.sectionHeatmap(),
      api.prompts.categories(),
      api.prompts.workflowMap(),
    ]);
    if (dashRes.status === "fulfilled") setDashboard(dashRes.value);
    else setDashboard(SEED_DASHBOARD);
    if (heatRes.status === "fulfilled") setHeatmap(heatRes.value.heatmap);
    else setHeatmap(SEED_HEATMAP);
    if (catRes.status === "fulfilled") setCategories(catRes.value.categories);
    if (mapRes.status === "fulfilled") setWorkflowMap(mapRes.value);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const effMap = new Map(
    (dashboard?.effectiveness ?? []).map((e) => [`${e.prompt_id}:${e.prompt_version}`, e]),
  );
  const editMap = new Map(
    (dashboard?.edit_stats ?? []).map((e) => [e.prompt_id, e]),
  );

  const catPromptIds = new Set<string>();
  if (activeCategory !== "all") {
    const cat = categories.find((c) => c.id === activeCategory);
    cat?.prompts.forEach((p) => catPromptIds.add(p.prompt_id));
  }

  const filteredPrompts = (dashboard?.prompts ?? []).filter(
    (p) => activeCategory === "all" || catPromptIds.has(p.prompt_id),
  );

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/prompts" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">
              &larr; 학습 대시보드
            </Link>
            <h1 className="text-sm font-semibold">프롬프트 카탈로그</h1>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            로딩 중...
          </div>
        )}

        {!loading && (
          <>
            {/* 워크플로 맵 */}
            {workflowMap && (
              <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                <WorkflowMap data={workflowMap} />
              </section>
            )}

            {/* 카테고리 탭 */}
            {dashboard && (
              <CategoryTabs
                categories={categories}
                activeCategory={activeCategory}
                onSelect={setActiveCategory}
                totalPrompts={dashboard.total_prompts}
              />
            )}

            {/* 프롬프트 테이블 */}
            <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
              <h2 className="text-sm font-semibold mb-4">
                프롬프트 목록 ({filteredPrompts.length}개)
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[#8c8c8c] border-b border-[#262626]">
                      <th className="text-left pb-2 pr-4">프롬프트</th>
                      <th className="text-left pb-2 pr-4">단계</th>
                      <th className="text-right pb-2 pr-4">버전</th>
                      <th className="text-right pb-2 pr-4">사용</th>
                      <th className="text-right pb-2 pr-4">승률</th>
                      <th className="text-right pb-2 pr-4">수정율</th>
                      <th className="text-right pb-2">품질</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPrompts.map((p) => {
                      const eff = effMap.get(`${p.prompt_id}:${p.version}`);
                      const es = editMap.get(p.prompt_id);
                      const nid = normalizePromptId(p.prompt_id);
                      const label = getPromptLabel(nid);
                      const desc = getPromptDescription(nid);
                      const catId = categories.find((c) => c.prompts.some((cp) => cp.prompt_id === p.prompt_id))?.id;
                      const catLabel = categories.find((c) => c.id === catId)?.label ?? "";
                      const catStyle = CAT_STYLE[catId ?? ""];
                      return (
                        <tr key={p.prompt_id} className="border-b border-[#1a1a1a] hover:bg-[#222]">
                          <td className="py-2 pr-4 max-w-[280px]">
                            <Link
                              href={`/admin/prompts/${encodeURIComponent(p.prompt_id)}`}
                              className="text-[#3ecf8e] hover:underline text-xs font-medium"
                            >
                              {label}
                            </Link>
                            {desc && (
                              <div className="text-[10px] text-[#666] mt-0.5 truncate">{desc}</div>
                            )}
                          </td>
                          <td className="py-2 pr-4">
                            {catLabel ? (
                              <span
                                className="px-1.5 py-0.5 rounded text-[10px] font-medium"
                                style={{ backgroundColor: `${catStyle?.color ?? "#666"}20`, color: catStyle?.color ?? "#666" }}
                              >
                                {catLabel}
                              </span>
                            ) : (
                              <span className="text-[10px] text-[#666]">
                                {getPromptLabel(nid) !== label ? "" : nid.split(".")[0]}
                              </span>
                            )}
                          </td>
                          <td className="text-right pr-4">v{p.version}</td>
                          <td className="text-right pr-4">{eff?.proposals_used ?? 0}</td>
                          <td className="text-right pr-4">{eff?.win_rate != null ? `${eff.win_rate}%` : "-"}</td>
                          <td className="text-right pr-4">
                            <span className={(es?.avg_edit_ratio ?? 0) > 0.5 ? "text-[#ff6b6b]" : ""}>
                              {es ? `${(es.avg_edit_ratio * 100).toFixed(0)}%` : "-"}
                            </span>
                          </td>
                          <td className="text-right">{eff?.avg_quality_score?.toFixed(0) ?? "-"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>

            {/* 히트맵 */}
            {heatmap.length > 0 && (
              <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
                <h2 className="text-sm font-semibold mb-4">섹션 유형별 히트맵</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {heatmap.map((h) => (
                    <div
                      key={h.section_id}
                      className="bg-[#111] rounded-lg p-3 border border-[#262626]"
                      style={{ borderLeftColor: heatColor(h.avg_quality), borderLeftWidth: 3 }}
                    >
                      <div className="text-xs font-mono truncate">{h.section_id}</div>
                      <div className="text-[#8c8c8c] text-xs mt-1">
                        사용 {h.usage_count}회 | 품질 {h.avg_quality?.toFixed(0) ?? "-"}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function heatColor(quality: number | null): string {
  if (quality == null) return "#262626";
  if (quality >= 80) return "#3ecf8e";
  if (quality >= 60) return "#f5a623";
  return "#ff6b6b";
}
