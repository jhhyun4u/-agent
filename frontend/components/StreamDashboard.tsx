"use client";

/**
 * StreamDashboard — 통합현황 (합류 게이트)
 *
 * 기능:
 * - 3-스트림 진행률 큰 카드
 * - 의존성 시각화
 * - 최종 제출 버튼 (3개 스트림 모두 completed 시 활성화)
 */

import { useCallback, useEffect, useState } from "react";
import {
  streamsApi,
  type StreamsOverview,
  type StreamProgress,
} from "@/lib/api";
import StreamDependencyGraph from "@/components/StreamDependencyGraph";

interface Props {
  proposalId: string;
  deadline?: string | null;
}

const STREAM_META: Record<string, { label: string; icon: string; description: string }> = {
  proposal: {
    label: "정성제안서",
    icon: "📝",
    description: "기술제안서 AI 작성 + 자가진단 + PPT",
  },
  bidding: {
    label: "비딩관리",
    icon: "💰",
    description: "입찰가격 시뮬레이션 + 투찰 확정",
  },
  documents: {
    label: "제출서류",
    icon: "📋",
    description: "제출서류 체크리스트 준비 + 검증",
  },
};

const STATUS_COLORS: Record<string, { bar: string; bg: string; text: string; label: string }> = {
  not_started: { bar: "bg-[#404040]", bg: "bg-[#1c1c1c]", text: "text-[#8c8c8c]", label: "미시작" },
  in_progress: { bar: "bg-blue-500", bg: "bg-blue-500/5", text: "text-blue-400", label: "진행중" },
  blocked: { bar: "bg-amber-500", bg: "bg-amber-500/5", text: "text-amber-400", label: "차단됨" },
  completed: { bar: "bg-[#3ecf8e]", bg: "bg-[#3ecf8e]/5", text: "text-[#3ecf8e]", label: "완료" },
  error: { bar: "bg-red-500", bg: "bg-red-500/5", text: "text-red-400", label: "오류" },
};

// 의존성 정의
const DEPENDENCIES = [
  { target: "기술제안서 HWPX", source: "Stream 1", condition: "제안서 완료 시 생성", stream: "proposal" },
  { target: "가격제안서", source: "Stream 2", condition: "투찰가 확정 필요", stream: "bidding" },
  { target: "PPT 발표자료", source: "Stream 1", condition: "PPT 완료", stream: "proposal" },
];

function daysUntil(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  if (diff < 0) return `D+${Math.abs(diff)}`;
  return `D-${diff}`;
}

export default function StreamDashboard({ proposalId, deadline }: Props) {
  const [overview, setOverview] = useState<StreamsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<{ success: boolean; message: string } | null>(null);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    try {
      const data = await streamsApi.getAll(proposalId);
      setOverview(data);
    } catch { /* empty */ }
    finally { setLoading(false); }
  }, [proposalId]);

  useEffect(() => { fetchOverview(); }, [fetchOverview]);
  // 30초 폴링
  useEffect(() => {
    const t = setInterval(fetchOverview, 30000);
    return () => clearInterval(t);
  }, [fetchOverview]);

  async function handleFinalSubmit() {
    if (!confirm("3개 스트림이 모두 완료되었습니다. 최종 제출을 확정하시겠습니까?")) return;
    setSubmitting(true);
    try {
      const res = await streamsApi.finalSubmit(proposalId);
      setSubmitResult(res);
      if (res.success) fetchOverview();
    } catch (e) {
      setSubmitResult({ success: false, message: e instanceof Error ? e.message : "제출 실패" });
    } finally { setSubmitting(false); }
  }

  if (loading || !overview) {
    return (
      <div className="flex items-center justify-center py-12 text-[#8c8c8c] text-sm">
        불러오는 중...
      </div>
    );
  }

  const streams = overview.streams as StreamProgress[];

  function getStream(name: string): StreamProgress {
    return streams.find(s => s.stream === name) || {
      stream: name as StreamProgress["stream"],
      status: "not_started",
      progress_pct: 0,
      current_phase: null,
      blocked_reason: null,
      started_at: null,
      completed_at: null,
      metadata: {},
    };
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[#ededed]">통합 제출 현황</h2>
        {deadline && (
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
            daysUntil(deadline).startsWith("D+")
              ? "bg-red-500/15 text-red-400 border-red-500/30"
              : "bg-amber-500/15 text-amber-400 border-amber-500/30"
          }`}>
            마감: {daysUntil(deadline)}
          </span>
        )}
      </div>

      {/* 3-스트림 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {["proposal", "bidding", "documents"].map((name) => {
          const s = getStream(name);
          const meta = STREAM_META[name];
          const colors = STATUS_COLORS[s.status] || STATUS_COLORS.not_started;

          return (
            <div
              key={name}
              className={`border rounded-xl p-5 transition-colors ${colors.bg} ${
                s.status === "completed" ? "border-[#3ecf8e]/30" : "border-[#262626]"
              }`}
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">{meta.icon}</span>
                <h3 className="text-xs font-semibold text-[#ededed]">{meta.label}</h3>
              </div>

              {/* 진행바 */}
              <div className="w-full h-2.5 bg-[#262626] rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${colors.bar}`}
                  style={{ width: `${s.progress_pct}%` }}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className={`text-xs font-medium ${colors.text}`}>
                  {s.progress_pct}%
                </span>
                <span className={`text-[10px] ${colors.text}`}>
                  {colors.label}
                </span>
              </div>

              {s.current_phase && (
                <p className="text-[10px] text-[#8c8c8c] mt-1.5 truncate">
                  {s.current_phase}
                </p>
              )}
              {s.blocked_reason && (
                <p className="text-[10px] text-amber-400 mt-1">
                  차단: {s.blocked_reason}
                </p>
              )}

              <p className="text-[10px] text-[#8c8c8c] mt-2">{meta.description}</p>
            </div>
          );
        })}
      </div>

      {/* 권고 #3: 스트림 간 의존성 시각화 (기존 텍스트 + 그래프) */}
      <StreamDependencyGraph streams={streams} />

      {/* 최종 제출 버튼 */}
      <div className={`border rounded-xl p-5 text-center ${
        overview.convergence_ready
          ? "bg-[#3ecf8e]/5 border-[#3ecf8e]/30"
          : "bg-[#1c1c1c] border-[#262626]"
      }`}>
        {overview.convergence_ready ? (
          <>
            <p className="text-sm font-semibold text-[#3ecf8e] mb-3">
              3개 스트림 모두 완료 — 최종 제출 가능
            </p>
            <button
              onClick={handleFinalSubmit}
              disabled={submitting}
              className="px-6 py-2.5 text-sm font-semibold rounded-xl bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 transition-colors disabled:opacity-50"
            >
              {submitting ? "제출 중..." : "최종 제출"}
            </button>
          </>
        ) : (
          <>
            <p className="text-sm text-[#8c8c8c] mb-2">최종 제출</p>
            <p className="text-xs text-[#8c8c8c]">
              미완료 스트림: {overview.missing_streams.map(s => STREAM_META[s]?.label || s).join(", ")}
            </p>
            <button
              disabled
              className="mt-3 px-6 py-2.5 text-sm font-semibold rounded-xl bg-[#262626] text-[#8c8c8c] cursor-not-allowed"
            >
              최종 제출
            </button>
          </>
        )}

        {submitResult && (
          <div className={`mt-3 text-xs ${submitResult.success ? "text-[#3ecf8e]" : "text-red-400"}`}>
            {submitResult.message}
          </div>
        )}
      </div>
    </div>
  );
}
