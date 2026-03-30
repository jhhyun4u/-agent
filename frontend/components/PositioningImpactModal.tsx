"use client";

/**
 * PositioningImpactModal — 포지셔닝 변경 시 영향 분석 확인 모달 (§13-6)
 *
 * GoNoGoPanel에서 포지셔닝을 변경할 때 트리거.
 * 영향 받는 STEP + 재생성 범위를 보여주고 확정/취소를 받는다.
 */

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface PositioningImpactModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (newPositioning: string) => void;
  proposalId: string;
  currentPositioning: string;
  newPositioning: string;
}

const POS_LABELS: Record<string, { label: string; icon: string }> = {
  defensive: { label: "수성형", icon: "🛡️" },
  offensive: { label: "공격형", icon: "⚔️" },
  adjacent: { label: "인접형", icon: "🔄" },
};

const STEP_LABELS: Record<number, string> = {
  2: "전략 수립",
  3: "계획",
  4: "제안서 작성",
  5: "PPT",
};

const IMPACT_ITEMS: Record<string, string[]> = {
  "defensive→offensive": ["Ghost Theme 변경", "Win Theme 재설정", "가격 전략 재계산 필요", "인력 구성 재검토 필요"],
  "offensive→defensive": ["Win Theme 축소", "가격 안정화 전략", "리스크 최소화 전략 적용"],
  "defensive→adjacent": ["Ghost Theme 조정", "틈새 전략 수립", "차별화 포인트 재설정"],
  "adjacent→offensive": ["Win Theme 강화", "공격적 가격 전략", "핵심 인력 재배치"],
  "adjacent→defensive": ["안정적 가격 전략", "기존 실적 중심 어필", "리스크 관리 강화"],
  "offensive→adjacent": ["Win Theme 조정", "틈새 전략 수립", "가격 재조정"],
};

export default function PositioningImpactModal({
  open,
  onClose,
  onConfirm,
  proposalId,
  currentPositioning,
  newPositioning,
}: PositioningImpactModalProps) {
  const [impact, setImpact] = useState<{ affected_steps: number[]; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    api.workflow.impact(proposalId, "go_no_go")
      .then((res) => setImpact(res))
      .catch(() => setImpact({ affected_steps: [2, 3, 4, 5], message: "영향 범위를 확인할 수 없습니다. 전체 재생성이 필요할 수 있습니다." }))
      .finally(() => setLoading(false));
  }, [open, proposalId]);

  if (!open) return null;

  const cur = POS_LABELS[currentPositioning] ?? { label: currentPositioning, icon: "?" };
  const nxt = POS_LABELS[newPositioning] ?? { label: newPositioning, icon: "?" };
  const transitionKey = `${currentPositioning}→${newPositioning}`;
  const items = IMPACT_ITEMS[transitionKey] ?? ["전략 전면 재검토 필요"];

  return (
    <>
      {/* 백드롭 */}
      <div className="fixed inset-0 bg-black/60 z-50" onClick={onClose} />

      {/* 모달 */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-[#1c1c1c] border border-[#333] rounded-2xl w-full max-w-md shadow-2xl">
          {/* 헤더 */}
          <div className="px-5 py-4 border-b border-[#262626]">
            <h3 className="text-sm font-semibold text-[#ededed] flex items-center gap-2">
              <span className="text-amber-400">!</span>
              포지셔닝 변경 영향 분석
            </h3>
          </div>

          {/* 본문 */}
          <div className="px-5 py-4 space-y-4">
            {/* 변경 요약 */}
            <div className="flex items-center justify-center gap-3 py-3 bg-[#111111] rounded-lg">
              <span className="text-sm">
                {cur.icon} <span className="text-[#ededed]">{cur.label}</span>
              </span>
              <span className="text-[#8c8c8c]">→</span>
              <span className="text-sm">
                {nxt.icon} <span className="text-[#3ecf8e] font-semibold">{nxt.label}</span>
              </span>
            </div>

            {/* 영향 항목 */}
            <div className="bg-[#111111] border border-[#262626] rounded-lg px-4 py-3">
              <p className="text-[10px] text-[#8c8c8c] uppercase tracking-wider mb-2">영향 받는 항목</p>
              <ul className="space-y-1">
                {items.map((item, i) => (
                  <li key={i} className="text-xs text-[#ededed] flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-amber-500 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* 재생성 범위 */}
            {loading ? (
              <div className="text-center py-4">
                <span className="text-xs text-[#8c8c8c]">영향 범위 분석 중...</span>
              </div>
            ) : impact && (
              <div className="bg-[#111111] border border-[#262626] rounded-lg px-4 py-3">
                <p className="text-[10px] text-[#8c8c8c] uppercase tracking-wider mb-2">재생성 범위</p>
                {impact.affected_steps.length > 0 ? (
                  <div className="space-y-1">
                    {impact.affected_steps.map((step) => (
                      <div key={step} className="flex items-center justify-between text-xs">
                        <span className="text-[#ededed]">STEP {step} {STEP_LABELS[step] ?? ""}</span>
                        <span className="text-amber-400 text-[10px]">재실행</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[#8c8c8c]">{impact.message}</p>
                )}
              </div>
            )}

            {/* 경고 */}
            <div className="flex items-center gap-2 px-3 py-2 bg-red-500/5 border border-red-500/20 rounded-lg">
              <span className="text-red-400 text-xs">!</span>
              <p className="text-[10px] text-[#8c8c8c]">승인 상태가 초기화됩니다.</p>
            </div>
          </div>

          {/* 액션 */}
          <div className="px-5 py-4 border-t border-[#262626] flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 text-xs font-medium rounded-lg border border-[#262626] text-[#8c8c8c] hover:bg-[#262626] transition-colors"
            >
              취소
            </button>
            <button
              onClick={() => onConfirm(newPositioning)}
              disabled={loading}
              className="flex-1 py-2.5 text-xs font-bold rounded-lg bg-amber-500 text-[#0f0f0f] hover:bg-amber-400 disabled:opacity-40 transition-colors"
            >
              변경 확정
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
