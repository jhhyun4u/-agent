"use client";

/**
 * WorkflowLogPanel — SSE 기반 실시간 노드 실행 로그 (터미널 스타일)
 */

import { useEffect, useRef } from "react";
import type { StreamEvent } from "@/lib/hooks/useWorkflowStream";

// 노드명 → 한글 라벨 매핑
const NODE_LABELS: Record<string, string> = {
  rfp_search: "공고 검색",
  rfp_fetch: "공고 상세 수집",
  rfp_analyze: "RFP 분석",
  research_gather: "선행 리서치",
  go_no_go: "Go/No-Go 판정",
  strategy_generate: "전략 수립",
  plan_team: "팀 구성",
  plan_assign: "역할 배분",
  plan_schedule: "일정 수립",
  plan_story: "스토리라인 설계",
  plan_price: "예산 산정",
  plan_merge: "계획 통합",
  proposal_write_next: "섹션 작성",
  self_review: "자가진단",
  presentation_strategy: "발표 전략",
  ppt_toc: "PPT 목차",
  ppt_visual_brief: "시각 설계",
  ppt_storyboard: "슬라이드 작성",
  review_search: "검색 결과 검토",
  review_rfp: "RFP 분석 검토",
  review_gng: "Go/No-Go 검토",
  review_strategy: "전략 검토",
  review_plan: "계획 검토",
  review_section: "섹션 검토",
  review_proposal: "제안서 최종 검토",
  review_ppt: "PPT 검토",
};

interface WorkflowLogPanelProps {
  events: StreamEvent[];
  isStreaming: boolean;
  collapsed?: boolean;
  onToggle?: () => void;
  className?: string;
}

export default function WorkflowLogPanel({
  events,
  isStreaming,
  collapsed = false,
  onToggle,
  className = "",
}: WorkflowLogPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // 자동 스크롤
  useEffect(() => {
    if (scrollRef.current && !collapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events.length, collapsed]);

  return (
    <div className={`bg-[#111111] border border-[#262626] rounded-xl overflow-hidden ${className}`}>
      {/* 헤더 */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-2 bg-[#1c1c1c] hover:bg-[#222222] transition-colors"
      >
        <div className="flex items-center gap-2">
          {isStreaming && (
            <div className="w-2 h-2 rounded-full bg-[#3ecf8e] animate-pulse" />
          )}
          <span className="text-[10px] font-medium text-[#8c8c8c] uppercase tracking-wider">
            실행 로그
          </span>
          <span className="text-[10px] text-[#5c5c5c]">({events.length})</span>
        </div>
        <span className="text-[10px] text-[#5c5c5c]">
          {collapsed ? "▸" : "▾"}
        </span>
      </button>

      {/* 로그 본문 */}
      {!collapsed && (
        <div
          ref={scrollRef}
          className="max-h-[200px] overflow-auto px-4 py-2 font-mono text-[10px] leading-relaxed"
        >
          {events.length === 0 && (
            <p className="text-[#5c5c5c] py-2">대기 중...</p>
          )}
          {events.map((evt, i) => (
            <LogEntry key={i} event={evt} />
          ))}
        </div>
      )}
    </div>
  );
}

function LogEntry({ event }: { event: StreamEvent }) {
  const time = event.timestamp
    ? new Date(event.timestamp).toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "";

  const label = NODE_LABELS[event.name] || event.name;

  if (event.event === "on_chain_start") {
    return (
      <div className="flex gap-2 py-0.5">
        <span className="text-[#5c5c5c] shrink-0">{time}</span>
        <span className="text-blue-400">▶</span>
        <span className="text-[#ededed]">{label}</span>
        <span className="text-[#5c5c5c]">시작</span>
      </div>
    );
  }

  if (event.event === "on_chain_end") {
    return (
      <div className="flex gap-2 py-0.5">
        <span className="text-[#5c5c5c] shrink-0">{time}</span>
        <span className="text-[#3ecf8e]">✓</span>
        <span className="text-[#ededed]">{label}</span>
        <span className="text-[#3ecf8e]">완료</span>
        {event.current_step && (
          <span className="text-[#5c5c5c]">→ {event.current_step}</span>
        )}
      </div>
    );
  }

  if (event.event === "error") {
    return (
      <div className="flex gap-2 py-0.5">
        <span className="text-[#5c5c5c] shrink-0">{time}</span>
        <span className="text-red-400">✗</span>
        <span className="text-red-400">{event.message || "오류 발생"}</span>
      </div>
    );
  }

  if (event.event === "done") {
    return (
      <div className="flex gap-2 py-0.5">
        <span className="text-[#5c5c5c] shrink-0">{time}</span>
        <span className="text-[#3ecf8e]">■</span>
        <span className="text-[#3ecf8e]">워크플로 완료</span>
      </div>
    );
  }

  return null;
}
