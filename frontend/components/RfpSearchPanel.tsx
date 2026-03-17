"use client";

/**
 * RfpSearchPanel — STEP 0 공고 검색/선정 전용 패널 (§13-2)
 *
 * WorkflowPanel에서 분리된 STEP 0 전용 컴포넌트.
 * 검색 결과 표시 + 관심과제 선정 + 재검색/종료 액션.
 */

import { useState } from "react";
import { api, type WorkflowState, type WorkflowResumeData } from "@/lib/api";

interface RfpSearchPanelProps {
  proposalId: string;
  workflowState: WorkflowState;
  onStateChange?: () => void;
  className?: string;
}

export default function RfpSearchPanel({
  proposalId,
  workflowState,
  onStateChange,
  className = "",
}: RfpSearchPanelProps) {
  const [selectedBid, setSelectedBid] = useState("");
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handlePick() {
    if (!selectedBid) return;
    setSubmitting(true);
    try {
      const data: WorkflowResumeData = {
        approved: true,
        picked_bid_no: selectedBid,
        feedback: feedback || undefined,
      };
      await api.workflow.resume(proposalId, data);
      onStateChange?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "요청 실패");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReSearch() {
    setSubmitting(true);
    try {
      const data: WorkflowResumeData = {
        approved: false,
        search_query: {},
        feedback: feedback || undefined,
      };
      await api.workflow.resume(proposalId, data);
      onStateChange?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "요청 실패");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleNoInterest() {
    setSubmitting(true);
    try {
      const data: WorkflowResumeData = {
        approved: false,
        no_interest: true,
        reason: feedback || "관심 과제 없음",
      };
      await api.workflow.resume(proposalId, data);
      onStateChange?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "요청 실패");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className={`bg-[#1c1c1c] rounded-2xl border border-blue-500/30 p-5 ${className}`}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
        <h2 className="text-sm font-semibold text-[#ededed]">
          공고 검색 결과 검토
        </h2>
        <span className="text-[10px] text-blue-400/80 bg-blue-500/10 px-2 py-0.5 rounded">
          STEP 0
        </span>
      </div>

      <p className="text-xs text-[#8c8c8c] mb-4">
        검색된 공고 중 관심 과제를 선택하세요.
      </p>

      {/* 공고 번호 입력 */}
      <div className="mb-4">
        <label className="text-[10px] text-[#8c8c8c] mb-1.5 block uppercase tracking-wider">
          선정 공고 번호
        </label>
        <input
          type="text"
          value={selectedBid}
          onChange={(e) => setSelectedBid(e.target.value)}
          placeholder="나라장터 공고번호 입력"
          className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-xs text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-blue-500/40"
        />
      </div>

      {/* 메모 */}
      <div className="mb-4">
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="메모 (선택)"
          rows={2}
          className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-xs text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-blue-500/40 resize-none"
        />
      </div>

      {/* 버튼 */}
      <div className="flex gap-2">
        <button
          onClick={handleNoInterest}
          disabled={submitting}
          className="px-3 py-2.5 text-xs font-medium rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 disabled:opacity-40 transition-colors"
        >
          관심 없음
        </button>
        <button
          onClick={handleReSearch}
          disabled={submitting}
          className="px-3 py-2.5 text-xs font-medium rounded-lg border border-[#262626] text-[#8c8c8c] hover:bg-[#262626] disabled:opacity-40 transition-colors"
        >
          재검색
        </button>
        <button
          onClick={handlePick}
          disabled={submitting || !selectedBid}
          className="flex-1 py-2.5 text-xs font-bold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 disabled:opacity-40 transition-colors"
        >
          이 과제 선정
        </button>
      </div>
    </div>
  );
}
