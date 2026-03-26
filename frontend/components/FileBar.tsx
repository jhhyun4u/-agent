"use client";

/**
 * FileBar — 상단 파일 바
 *
 * 프로젝트 관련 모든 파일(첨부 + AI 산출물)을 가로 스크롤 칩으로 표시.
 * 클릭 시 우측 패널에 열리거나 다운로드.
 */

import { useEffect, useState } from "react";
import { api, type ProposalFile } from "@/lib/api";

// ── 산출물 정의 ──

const ARTIFACT_DOCS = [
  // 공통
  { key: "search_results",  label: "공고 검색",     icon: "S",  color: "text-blue-400 bg-blue-500/15",       step: 0 },
  { key: "rfp_analyze",     label: "RFP 분석",      icon: "R",  color: "text-purple-400 bg-purple-500/15",   step: 0 },
  { key: "research_gather", label: "리서치",         icon: "L",  color: "text-cyan-400 bg-cyan-500/15",       step: 0 },
  { key: "go_no_go",        label: "Go/No-Go",      icon: "G",  color: "text-emerald-400 bg-emerald-500/15", step: 0 },
  { key: "strategy",        label: "전략기획",       icon: "W",  color: "text-amber-400 bg-amber-500/15",     step: 1 },
  // Path A: 제안서
  { key: "plan",            label: "제안 계획",      icon: "P",  color: "text-cyan-400 bg-cyan-500/15",       step: 2 },
  { key: "proposal",        label: "제안서",         icon: "D",  color: "text-blue-400 bg-blue-500/15",       step: 3 },
  { key: "self_review",     label: "자가진단",       icon: "Q",  color: "text-orange-400 bg-orange-500/15",   step: 3 },
  { key: "ppt_storyboard",  label: "PPT",             icon: "T",  color: "text-indigo-400 bg-indigo-500/15",   step: 4 },
  { key: "mock_evaluation", label: "모의 평가",       icon: "E",  color: "text-violet-400 bg-violet-500/15",   step: 5 },
  // Path B: 입찰·제출
  { key: "submission_plan",     label: "제출서류 계획", icon: "F",  color: "text-pink-400 bg-pink-500/15",     step: 6 },
  { key: "bid_plan",            label: "입찰가 결정",   icon: "$",  color: "text-amber-400 bg-amber-500/15",   step: 7 },
  { key: "cost_sheet",          label: "산출내역서",    icon: "C",  color: "text-green-400 bg-green-500/15",   step: 8 },
  { key: "submission_checklist", label: "제출서류 확인", icon: "V",  color: "text-teal-400 bg-teal-500/15",    step: 9 },
  // Tail: 통합
  { key: "eval_result",     label: "평가결과",        icon: "7",  color: "text-rose-400 bg-rose-500/15",       step: 10 },
  { key: "project_closing", label: "Closing",          icon: "8",  color: "text-[#8c8c8c] bg-[#262626]",      step: 11 },
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
  return "text-[#8c8c8c] bg-[#262626]";
}

// ── Props ──

interface FileBarProps {
  proposalId: string;
  phasesCompleted: number;
  activeDocId?: string | null;
  onSelectArtifact: (stepIndex: number, artifactKey: string) => void;
  onSelectFile: (file: ProposalFile) => void;
}

export default function FileBar({
  proposalId,
  phasesCompleted,
  activeDocId,
  onSelectArtifact,
  onSelectFile,
}: FileBarProps) {
  const [files, setFiles] = useState<ProposalFile[]>([]);
  const [availableArtifacts, setAvailableArtifacts] = useState<Set<string>>(new Set());

  // 파일 로드
  useEffect(() => {
    api.proposals.listFiles(proposalId).then((r) => setFiles(r.files)).catch(() => {});
  }, [proposalId]);

  // 산출물 존재 여부
  useEffect(() => {
    const check = async () => {
      const avail = new Set<string>();
      for (const d of ARTIFACT_DOCS) {
        try { await api.artifacts.get(proposalId, d.key); avail.add(d.key); } catch {}
      }
      setAvailableArtifacts(avail);
    };
    check();
  }, [proposalId, phasesCompleted]);

  const hasAnyContent = files.length > 0 || availableArtifacts.size > 0;
  if (!hasAnyContent) return null;

  return (
    <div className="px-4 py-1.5 overflow-hidden">
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
        {/* 첨부 파일 */}
        {files.map((f) => (
          <button
            key={f.id}
            onClick={() => onSelectFile(f)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium shrink-0 border transition-colors ${
              activeDocId === `file-${f.id}`
                ? "bg-[#3ecf8e]/10 border-[#3ecf8e]/30 text-[#ededed]"
                : "border-[#262626] text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3c3c3c]"
            }`}
            title={f.filename}
          >
            <span className={`w-4 h-4 rounded flex items-center justify-center text-[8px] font-bold ${fileColor(f.file_type ?? undefined)}`}>
              {(f.file_type || "?").slice(0, 2).toUpperCase()}
            </span>
            <span className="max-w-[100px] truncate">{f.filename.replace(/\.[^.]+$/, "")}</span>
          </button>
        ))}

        {/* 구분선 */}
        {files.length > 0 && availableArtifacts.size > 0 && (
          <div className="w-px h-5 bg-[#333] shrink-0 mx-0.5" />
        )}

        {/* AI 산출물 */}
        {ARTIFACT_DOCS.map((d) => {
          const avail = availableArtifacts.has(d.key);
          return (
            <button
              key={d.key}
              onClick={() => avail && onSelectArtifact(d.step, d.key)}
              disabled={!avail}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium shrink-0 border transition-colors ${
                !avail
                  ? "border-transparent text-[#3c3c3c] cursor-default"
                  : activeDocId === `artifact-${d.key}`
                  ? "bg-[#3ecf8e]/10 border-[#3ecf8e]/30 text-[#ededed]"
                  : "border-[#262626] text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3c3c3c]"
              }`}
              title={avail ? d.label : `${d.label} (미생성)`}
            >
              <span className={`w-4 h-4 rounded flex items-center justify-center text-[8px] font-bold ${avail ? d.color : "text-[#3c3c3c] bg-[#1a1a1a]"}`}>
                {d.icon}
              </span>
              {d.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
