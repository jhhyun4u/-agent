"use client";

/**
 * StreamTabBar — 4개 탭 전환 (정성제안서 / 비딩관리 / 제출서류 / 통합현황)
 *
 * 각 탭에 스트림 상태 뱃지 표시.
 */

interface StreamInfo {
  stream: string;
  status: string;
  progress_pct: number;
}

export type StreamTab = "proposal" | "bidding" | "documents" | "overview";

interface Props {
  activeTab: StreamTab;
  onTabChange: (tab: StreamTab) => void;
  streams: StreamInfo[];
}

const TABS: { key: StreamTab; label: string; stream?: string }[] = [
  { key: "proposal", label: "정성제안서", stream: "proposal" },
  { key: "bidding", label: "비딩관리", stream: "bidding" },
  { key: "documents", label: "제출서류", stream: "documents" },
  { key: "overview", label: "통합현황" },
];

const STATUS_BADGE: Record<string, { color: string; label: string }> = {
  not_started: { color: "bg-[#404040] text-[#8c8c8c]", label: "미시작" },
  in_progress: { color: "bg-blue-500/20 text-blue-400", label: "진행중" },
  blocked: { color: "bg-amber-500/20 text-amber-400", label: "차단" },
  completed: { color: "bg-[#3ecf8e]/20 text-[#3ecf8e]", label: "완료" },
  error: { color: "bg-red-500/20 text-red-400", label: "오류" },
};

export default function StreamTabBar({ activeTab, onTabChange, streams }: Props) {
  function getStreamStatus(streamName?: string): StreamInfo | null {
    if (!streamName) return null;
    return streams.find((s) => s.stream === streamName) || null;
  }

  return (
    <div className="flex items-center gap-1 border-b border-[#262626] bg-[#111111] px-4">
      {TABS.map(({ key, label, stream }) => {
        const isActive = activeTab === key;
        const streamData = getStreamStatus(stream);
        const badge = streamData ? STATUS_BADGE[streamData.status] || STATUS_BADGE.not_started : null;

        return (
          <button
            key={key}
            onClick={() => onTabChange(key)}
            className={`
              relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors
              ${isActive
                ? "text-[#ededed] border-b-2 border-[#3ecf8e]"
                : "text-[#8c8c8c] hover:text-[#ededed] border-b-2 border-transparent"
              }
            `}
          >
            {label}
            {badge && (
              <span className={`inline-flex px-1.5 py-0.5 rounded text-[9px] font-medium ${badge.color}`}>
                {streamData!.progress_pct > 0 && streamData!.status !== "completed"
                  ? `${streamData!.progress_pct}%`
                  : badge.label
                }
              </span>
            )}
            {key === "overview" && (
              <span className="inline-flex px-1.5 py-0.5 rounded text-[9px] font-medium bg-[#262626] text-[#8c8c8c]">
                합류
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
