"use client";

/**
 * 제안서 편집 뷰 — 3단 레이아웃 (§13-10)
 * 좌: 목차 + Compliance | 중앙: Tiptap 에디터 | 우: AI 어시스턴트
 *
 * 공유 컴포넌트: /proposals/[id]/edit 및 /editor/[id] 양쪽에서 사용
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import KeyboardShortcutsGuide from "@/components/KeyboardShortcutsGuide";
import Breadcrumb from "@/components/Breadcrumb";
import { api, type ComplianceItem, type SectionLock } from "@/lib/api";
import EditorTocPanel, { type TocSection } from "@/components/EditorTocPanel";
import EditorAiPanel, {
  type StrategyCheck,
  type KbReference,
  type ChangeEntry,
} from "@/components/EditorAiPanel";

const ProposalEditor = dynamic(
  () => import("@/components/ProposalEditor"),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full text-[#8c8c8c] text-sm">
        <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
        에디터 로딩 중...
      </div>
    ),
  }
);

interface ProposalEditViewProps {
  id: string;
  /** true이면 "돌아가기" 대신 window.close() */
  standalone?: boolean;
}

export default function ProposalEditView({ id, standalone }: ProposalEditViewProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [mobilePanel, setMobilePanel] = useState<"toc" | "editor" | "ai">("editor");

  const [content, setContent] = useState("");
  const [sections, setSections] = useState<TocSection[]>([]);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [complianceItems, setComplianceItems] = useState<ComplianceItem[]>([]);

  const [strategyChecks, setStrategyChecks] = useState<StrategyCheck[]>([]);
  const [kbReferences, setKbReferences] = useState<KbReference[]>([]);
  const [changes, setChanges] = useState<ChangeEntry[]>([]);
  const [sectionLocks, setSectionLocks] = useState<SectionLock[]>([]);

  // BroadcastChannel for cross-window sync
  const channelRef = useRef<BroadcastChannel | null>(null);
  useEffect(() => {
    channelRef.current = new BroadcastChannel(`tenopa-proposal-${id}`);
    return () => { channelRef.current?.close(); };
  }, [id]);

  // ── 데이터 로드 ──
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [proposalArtifact, complianceData] = await Promise.allSettled([
        api.artifacts.get(id, "proposal"),
        api.artifacts.getCompliance(id),
      ]);

      if (proposalArtifact.status === "fulfilled") {
        const data = proposalArtifact.value.data as Record<string, unknown>;
        const html = (data.html_content as string) ?? (data.content as string) ?? "";
        setContent(html);

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

        const strategy = data.strategy_checks as StrategyCheck[] | undefined;
        if (strategy) setStrategyChecks(strategy);
        else {
          setStrategyChecks([
            { label: "Ghost Theme 반영", met: true },
            { label: "Win Theme 반영", met: true },
            { label: "차별화 포인트", met: false },
          ]);
        }

        const refs = data.kb_references as KbReference[] | undefined;
        if (refs) setKbReferences(refs);

        const history = data.changes as ChangeEntry[] | undefined;
        if (history) setChanges(history);
      }

      if (complianceData.status === "fulfilled") {
        setComplianceItems(complianceData.value.items);
      }
    } catch {
      // 데이터 없으면 빈 상태로 시작
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // 섹션 잠금 폴링 (10초 간격)
  useEffect(() => {
    let active = true;
    async function pollLocks() {
      try {
        const res = await api.workflow.listLocks(id);
        if (active) setSectionLocks(res.locks);
      } catch { /* silent */ }
    }
    pollLocks();
    const interval = setInterval(pollLocks, 10_000);
    return () => { active = false; clearInterval(interval); };
  }, [id]);

  // ── 비저장 경고: beforeunload ──
  useEffect(() => {
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      if (isDirty) { e.preventDefault(); e.returnValue = ""; }
    }
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isDirty]);

  // ── 키보드 단축키 ──
  const contentRef = useRef(content);
  contentRef.current = content;

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        if (isDirty) flushSave(contentRef.current);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "/") {
        e.preventDefault();
        setShortcutsOpen(prev => !prev);
      }
      if (e.key === "Escape" && shortcutsOpen) setShortcutsOpen(false);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isDirty, shortcutsOpen]);

  // ── 즉시 저장 (Ctrl+S용) ──
  const flushSave = useCallback(async (html: string) => {
    setSaving(true);
    try {
      await api.artifacts.save(id, "proposal", html);
      setLastSaved(new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }));
      setIsDirty(false);
      channelRef.current?.postMessage({ type: "saved" });
    } catch { /* silent */ }
    finally { setSaving(false); }
  }, [id]);

  // ── 자동 저장 + BroadcastChannel 알림 + 수정 추적 ──
  const prevContentRef = useRef(content);
  const handleContentUpdate = useCallback(
    async (html: string) => {
      setIsDirty(true);
      setSaving(true);
      try {
        await api.artifacts.save(id, "proposal", html);
        setLastSaved(new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }));
        setIsDirty(false);
        // 다른 창(상세 페이지)에 저장 완료 알림
        channelRef.current?.postMessage({ type: "saved" });
        // 프롬프트 수정 추적 (비동기, 실패 무시)
        if (prevContentRef.current && prevContentRef.current !== html) {
          api.prompts.recordEditAction({
            proposal_id: id,
            section_id: activeSection ?? "full_proposal",
            action: "edit",
            original: prevContentRef.current.slice(0, 5000),
            edited: html.slice(0, 5000),
          }).catch(() => {});
        }
        prevContentRef.current = html;
      } catch {
        // 저장 실패 시 무시
      } finally {
        setSaving(false);
      }
    },
    [id, activeSection]
  );

  function handleSectionClick(sectionId: string) {
    setActiveSection(sectionId);
    const el = document.getElementById(sectionId);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function handleBack() {
    if (isDirty && !confirm("저장하지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?")) return;
    if (standalone) window.close();
    else router.push(`/proposals/${id}`);
  }

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
          {standalone ? (
            <button onClick={handleBack} className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">닫기</button>
          ) : (
            <Breadcrumb items={[
              { label: "제안 프로젝트", href: "/proposals" },
              { label: "프로젝트", href: `/proposals/${id}` },
              { label: "편집" },
            ]} />
          )}
          {isDirty && <span className="text-[9px] text-amber-400 font-medium">수정됨</span>}
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

      {/* 3단 레이아웃 — 반응형: lg 이상 3컬럼, 미만 탭 전환 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 좌측 TOC — lg 이상만 표시 */}
        <aside className="hidden lg:block w-56 bg-[#1c1c1c] border-r border-[#262626] shrink-0 overflow-hidden">
          <EditorTocPanel
            sections={sections}
            activeSection={activeSection}
            onSectionClick={handleSectionClick}
            complianceItems={complianceItems}
          />
        </aside>

        {/* 중앙 — 모바일 탭 + 에디터 */}
        <main className="flex-1 overflow-hidden flex flex-col">
          {/* 모바일 탭 바 — lg 미만 */}
          <MobileTabBar activeTab={mobilePanel} onTabChange={setMobilePanel} />

          {/* 모바일: 선택된 패널 */}
          <div className="lg:hidden flex-1 overflow-hidden">
            {mobilePanel === "toc" && (
              <EditorTocPanel sections={sections} activeSection={activeSection} onSectionClick={handleSectionClick} complianceItems={complianceItems} />
            )}
            {mobilePanel === "editor" && (
              <ProposalEditor content={content} onUpdate={handleContentUpdate} onChange={() => setIsDirty(true)} />
            )}
            {mobilePanel === "ai" && (
              <EditorAiPanel proposalId={id} complianceItems={complianceItems} strategyChecks={strategyChecks} kbReferences={kbReferences} changes={changes} activeSectionId={activeSection} currentContent={content} onApplySuggestion={(html) => setContent(html)} />
            )}
          </div>

          {/* 데스크톱: 에디터만 */}
          <div className="hidden lg:block flex-1 overflow-hidden">
            <ProposalEditor content={content} onUpdate={handleContentUpdate} onChange={() => setIsDirty(true)} />
          </div>
        </main>

        {/* 우측 AI — lg 이상만 표시 */}
        <aside className="hidden lg:block w-56 bg-[#1c1c1c] border-l border-[#262626] shrink-0 overflow-hidden">
          <EditorAiPanel
            proposalId={id}
            complianceItems={complianceItems}
            strategyChecks={strategyChecks}
            kbReferences={kbReferences}
            changes={changes}
            activeSectionId={activeSection}
            currentContent={content}
            onApplySuggestion={(html) => setContent(html)}
          />
        </aside>
      </div>

      {/* 하단 상태바 */}
      <footer className="bg-[#111111] border-t border-[#262626] px-4 py-1.5 flex items-center gap-4 text-[10px] text-[#5c5c5c] shrink-0">
        <span className={isDirty && !saving ? "text-amber-400" : ""}>
          {saving ? "저장 중..." : isDirty ? "수정됨 (저장 대기)" : lastSaved ? `마지막 저장: ${lastSaved}` : "미저장"}
        </span>
        <span>•</span>
        <span>{sections.length}개 섹션</span>
        <span>•</span>
        <span>
          Compliance: {complianceItems.filter((i) => i.status === "met").length}/
          {complianceItems.length}
        </span>
        {sectionLocks.length > 0 && (
          <>
            <span>•</span>
            <span className="text-amber-400">
              {sectionLocks.length}개 섹션 편집 중
              {sectionLocks.map((l) => l.locked_by_name || l.locked_by).filter(Boolean).length > 0 &&
                ` (${[...new Set(sectionLocks.map((l) => l.locked_by_name || "").filter(Boolean))].join(", ")})`
              }
            </span>
          </>
        )}
      </footer>

      {/* 키보드 단축키 가이드 */}
      <KeyboardShortcutsGuide open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
    </div>
  );
}

// ── 모바일 탭 바 (lg 미만에서만 표시) ──
function MobileTabBar({
  activeTab,
  onTabChange,
}: {
  activeTab: "toc" | "editor" | "ai";
  onTabChange: (tab: "toc" | "editor" | "ai") => void;
}) {
  const tabs = [
    { key: "toc" as const, label: "목차" },
    { key: "editor" as const, label: "편집" },
    { key: "ai" as const, label: "AI" },
  ];

  return (
    <div className="lg:hidden flex border-b border-[#262626] bg-[#1c1c1c] shrink-0">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onTabChange(tab.key)}
          className={`flex-1 py-2 text-[10px] font-medium transition-colors ${
            activeTab === tab.key
              ? "text-[#3ecf8e] border-b-2 border-[#3ecf8e]"
              : "text-[#8c8c8c] hover:text-[#ededed]"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
