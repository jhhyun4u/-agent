"use client";

/**
 * EditorTocPanel — 좌측 목차 + Compliance Matrix (§13-10)
 *
 * - 섹션 트리 (클릭 시 에디터 스크롤)
 * - Compliance Matrix 상태 표시
 */

import type { ComplianceItem } from "@/lib/api";

// ── 섹션 타입 ──

export interface TocSection {
  id: string;
  title: string;
  level: number;
}

interface EditorTocPanelProps {
  sections: TocSection[];
  activeSection: string | null;
  onSectionClick: (sectionId: string) => void;
  complianceItems: ComplianceItem[];
  className?: string;
}

export default function EditorTocPanel({
  sections,
  activeSection,
  onSectionClick,
  complianceItems,
  className = "",
}: EditorTocPanelProps) {
  const met = complianceItems.filter((i) => i.status === "met").length;
  const partial = complianceItems.filter((i) => i.status === "partial").length;
  const notMet = complianceItems.filter((i) => i.status === "not_met").length;
  const total = complianceItems.length;
  const progressRate = total > 0 ? Math.round(((met + partial * 0.5) / total) * 100) : 0;

  return (
    <div className={`flex flex-col h-full overflow-hidden ${className}`}>
      {/* Compliance 요약 */}
      {total > 0 && (
        <div className="px-3 py-2.5 border-b border-[#262626]">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium">
              Compliance
            </span>
            <span className={`text-xs font-bold ${
              progressRate >= 80 ? "text-[#3ecf8e]" : progressRate >= 60 ? "text-amber-400" : "text-red-400"
            }`}>
              {progressRate}%
            </span>
          </div>
          <div className="h-1.5 bg-[#262626] rounded-full overflow-hidden mb-1.5">
            <div
              className={`h-full rounded-full transition-all ${
                progressRate >= 80 ? "bg-[#3ecf8e]" : progressRate >= 60 ? "bg-amber-500" : "bg-red-500"
              }`}
              style={{ width: `${progressRate}%` }}
            />
          </div>
          <div className="flex gap-2 text-[9px]">
            <span className="text-[#3ecf8e]">{met} 충족</span>
            <span className="text-amber-400">{partial} 부분</span>
            <span className="text-red-400">{notMet} 미충족</span>
          </div>
        </div>
      )}

      {/* 목차 */}
      <div className="flex-1 overflow-y-auto">
        <h3 className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium px-3 py-2">
          목차
        </h3>
        <nav className="space-y-0.5 px-1">
          {sections.map((sec) => (
            <button
              key={sec.id}
              onClick={() => onSectionClick(sec.id)}
              className={`w-full text-left px-2 py-1.5 rounded-lg text-xs transition-colors ${
                activeSection === sec.id
                  ? "bg-[#3ecf8e]/15 text-[#3ecf8e] font-medium"
                  : "text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626]"
              }`}
              style={{ paddingLeft: `${8 + (sec.level - 1) * 12}px` }}
            >
              {sec.title}
            </button>
          ))}
          {sections.length === 0 && (
            <p className="px-3 py-2 text-[10px] text-[#5c5c5c]">섹션 없음</p>
          )}
        </nav>
      </div>

      {/* Compliance Matrix */}
      {complianceItems.length > 0 && (
        <div className="border-t border-[#262626] overflow-y-auto max-h-[40%]">
          <h3 className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium px-3 py-2 sticky top-0 bg-[#1c1c1c]">
            Compliance Matrix
          </h3>
          <div className="space-y-0.5 px-1 pb-2">
            {complianceItems.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center gap-1.5 px-2 py-1 text-[10px]"
              >
                <span>
                  {item.status === "met"
                    ? "✅"
                    : item.status === "partial"
                    ? "⚠️"
                    : item.status === "not_met"
                    ? "❌"
                    : "⏳"}
                </span>
                <span
                  className={`truncate ${
                    item.status === "met"
                      ? "text-[#8c8c8c]"
                      : item.status === "partial"
                      ? "text-amber-400"
                      : item.status === "not_met"
                      ? "text-red-400"
                      : "text-[#5c5c5c]"
                  }`}
                  title={item.requirement}
                >
                  {item.requirement}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
