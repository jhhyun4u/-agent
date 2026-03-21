"use client";

/**
 * StreamProgressHeader — 3-스트림 미니 진행바 (항상 노출)
 *
 * 색상: 회색(미시작) → 파랑(진행) → 황색(차단) → 초록+체크(완료)
 * 클릭 시 해당 탭으로 전환.
 */

interface StreamInfo {
  stream: string;
  status: string;
  progress_pct: number;
  current_phase?: string | null;
}

interface Props {
  streams: StreamInfo[];
  onStreamClick?: (stream: string) => void;
}

const STREAM_LABELS: Record<string, string> = {
  proposal: "제안서",
  bidding: "비딩",
  documents: "서류",
};

const STATUS_COLORS: Record<string, { bar: string; text: string; bg: string }> = {
  not_started: { bar: "bg-[#404040]", text: "text-[#8c8c8c]", bg: "bg-[#262626]" },
  in_progress: { bar: "bg-blue-500", text: "text-blue-400", bg: "bg-blue-500/10" },
  blocked: { bar: "bg-amber-500", text: "text-amber-400", bg: "bg-amber-500/10" },
  completed: { bar: "bg-[#3ecf8e]", text: "text-[#3ecf8e]", bg: "bg-[#3ecf8e]/10" },
  error: { bar: "bg-red-500", text: "text-red-400", bg: "bg-red-500/10" },
};

function getColors(status: string) {
  return STATUS_COLORS[status] || STATUS_COLORS.not_started;
}

export default function StreamProgressHeader({ streams, onStreamClick }: Props) {
  if (!streams || streams.length === 0) return null;

  return (
    <div className="flex items-center gap-3">
      <span className="text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium">Stream</span>
      {["proposal", "bidding", "documents"].map((name) => {
        const s = streams.find((x) => x.stream === name) || {
          stream: name,
          status: "not_started",
          progress_pct: 0,
        };
        const colors = getColors(s.status);
        const pct = s.progress_pct || 0;

        return (
          <button
            key={name}
            onClick={() => onStreamClick?.(name)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-md ${colors.bg} hover:opacity-80 transition-opacity`}
            title={`${STREAM_LABELS[name]}: ${s.status} (${pct}%)`}
          >
            {/* 미니 진행바 */}
            <div className="w-10 h-1.5 bg-[#262626] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${colors.bar}`}
                style={{ width: `${Math.max(pct, s.status === "not_started" ? 0 : 5)}%` }}
              />
            </div>
            <span className={`text-[10px] font-medium ${colors.text}`}>
              {STREAM_LABELS[name]}
            </span>
            {s.status === "completed" && (
              <svg className="w-3 h-3 text-[#3ecf8e]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            )}
            {s.status === "blocked" && (
              <svg className="w-3 h-3 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </button>
        );
      })}
    </div>
  );
}
