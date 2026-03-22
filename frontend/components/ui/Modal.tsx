"use client";

/**
 * Modal — 공통 모달 컴포넌트
 */

import { useEffect } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl" | "full";
}

const SIZES = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
  full: "w-[90vw]",
} as const;

export default function Modal({ open, onClose, title, children, size = "md" }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-[#0f0f0f]/80 backdrop-blur-sm flex items-center justify-center p-4"
      style={{ zIndex: "var(--z-modal, 60)" }}
      onClick={onClose}
    >
      <div
        className={`bg-[var(--card,#1c1c1c)] border border-[var(--border,#262626)] rounded-xl ${SIZES[size]} w-full max-h-[85vh] overflow-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--border,#262626)]">
            <h2 className="text-sm font-semibold text-[var(--text,#ededed)]">{title}</h2>
            <button
              onClick={onClose}
              className="text-[var(--muted,#8c8c8c)] hover:text-[var(--text,#ededed)] transition-colors"
              aria-label="닫기"
            >
              ✕
            </button>
          </div>
        )}
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
