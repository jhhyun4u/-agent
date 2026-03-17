"use client";

/**
 * 제안서 편집 페이지 — 3단 레이아웃 (§13-10)
 *
 * /proposals/[id]/edit
 * 좌: 목차 + Compliance | 중앙: Tiptap 에디터 | 우: AI 어시스턴트
 */

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import dynamic from "next/dynamic";
import { api, type ComplianceItem, type ArtifactData } from "@/lib/api";
import EditorTocPanel, { type TocSection } from "@/components/EditorTocPanel";
import EditorAiPanel, {
  type StrategyCheck,
  type KbReference,
  type ChangeEntry,
} from "@/components/EditorAiPanel";

// Tiptap은 SSR 비호환 — dynamic import
const ProposalEditor = dynamic(
  () => import("@/components/ProposalEditor"),
  { ssr: false, loading: () => <EditorSkeleton /> }
);

function EditorSkeleton() {
  return (
    <div className="flex items-center justify-center h-full text-[#8c8c8c] text-sm">
      <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
      에디터 로딩 중...
    </div>
  );
}

export default function ProposalEditPage() {
  const { id } = useParams<{ id: string }>();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);

  // 에디터 콘텐츠
  const [content, setContent] = useState("");

  // 좌측 패널 데이터
  const [sections, setSections] = useState<TocSection[]>([]);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [complianceItems, setComplianceItems] = useState<ComplianceItem[]>([]);

  // 우측 패널 데이터
  const [strategyChecks, setStrategyChecks] = useState<StrategyCheck[]>([]);
  const [kbReferences, setKbReferences] = useState<KbReference[]>([]);
  const [changes, setChanges] = useState<ChangeEntry[]>([]);

  // ── 데이터 로드 ──

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [proposalArtifact, complianceData] = await Promise.allSettled([
        api.artifacts.get(id, "proposal"),
        api.artifacts.getCompliance(id),
      ]);

      // 제안서 본문
      if (proposalArtifact.status === "fulfilled") {
        const data = proposalArtifact.value.data as Record<string, unknown>;
        const html = (data.html_content as string) ?? (data.content as string) ?? "";
        setContent(html);

        // 섹션 목차 추출
        const dynSections = (data.sections ?? data.dynamic_sections) as
          | Array<{ id?: string; title?: string; level?: number }>
          | undefined;
        if (Array.isArray(dynSections)) {
          setSections(
            dynSections.map((s, i) => ({
              id: s.id ?? `section-${i}`,
              title: s.title ?? `섹션 ${i + 1}`,
              level: s.level ?? 1,
            }))
          );
        }

        // Strategy checks
        const strategy = data.strategy_checks as StrategyCheck[] | undefined;
        if (strategy) setStrategyChecks(strategy);
        else {
          // 기본 체크리스트
          setStrategyChecks([
            { label: "Ghost Theme 반영", met: true },
            { label: "Win Theme 반영", met: true },
            { label: "차별화 포인트", met: false },
          ]);
        }

        // KB references
        const refs = data.kb_references as KbReference[] | undefined;
        if (refs) setKbReferences(refs);

        // Change history
        const history = data.changes as ChangeEntry[] | undefined;
        if (history) setChanges(history);
      }

      // Compliance matrix
      if (complianceData.status === "fulfilled") {
        setComplianceItems(complianceData.value.items);
      }
    } catch {
      // 데이터 없으면 빈 상태로 시작
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── 자동 저장 ──

  const handleContentUpdate = useCallback(
    async (html: string) => {
      setSaving(true);
      try {
        await api.artifacts.save(id, "proposal", html);
        setLastSaved(new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }));
      } catch {
        // 저장 실패 시 무시 (재시도는 다음 debounce)
      } finally {
        setSaving(false);
      }
    },
    [id]
  );

  // ── 섹션 클릭 → 에디터 스크롤 ──

  function handleSectionClick(sectionId: string) {
    setActiveSection(sectionId);
    const el = document.getElementById(sectionId);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ── DOCX 내보내기 ──

  function handleExportDocx() {
    const url = api.artifacts.downloadDocxUrl(id);
    window.open(url, "_blank");
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center text-[#8c8c8c] text-sm">
        <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
        불러오는 중...
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#0f0f0f] text-[#ededed] flex flex-col overflow-hidden">
      {/* 헤더 */}
      <header className="bg-[#111111] border-b border-[#262626] px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href={`/proposals/${id}`}
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
          >
            ← 돌아가기
          </Link>
          <h1 className="text-sm font-semibold text-[#ededed]">제안서 편집</h1>
        </div>
        <div className="flex items-center gap-3">
          {lastSaved && (
            <span className="text-[10px] text-[#5c5c5c]">
              {saving ? "저장 중..." : `마지막 저장: ${lastSaved}`}
            </span>
          )}
          <button
            onClick={handleExportDocx}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-[#262626] text-[#ededed] hover:bg-[#262626] transition-colors"
          >
            DOCX 내보내기
          </button>
        </div>
      </header>

      {/* 3단 레이아웃 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 좌측: 목차 + Compliance */}
        <aside className="w-56 bg-[#1c1c1c] border-r border-[#262626] shrink-0 overflow-hidden">
          <EditorTocPanel
            sections={sections}
            activeSection={activeSection}
            onSectionClick={handleSectionClick}
            complianceItems={complianceItems}
          />
        </aside>

        {/* 중앙: Tiptap 에디터 */}
        <main className="flex-1 overflow-hidden">
          <ProposalEditor
            content={content}
            onUpdate={handleContentUpdate}
          />
        </main>

        {/* 우측: AI 어시스턴트 */}
        <aside className="w-56 bg-[#1c1c1c] border-l border-[#262626] shrink-0 overflow-hidden">
          <EditorAiPanel
            proposalId={id}
            complianceItems={complianceItems}
            strategyChecks={strategyChecks}
            kbReferences={kbReferences}
            changes={changes}
            activeSectionId={activeSection}
            onApplySuggestion={(html) => setContent(html)}
          />
        </aside>
      </div>

      {/* 하단 상태바 */}
      <footer className="bg-[#111111] border-t border-[#262626] px-4 py-1.5 flex items-center gap-4 text-[10px] text-[#5c5c5c] shrink-0">
        <span>{saving ? "저장 중..." : lastSaved ? `마지막 저장: ${lastSaved}` : "미저장"}</span>
        <span>•</span>
        <span>{sections.length}개 섹션</span>
        <span>•</span>
        <span>
          Compliance: {complianceItems.filter((i) => i.status === "met").length}/
          {complianceItems.length}
        </span>
      </footer>
    </div>
  );
}
