"use client";

/**
 * KeyboardShortcutsGuide — 단축키 가이드 오버레이
 * Ctrl+/ 또는 ? 키로 토글
 */

interface KeyboardShortcutsGuideProps {
  open: boolean;
  onClose: () => void;
}

const SHORTCUTS = [
  { keys: ["Ctrl", "S"], desc: "즉시 저장" },
  { keys: ["Ctrl", "Z"], desc: "실행 취소" },
  { keys: ["Ctrl", "Y"], desc: "다시 실행" },
  { keys: ["Ctrl", "Enter"], desc: "AI 제안 전송" },
  { keys: ["Ctrl", "/"], desc: "단축키 가이드 열기/닫기" },
  { keys: ["Escape"], desc: "패널 닫기" },
] as const;

export default function KeyboardShortcutsGuide({
  open,
  onClose,
}: KeyboardShortcutsGuideProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-[#0f0f0f]/80 backdrop-blur-sm flex items-start justify-center pt-24"
      style={{ zIndex: "var(--z-modal, 60)" }}
      onClick={onClose}
    >
      <div
        className="bg-[#1c1c1c] border border-[#262626] rounded-xl max-w-sm w-full mx-4 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-[#ededed]">
            키보드 단축키
          </h2>
          <button
            onClick={onClose}
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
            aria-label="닫기"
          >
            ✕
          </button>
        </div>

        <div className="space-y-2">
          {SHORTCUTS.map(({ keys, desc }) => (
            <div key={desc} className="flex items-center justify-between py-1">
              <span className="text-xs text-[#8c8c8c]">{desc}</span>
              <div className="flex items-center gap-1">
                {keys.map((key) => (
                  <kbd
                    key={key}
                    className="inline-block px-1.5 py-0.5 bg-[#262626] border border-[#3a3a3a] rounded text-[10px] font-mono text-[#ededed] min-w-[24px] text-center"
                  >
                    {key}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>

        <p className="mt-4 text-[9px] text-[#5c5c5c]">
          Mac에서는 Ctrl 대신 Cmd 사용
        </p>
      </div>
    </div>
  );
}
