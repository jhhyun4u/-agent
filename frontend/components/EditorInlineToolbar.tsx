"use client";

/**
 * EditorInlineToolbar — 텍스트 선택 시 나타나는 플로팅 AI 미니 툴바
 *
 * 선택 영역 위에 고정 표시. 4개 AI 액션 버튼 + 닫기.
 */

import { useEffect, useRef } from "react";

export type InlineAiMode = "improve" | "shorten" | "expand" | "formalize";

interface Props {
  rect: DOMRect;
  selectedText: string;
  loading: boolean;
  onAction: (mode: InlineAiMode) => void;
  onClose: () => void;
}

const ACTIONS: { mode: InlineAiMode; label: string; icon: string }[] = [
  { mode: "improve",   label: "개선",   icon: "✨" },
  { mode: "shorten",   label: "축약",   icon: "⬇" },
  { mode: "expand",    label: "확장",   icon: "⬆" },
  { mode: "formalize", label: "공식화", icon: "📝" },
];

export default function EditorInlineToolbar({
  rect,
  selectedText,
  loading,
  onAction,
  onClose,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);

  // 툴바 위치: 선택 영역 위 중앙
  const top  = rect.top + window.scrollY - 44;
  const left = rect.left + window.scrollX + rect.width / 2;

  // 외부 클릭 시 닫기
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  return (
    <div
      ref={ref}
      style={{ top, left, transform: "translateX(-50%)" }}
      className="fixed z-50 flex items-center gap-0.5 px-1.5 py-1 rounded-xl bg-[#1c1c1c] border border-[#3ecf8e]/30 shadow-xl shadow-black/40"
    >
      {/* 선택 텍스트 미리보기 */}
      <span className="text-[9px] text-[#5c5c5c] max-w-[80px] truncate pr-1 border-r border-[#262626]">
        "{selectedText.slice(0, 20)}{selectedText.length > 20 ? "…" : ""}"
      </span>

      {/* AI 액션 버튼들 */}
      {ACTIONS.map(({ mode, label, icon }) => (
        <button
          key={mode}
          onClick={() => onAction(mode)}
          disabled={loading}
          title={label}
          className={`flex items-center gap-0.5 px-2 py-1 rounded-lg text-[10px] font-medium transition-colors
            ${loading
              ? "text-[#5c5c5c] cursor-not-allowed"
              : "text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626]"
            }`}
        >
          <span>{icon}</span>
          <span>{label}</span>
        </button>
      ))}

      {/* 로딩 스피너 */}
      {loading && (
        <span className="ml-1 w-3.5 h-3.5 border-2 border-[#3ecf8e]/30 border-t-[#3ecf8e] rounded-full animate-spin" />
      )}

      {/* 닫기 */}
      {!loading && (
        <button
          onClick={onClose}
          className="ml-0.5 pl-1 border-l border-[#262626] text-[#5c5c5c] hover:text-[#ededed] text-xs leading-none"
        >
          ×
        </button>
      )}
    </div>
  );
}
