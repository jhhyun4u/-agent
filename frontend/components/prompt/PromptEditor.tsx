"use client";

/**
 * PromptEditor — 프롬프트 텍스트 편집기
 *
 * - {variable} 변수 하이라이트 (오버레이 방식)
 * - 실시간 토큰 카운터
 * - 변수 목록 표시
 */

import { useMemo, useRef } from "react";

interface PromptEditorProps {
  value: string;
  onChange: (text: string) => void;
  readOnly?: boolean;
  height?: string;
}

export default function PromptEditor({
  value,
  onChange,
  readOnly = false,
  height = "h-96",
}: PromptEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const tokenEstimate = useMemo(
    () => Math.max(1, Math.round(value.length / 2)),
    [value],
  );

  const variables = useMemo(
    () => [...new Set((value.match(/\{(\w+)\}/g) ?? []).map((v) => v))],
    [value],
  );

  const highlighted = useMemo(() => {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(
        /\{(\w+)\}/g,
        '<mark class="bg-blue-500/20 text-[#60a5fa] rounded px-0.5">{$1}</mark>',
      );
  }, [value]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold">프롬프트 편집</h3>
        <span className="text-xs text-[#8c8c8c]">~{tokenEstimate.toLocaleString()} 토큰</span>
      </div>

      {/* 편집 영역 (하이라이트 오버레이) */}
      <div className="relative">
        {/* 하이라이트 백드롭 */}
        <div
          className={`absolute inset-0 ${height} bg-[#0a0a0a] rounded-lg p-3 text-xs font-mono overflow-auto whitespace-pre-wrap break-words pointer-events-none border border-transparent`}
          dangerouslySetInnerHTML={{ __html: highlighted + "\n" }}
          aria-hidden
        />
        {/* 실제 textarea (투명) */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          readOnly={readOnly}
          className={`relative w-full ${height} bg-transparent rounded-lg p-3 text-xs font-mono text-transparent caret-[#ededed] border border-[#262626] focus:border-[#3ecf8e] focus:outline-none resize-none`}
          spellCheck={false}
        />
      </div>

      {/* 변수 목록 */}
      {variables.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <span className="text-xs text-[#8c8c8c]">변수:</span>
          {variables.map((v) => (
            <span
              key={v}
              className="text-xs font-mono text-[#60a5fa] bg-[#60a5fa]/10 px-2 py-0.5 rounded"
            >
              {v}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
