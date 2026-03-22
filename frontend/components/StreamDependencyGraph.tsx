"use client";

/**
 * 권고 #3: 스트림 간 의존성 시각화
 *
 * 3-Stream(정성제안서, 비딩관리, 제출서류) 간의 의존 관계를
 * 시각적 플로우 그래프로 표시한다.
 */

import type { StreamProgress } from "@/lib/api";

interface Props {
  streams: StreamProgress[];
}

// 의존성 정의: source 스트림의 특정 이벤트 → target 스트림에 영향
const DEPENDENCY_FLOWS = [
  {
    id: "price-to-bid",
    sourceStream: "proposal",
    sourceLabel: "계획: 입찰가격 산정",
    targetStream: "bidding",
    targetLabel: "비딩: 가격 기초자료",
    description: "제안서 가격 계획에서 산정된 원가가 비딩 가격 시뮬레이션의 기초가 됩니다.",
    type: "data" as const,
  },
  {
    id: "bid-to-doc",
    sourceStream: "bidding",
    sourceLabel: "비딩: 투찰가 확정",
    targetStream: "documents",
    targetLabel: "제출: 가격제안서",
    description: "확정된 투찰 가격이 가격제안서 문서에 반영됩니다.",
    type: "data" as const,
  },
  {
    id: "proposal-to-doc",
    sourceStream: "proposal",
    sourceLabel: "제안서: HWPX 생성",
    targetStream: "documents",
    targetLabel: "제출: 기술제안서 파일",
    description: "완성된 기술제안서 HWPX/DOCX 파일이 제출서류 체크리스트에 포함됩니다.",
    type: "artifact" as const,
  },
  {
    id: "ppt-to-doc",
    sourceStream: "proposal",
    sourceLabel: "PPT: 발표자료 생성",
    targetStream: "documents",
    targetLabel: "제출: 발표자료 파일",
    description: "PPT 발표자료가 제출서류에 포함됩니다 (구두발표 시).",
    type: "artifact" as const,
  },
  {
    id: "doc-checklist",
    sourceStream: "documents",
    sourceLabel: "제출: 서류 검증 완료",
    targetStream: "bidding",
    targetLabel: "비딩: 투찰 가능",
    description: "필수 제출서류가 모두 검증되어야 투찰을 진행할 수 있습니다.",
    type: "gate" as const,
  },
];

const STREAM_INFO: Record<string, { label: string; icon: string; color: string }> = {
  proposal: { label: "정성제안서", icon: "📝", color: "#3ecf8e" },
  bidding:  { label: "비딩관리", icon: "💰", color: "#3b82f6" },
  documents:{ label: "제출서류", icon: "📋", color: "#a855f7" },
};

const TYPE_STYLE: Record<string, { color: string; label: string }> = {
  data:     { color: "text-blue-400", label: "데이터" },
  artifact: { color: "text-purple-400", label: "산출물" },
  gate:     { color: "text-amber-400", label: "게이트" },
};

export default function StreamDependencyGraph({ streams }: Props) {
  function getStreamStatus(name: string): string {
    const s = streams.find(st => st.stream === name);
    return s?.status ?? "not_started";
  }

  function isResolved(dep: typeof DEPENDENCY_FLOWS[0]): boolean {
    const sourceStatus = getStreamStatus(dep.sourceStream);
    return sourceStatus === "completed";
  }

  return (
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-5">
      <h3 className="text-xs font-medium text-[#8c8c8c] uppercase tracking-wider mb-4">
        스트림 의존성 흐름
      </h3>

      {/* 스트림 헤더 (3개) */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        {["proposal", "bidding", "documents"].map((name) => {
          const info = STREAM_INFO[name];
          const status = getStreamStatus(name);
          const isComplete = status === "completed";
          const isActive = status === "in_progress";

          return (
            <div
              key={name}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
                isComplete
                  ? "border-[#3ecf8e]/30 bg-[#3ecf8e]/5"
                  : isActive
                  ? "border-blue-500/30 bg-blue-500/5"
                  : "border-[#262626] bg-[#111111]"
              }`}
            >
              <span className="text-sm">{info.icon}</span>
              <span className="text-xs font-medium text-[#ededed]">{info.label}</span>
              <span
                className={`ml-auto w-2 h-2 rounded-full ${
                  isComplete ? "bg-[#3ecf8e]" : isActive ? "bg-blue-400 animate-pulse" : "bg-[#404040]"
                }`}
              />
            </div>
          );
        })}
      </div>

      {/* 의존성 플로우 리스트 */}
      <div className="space-y-2">
        {DEPENDENCY_FLOWS.map((dep) => {
          const resolved = isResolved(dep);
          const srcInfo = STREAM_INFO[dep.sourceStream];
          const tgtInfo = STREAM_INFO[dep.targetStream];
          const typeStyle = TYPE_STYLE[dep.type];

          return (
            <div
              key={dep.id}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors ${
                resolved
                  ? "border-[#3ecf8e]/20 bg-[#3ecf8e]/5"
                  : "border-[#262626] bg-[#111111]"
              }`}
            >
              {/* 상태 아이콘 */}
              <span className={`shrink-0 text-xs ${resolved ? "text-[#3ecf8e]" : "text-[#404040]"}`}>
                {resolved ? "●" : "○"}
              </span>

              {/* Source */}
              <div className="flex items-center gap-1.5 min-w-0">
                <span
                  className="w-1.5 h-1.5 rounded-full shrink-0"
                  style={{ backgroundColor: srcInfo.color }}
                />
                <span className="text-[10px] text-[#ededed] truncate">
                  {dep.sourceLabel}
                </span>
              </div>

              {/* 화살표 + 타입 */}
              <div className="flex items-center gap-1 shrink-0">
                <svg className="w-4 h-4 text-[#404040]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                <span className={`text-[9px] px-1.5 py-0.5 rounded border border-[#262626] ${typeStyle.color}`}>
                  {typeStyle.label}
                </span>
              </div>

              {/* Target */}
              <div className="flex items-center gap-1.5 min-w-0">
                <span
                  className="w-1.5 h-1.5 rounded-full shrink-0"
                  style={{ backgroundColor: tgtInfo.color }}
                />
                <span className="text-[10px] text-[#ededed] truncate">
                  {dep.targetLabel}
                </span>
              </div>

              {/* 설명 (호버용 타이틀) */}
              <button
                className="ml-auto shrink-0 w-4 h-4 rounded-full bg-[#262626] text-[10px] text-[#8c8c8c] hover:text-[#ededed] flex items-center justify-center"
                title={dep.description}
              >
                i
              </button>
            </div>
          );
        })}
      </div>

      {/* 범례 */}
      <div className="flex items-center gap-4 mt-4 pt-3 border-t border-[#262626]">
        {Object.entries(TYPE_STYLE).map(([key, style]) => (
          <div key={key} className="flex items-center gap-1.5">
            <span className={`text-[9px] ${style.color}`}>●</span>
            <span className="text-[10px] text-[#8c8c8c]">{style.label} 의존</span>
          </div>
        ))}
        <div className="ml-auto flex items-center gap-1.5">
          <span className="text-[9px] text-[#3ecf8e]">●</span>
          <span className="text-[10px] text-[#8c8c8c]">해소됨</span>
          <span className="text-[9px] text-[#404040] ml-2">○</span>
          <span className="text-[10px] text-[#8c8c8c]">미해소</span>
        </div>
      </div>
    </div>
  );
}
