"use client";

/**
 * FileHubPanel — 통합 파일 허브
 *
 * AI 산출물, 첨부파일, 제출서류, 생성문서를 한 곳에서 조회·관리.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { api, submissionDocsApi, type ProposalFile, type SubmissionDocument } from "@/lib/api";

// ── AI 산출물 정의 (FileBar에서 이관) ──
const ARTIFACT_DOCS = [
  { key: "search_results",  label: "공고 검색",     icon: "S",  color: "text-blue-400 bg-blue-500/15",       step: 0 },
  { key: "rfp_analyze",     label: "RFP 분석",      icon: "R",  color: "text-purple-400 bg-purple-500/15",   step: 0 },
  { key: "research_gather", label: "리서치",         icon: "L",  color: "text-cyan-400 bg-cyan-500/15",       step: 0 },
  { key: "go_no_go",        label: "Go/No-Go",      icon: "G",  color: "text-emerald-400 bg-emerald-500/15", step: 0 },
  { key: "strategy",        label: "전략기획",       icon: "W",  color: "text-amber-400 bg-amber-500/15",     step: 1 },
  { key: "plan",            label: "제안 계획",      icon: "P",  color: "text-cyan-400 bg-cyan-500/15",       step: 2 },
  { key: "proposal",        label: "제안서",         icon: "D",  color: "text-blue-400 bg-blue-500/15",       step: 3 },
  { key: "self_review",     label: "자가진단",       icon: "Q",  color: "text-orange-400 bg-orange-500/15",   step: 3 },
  { key: "ppt_storyboard",  label: "PPT",            icon: "T",  color: "text-indigo-400 bg-indigo-500/15",   step: 4 },
  { key: "mock_evaluation", label: "모의 평가",      icon: "E",  color: "text-violet-400 bg-violet-500/15",   step: 5 },
  { key: "submission_plan",     label: "제출서류 계획", icon: "F",  color: "text-pink-400 bg-pink-500/15",     step: 6 },
  { key: "bid_plan",            label: "입찰가 결정",   icon: "$",  color: "text-amber-400 bg-amber-500/15",   step: 7 },
  { key: "cost_sheet",          label: "산출내역서",    icon: "C",  color: "text-green-400 bg-green-500/15",   step: 8 },
  { key: "submission_checklist", label: "제출서류 확인", icon: "V",  color: "text-teal-400 bg-teal-500/15",    step: 9 },
  { key: "eval_result",     label: "평가결과",       icon: "7",  color: "text-rose-400 bg-rose-500/15",       step: 10 },
  { key: "project_closing", label: "Closing",        icon: "8",  color: "text-[#8c8c8c] bg-[#262626]",       step: 11 },
] as const;

// 파일 확장자 → 색상
function fileColor(ext?: string): string {
  if (!ext) return "text-[#8c8c8c] bg-[#262626]";
  const e = ext.toLowerCase();
  if (e === "pdf") return "text-red-400 bg-red-500/15";
  if (e === "docx") return "text-blue-400 bg-blue-500/15";
  if (e === "hwp" || e === "hwpx") return "text-[#3ecf8e] bg-[#3ecf8e]/15";
  if (e === "pptx") return "text-orange-400 bg-orange-500/15";
  if (e === "xlsx") return "text-green-400 bg-green-500/15";
  if (["png", "jpg", "jpeg"].includes(e)) return "text-pink-400 bg-pink-500/15";
  return "text-[#8c8c8c] bg-[#262626]";
}

function formatBytes(bytes: number | null): string {
  if (!bytes) return "-";
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function formatDateShort(dateStr?: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "";
  return `${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

// 제출서류 상태
const DOC_STATUS: Record<string, { label: string; color: string; icon: string }> = {
  pending:        { label: "대기",     color: "text-[#8c8c8c]", icon: "○" },
  assigned:       { label: "배정됨",   color: "text-blue-400",  icon: "◉" },
  in_progress:    { label: "작성중",   color: "text-amber-400", icon: "◐" },
  uploaded:       { label: "업로드됨", color: "text-cyan-400",  icon: "◑" },
  verified:       { label: "검증완료", color: "text-[#3ecf8e]", icon: "✓" },
  rejected:       { label: "반려",     color: "text-red-400",   icon: "✗" },
  not_applicable: { label: "해당없음", color: "text-[#5c5c5c]", icon: "—" },
  expired:        { label: "만료",     color: "text-red-400",   icon: "!" },
};

// 생성 문서 정의
const GENERATED_DOCS = [
  { key: "docx",       label: "제안서.docx",      icon: "DOCX", color: "text-blue-400 bg-blue-500/15" },
  { key: "hwpx",       label: "제안서.hwpx",      icon: "HWPX", color: "text-[#3ecf8e] bg-[#3ecf8e]/15" },
  { key: "pptx",       label: "발표자료.pptx",    icon: "PPTX", color: "text-orange-400 bg-orange-500/15" },
  { key: "cost-sheet", label: "산출내역서.xlsx",   icon: "XLSX", color: "text-green-400 bg-green-500/15" },
];

// ── Props ──
interface FileHubPanelProps {
  proposalId: string;
  phasesCompleted: number;
  onSelectArtifact: (stepIndex: number, artifactKey: string) => void;
  onSelectFile: (file: ProposalFile) => void;
}

export default function FileHubPanel({
  proposalId,
  phasesCompleted,
  onSelectArtifact,
  onSelectFile,
}: FileHubPanelProps) {
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  // AI 산출물 존재 여부
  const [availableArtifacts, setAvailableArtifacts] = useState<Set<string>>(new Set());
  const [artifactsLoading, setArtifactsLoading] = useState(true);

  // 첨부파일
  const [files, setFiles] = useState<ProposalFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(true);

  // 제출서류
  const [submissionDocs, setSubmissionDocs] = useState<SubmissionDocument[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);

  // 생성 문서 존재 여부
  const [generatedAvailable, setGeneratedAvailable] = useState<Set<string>>(new Set());

  // 파일 업로드
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // ── 데이터 로드 ──
  useEffect(() => {
    // AI 산출물 존재 확인
    const checkArtifacts = async () => {
      setArtifactsLoading(true);
      const avail = new Set<string>();
      await Promise.allSettled(
        ARTIFACT_DOCS.map(async (d) => {
          try { await api.artifacts.get(proposalId, d.key); avail.add(d.key); } catch {}
        })
      );
      setAvailableArtifacts(avail);
      setArtifactsLoading(false);
    };

    // 첨부파일
    const loadFiles = async () => {
      setFilesLoading(true);
      try { setFiles((await api.proposals.listFiles(proposalId)).files); } catch {}
      finally { setFilesLoading(false); }
    };

    // 제출서류
    const loadDocs = async () => {
      setDocsLoading(true);
      try {
        const res = await submissionDocsApi.list(proposalId);
        setSubmissionDocs(Array.isArray(res) ? res : []);
      } catch {}
      finally { setDocsLoading(false); }
    };

    // 생성 문서 존재 확인 (HEAD 요청으로 빠르게)
    const checkGenerated = async () => {
      const avail = new Set<string>();
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      for (const g of GENERATED_DOCS) {
        try {
          const res = await fetch(`${baseUrl}/proposals/${proposalId}/download/${g.key}`, { method: "HEAD" });
          if (res.ok) avail.add(g.key);
        } catch {}
      }
      setGeneratedAvailable(avail);
    };

    checkArtifacts();
    loadFiles();
    loadDocs();
    checkGenerated();
  }, [proposalId, phasesCompleted]);

  // ── 파일 업로드 핸들러 ──
  const handleFileUpload = useCallback(async (fileList: FileList) => {
    setUploading(true);
    try {
      for (const file of Array.from(fileList)) {
        await api.proposals.uploadFile(proposalId, file);
      }
      const res = await api.proposals.listFiles(proposalId);
      setFiles(res.files);
    } catch {
      alert("파일 업로드 실패");
    } finally {
      setUploading(false);
    }
  }, [proposalId]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files);
  }, [handleFileUpload]);

  // ── 생성 문서 다운로드 ──
  const handleDownloadGenerated = (key: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
    window.open(`${baseUrl}/proposals/${proposalId}/download/${key}`, "_blank");
  };

  // ── 섹션 토글 ──
  const toggleSection = (key: string) => setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));

  // ── 검색 필터 ──
  const q = search.toLowerCase().trim();

  const filteredArtifacts = ARTIFACT_DOCS.filter((d) => !q || d.label.toLowerCase().includes(q));
  const filteredFiles = files.filter((f) => !q || f.filename.toLowerCase().includes(q));
  const filteredDocs = submissionDocs.filter((d) => !q || d.doc_type.toLowerCase().includes(q));
  const filteredGenerated = GENERATED_DOCS.filter((g) => !q || g.label.toLowerCase().includes(q));

  const availCount = availableArtifacts.size;
  const totalCount = ARTIFACT_DOCS.length;
  const docsCompleted = submissionDocs.filter((d) => d.status === "verified" || d.status === "uploaded").length;

  return (
    <div className="space-y-1">
      {/* 검색 바 */}
      <div className="px-2 pt-2 pb-1">
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#5c5c5c]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="파일 검색..."
            className="w-full pl-8 pr-3 py-1.5 bg-[#1c1c1c] border border-[#262626] rounded-lg text-xs text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e]/50"
          />
        </div>
      </div>

      {/* ═══ 섹션 1: AI 산출물 ═══ */}
      <Section
        title="AI 산출물"
        badge={`${availCount}/${totalCount}`}
        collapsed={!!collapsed.artifacts}
        onToggle={() => toggleSection("artifacts")}
        loading={artifactsLoading}
      >
        <div className="space-y-0.5">
          {filteredArtifacts.map((d) => {
            const avail = availableArtifacts.has(d.key);
            return (
              <button
                key={d.key}
                onClick={() => avail && onSelectArtifact(d.step, d.key)}
                disabled={!avail}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors ${
                  avail
                    ? "hover:bg-[#1c1c1c] text-[#ededed] cursor-pointer"
                    : "text-[#3c3c3c] cursor-default"
                }`}
              >
                <span className={`w-5 h-5 rounded flex items-center justify-center text-[9px] font-bold shrink-0 ${avail ? d.color : "text-[#3c3c3c] bg-[#1a1a1a]"}`}>
                  {d.icon}
                </span>
                <span className="flex-1 text-left truncate">{d.label}</span>
                {avail ? (
                  <span className="text-[10px] text-[#3ecf8e]">● 생성됨</span>
                ) : (
                  <span className="text-[10px] text-[#3c3c3c]">○ 미생성</span>
                )}
                {avail && (
                  <svg className="w-3 h-3 text-[#5c5c5c] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      </Section>

      {/* ═══ 섹션 2: 첨부파일 ═══ */}
      <Section
        title="첨부파일"
        badge={String(files.length)}
        collapsed={!!collapsed.files}
        onToggle={() => toggleSection("files")}
        loading={filesLoading}
        action={
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-[10px] text-[#3ecf8e] hover:text-[#3ecf8e]/80 transition-colors"
          >
            + 파일 추가
          </button>
        }
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
        />
        <div className="space-y-0.5">
          {filteredFiles.map((f) => (
            <button
              key={f.id}
              onClick={() => onSelectFile(f)}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs hover:bg-[#1c1c1c] text-[#ededed] transition-colors"
            >
              <span className={`w-5 h-5 rounded flex items-center justify-center text-[8px] font-bold shrink-0 ${fileColor(f.file_type ?? undefined)}`}>
                {(f.file_type || "?").slice(0, 3).toUpperCase()}
              </span>
              <span className="flex-1 text-left truncate">{f.filename}</span>
              <span className="text-[10px] text-[#5c5c5c] shrink-0">{formatBytes(f.file_size)}</span>
              <span className="text-[10px] text-[#5c5c5c] shrink-0">{formatDateShort(f.created_at)}</span>
            </button>
          ))}
        </div>

        {/* 드래그 앤 드롭 */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`mt-1 mx-3 mb-2 flex items-center justify-center py-4 border border-dashed rounded-lg text-[11px] transition-colors ${
            dragOver
              ? "border-[#3ecf8e]/50 bg-[#3ecf8e]/5 text-[#3ecf8e]"
              : "border-[#333] text-[#5c5c5c]"
          } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
        >
          {uploading ? "업로드 중..." : "여기에 파일을 드래그하세요"}
        </div>
      </Section>

      {/* ═══ 섹션 3: 제출서류 ═══ */}
      <Section
        title="제출서류"
        badge={submissionDocs.length > 0 ? `${docsCompleted}/${submissionDocs.length} 완료` : "0"}
        collapsed={!!collapsed.submission}
        onToggle={() => toggleSection("submission")}
        loading={docsLoading}
      >
        <div className="space-y-0.5">
          {filteredDocs.length === 0 && !docsLoading && (
            <p className="px-3 py-2 text-[11px] text-[#5c5c5c]">제출서류가 아직 추출되지 않았습니다.</p>
          )}
          {filteredDocs.map((d) => {
            const st = DOC_STATUS[d.status] ?? DOC_STATUS.pending;
            const hasFile = !!d.file_path;
            return (
              <div
                key={d.id}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs hover:bg-[#1c1c1c] transition-colors"
              >
                <span className={`shrink-0 ${st.color}`}>{st.icon}</span>
                <span className="flex-1 text-left truncate text-[#ededed]">{d.doc_type}</span>
                <span className="text-[10px] text-[#5c5c5c] shrink-0">{d.required_format}</span>
                <span className={`text-[10px] shrink-0 ${st.color}`}>{st.label}</span>
                {hasFile && (
                  <button
                    onClick={() => {
                      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
                      window.open(`${baseUrl}/proposals/${proposalId}/submission-docs/${d.id}/download`, "_blank");
                    }}
                    className="text-[#8c8c8c] hover:text-[#ededed] transition-colors shrink-0"
                    title="다운로드"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </Section>

      {/* ═══ 섹션 4: 생성 문서 다운로드 ═══ */}
      <Section
        title="생성 문서 다운로드"
        badge={String(generatedAvailable.size)}
        collapsed={!!collapsed.generated}
        onToggle={() => toggleSection("generated")}
      >
        <div className="space-y-0.5">
          {filteredGenerated.map((g) => {
            const avail = generatedAvailable.has(g.key);
            return (
              <button
                key={g.key}
                onClick={() => avail && handleDownloadGenerated(g.key)}
                disabled={!avail}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors ${
                  avail
                    ? "hover:bg-[#1c1c1c] text-[#ededed] cursor-pointer"
                    : "text-[#3c3c3c] cursor-default"
                }`}
              >
                <span className={`w-5 h-5 rounded flex items-center justify-center text-[8px] font-bold shrink-0 ${avail ? g.color : "text-[#3c3c3c] bg-[#1a1a1a]"}`}>
                  {g.icon}
                </span>
                <span className="flex-1 text-left truncate">{g.label}</span>
                {avail ? (
                  <>
                    <span className="text-[10px] text-[#3ecf8e]">● 다운로드 가능</span>
                    <svg className="w-3.5 h-3.5 text-[#8c8c8c] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </>
                ) : (
                  <span className="text-[10px] text-[#3c3c3c]">○ 미생성</span>
                )}
              </button>
            );
          })}
        </div>
      </Section>
    </div>
  );
}

// ── 공통 섹션 컴포넌트 ──
function Section({
  title,
  badge,
  collapsed,
  onToggle,
  loading,
  action,
  children,
}: {
  title: string;
  badge: string;
  collapsed: boolean;
  onToggle: () => void;
  loading?: boolean;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="border-t border-[#1c1c1c]">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-xs font-medium text-[#b0b0b0] hover:text-[#ededed] transition-colors"
      >
        <svg
          className={`w-3 h-3 transition-transform ${collapsed ? "" : "rotate-90"}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span>{title}</span>
        <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-[#262626] text-[#8c8c8c]">
          {loading ? "..." : badge}
        </span>
        <span className="flex-1" />
        {action && <span onClick={(e) => e.stopPropagation()}>{action}</span>}
      </button>
      {!collapsed && <div className="pb-1">{children}</div>}
    </div>
  );
}
