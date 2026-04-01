"use client";

/**
 * VersionCompareModal — 전체화면 버전 비교 (Side-by-side diff)
 */

import { useCallback, useEffect, useState } from "react";
import { api, type ProposalSummary } from "@/lib/api";

interface VersionCompareModalProps {
  open: boolean;
  onClose: () => void;
  proposalId: string;
  versions: ProposalSummary[];
  currentVersionLabel: string;
}

/** HTML 태그 제거 */
function stripHtml(html: string): string {
  if (typeof document !== "undefined") {
    const div = document.createElement("div");
    div.innerHTML = html;
    return div.textContent || div.innerText || "";
  }
  return html.replace(/<[^>]*>/g, "");
}

/** 줄 단위 diff */
function lineDiff(
  a: string,
  b: string,
): Array<{ type: "same" | "add" | "del"; text: string }> {
  const aLines = a.split("\n");
  const bLines = b.split("\n");
  const result: Array<{ type: "same" | "add" | "del"; text: string }> = [];

  const maxLen = Math.max(aLines.length, bLines.length);
  for (let i = 0; i < maxLen; i++) {
    const al = aLines[i];
    const bl = bLines[i];
    if (al === bl) {
      if (al !== undefined) result.push({ type: "same", text: al });
    } else {
      if (al !== undefined) result.push({ type: "del", text: al });
      if (bl !== undefined) result.push({ type: "add", text: bl });
    }
  }
  return result;
}

export default function VersionCompareModal({
  open,
  onClose,
  proposalId,
  versions,
  currentVersionLabel,
}: VersionCompareModalProps) {
  const [versionA, setVersionA] = useState<string>("");
  const [versionB, setVersionB] = useState<string>(proposalId);
  const [contentA, setContentA] = useState("");
  const [contentB, setContentB] = useState("");
  const [loading, setLoading] = useState(false);

  const loadContent = useCallback(async (id: string): Promise<string> => {
    try {
      const result = await api.artifacts.get(id, "proposal");
      const data = result.data as Record<string, unknown>;
      return (data.html_content as string) ?? (data.content as string) ?? "";
    } catch {
      return "(내용 없음)";
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    Promise.all([
      versionA ? loadContent(versionA) : Promise.resolve("(버전 선택)"),
      loadContent(versionB),
    ])
      .then(([a, b]) => {
        setContentA(stripHtml(a));
        setContentB(stripHtml(b));
      })
      .finally(() => setLoading(false));
  }, [open, versionA, versionB, loadContent]);

  if (!open) return null;

  const diffs = lineDiff(contentA, contentB);

  return (
    <div
      className="fixed inset-0 bg-[#0f0f0f]/80 flex items-center justify-center"
      style={{ zIndex: "var(--z-modal, 60)" }}
      onClick={onClose}
    >
      <div
        className="bg-[#1c1c1c] border border-[#262626] rounded-xl w-[90vw] h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[#262626] shrink-0">
          <h2 className="text-sm font-semibold text-[#ededed]">버전 비교</h2>
          <div className="flex items-center gap-3">
            <select
              value={versionA}
              onChange={(e) => setVersionA(e.target.value)}
              className="bg-[#111111] border border-[#262626] rounded px-2 py-1 text-[10px] text-[#ededed]"
            >
              <option value="">이전 버전 선택</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.title || v.id}
                </option>
              ))}
            </select>
            <span className="text-[10px] text-[#5c5c5c]">vs</span>
            <span className="text-[10px] text-[#8c8c8c]">
              {currentVersionLabel || "현재"}
            </span>
            <button
              onClick={onClose}
              className="text-[#8c8c8c] hover:text-[#ededed] ml-4 transition-colors"
              aria-label="닫기"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Diff 본문 */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full text-[#8c8c8c] text-sm">
              <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
              불러오는 중...
            </div>
          ) : (
            <div className="font-mono text-xs leading-relaxed space-y-0">
              {diffs.map((d, i) => (
                <div
                  key={i}
                  className={`px-3 py-0.5 ${
                    d.type === "add"
                      ? "bg-green-500/10 text-green-300"
                      : d.type === "del"
                        ? "bg-red-500/10 text-red-400"
                        : "text-[#8c8c8c]"
                  }`}
                >
                  <span className="inline-block w-4 text-[#5c5c5c] select-none">
                    {d.type === "add" ? "+" : d.type === "del" ? "-" : " "}
                  </span>
                  {d.text || "\u00A0"}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
