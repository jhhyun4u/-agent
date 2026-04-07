"use client";

/**
 * ThemeToggle — 라이트/다크 모드 전환 버튼
 */

import { useEffect, useState } from "react";

interface ThemeToggleProps {
  collapsed?: boolean;
}

export default function ThemeToggle({ collapsed }: ThemeToggleProps) {
  const [isLight, setIsLight] = useState(false);

  useEffect(() => {
    setIsLight(document.documentElement.classList.contains("light"));
  }, []);

  function toggle() {
    const next = !isLight;
    setIsLight(next);
    if (next) {
      document.documentElement.classList.add("light");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.classList.remove("light");
      localStorage.setItem("theme", "dark");
    }
  }

  return (
    <button
      onClick={toggle}
      className={`flex items-center ${collapsed ? "justify-center" : "gap-2.5"} px-3 py-2 rounded-md text-sm text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors`}
      title={isLight ? "다크 모드로 전환" : "라이트 모드로 전환"}
      aria-label={isLight ? "다크 모드" : "라이트 모드"}
    >
      <span className="text-base shrink-0">
        {isLight ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
      </span>
      {!collapsed && <span>{isLight ? "다크 모드" : "라이트 모드"}</span>}
    </button>
  );
}
