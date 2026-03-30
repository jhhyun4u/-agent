"use client";

/**
 * AiSuggestionDiff — AI 제안과 원본 텍스트의 인라인 diff 표시
 * diff-match-patch 라이브러리 사용
 */

import { useMemo } from "react";

interface AiSuggestionDiffProps {
  original: string;
  suggestion: string;
  explanation?: string;
  onAccept: () => void;
  onReject: () => void;
}

/** 간단한 문장 단위 diff (diff-match-patch 없이 동작하는 폴백) */
function computeSimpleDiff(original: string, suggestion: string): Array<[number, string]> {
  // 줄 단위 비교
  const origLines = original.split("\n");
  const suggLines = suggestion.split("\n");
  const result: Array<[number, string]> = [];

  const maxLen = Math.max(origLines.length, suggLines.length);
  for (let i = 0; i < maxLen; i++) {
    const o = origLines[i];
    const s = suggLines[i];
    if (o === s) {
      if (o !== undefined) result.push([0, o + "\n"]);
    } else {
      if (o !== undefined) result.push([-1, o + "\n"]);
      if (s !== undefined) result.push([1, s + "\n"]);
    }
  }
  return result;
}

/** HTML 태그를 제거하고 텍스트만 추출 */
function stripHtml(html: string): string {
  if (typeof document !== "undefined") {
    const div = document.createElement("div");
    div.innerHTML = html;
    return div.textContent || div.innerText || "";
  }
  return html.replace(/<[^>]*>/g, "");
}

export default function AiSuggestionDiff({
  original,
  suggestion,
  explanation,
  onAccept,
  onReject,
}: AiSuggestionDiffProps) {
  const diffs = useMemo(() => {
    const origText = stripHtml(original).trim();
    const suggText = stripHtml(suggestion).trim();

    // diff-match-patch가 있으면 사용, 없으면 폴백
    try {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const DiffMatchPatch = require("diff-match-patch");
      const dmp = new DiffMatchPatch();
      const d = dmp.diff_main(origText, suggText);
      dmp.diff_cleanupSemantic(d);
      return d as Array<[number, string]>;
    } catch {
      return computeSimpleDiff(origText, suggText);
    }
  }, [original, suggestion]);

  const hasChanges = diffs.some(([op]) => op !== 0);

  return (
    <div className="bg-[#111111] border border-[#3ecf8e]/20 rounded-lg px-2.5 py-2 space-y-2">
      {explanation && (
        <p className="text-[10px] text-[#8c8c8c]">{explanation}</p>
      )}

      {hasChanges ? (
        <div className="text-[10px] leading-relaxed max-h-40 overflow-y-auto whitespace-pre-wrap font-mono">
          {diffs.map(([op, text], i) => (
            <span
              key={i}
              className={
                op === 1
                  ? "bg-green-500/20 text-green-300"
                  : op === -1
                  ? "bg-red-500/20 text-red-400 line-through"
                  : "text-[#8c8c8c]"
              }
            >
              {text}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-[10px] text-[#5c5c5c]">변경사항 없음</p>
      )}

      <div className="flex gap-2">
        <button
          onClick={onAccept}
          className="px-3 py-1 text-[10px] font-semibold rounded bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 transition-colors"
        >
          수락
        </button>
        <button
          onClick={onReject}
          className="px-3 py-1 text-[10px] font-medium rounded border border-[#262626] text-[#8c8c8c] hover:bg-[#262626] transition-colors"
        >
          거부
        </button>
      </div>
    </div>
  );
}
