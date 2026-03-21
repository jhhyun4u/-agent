"use client";

/**
 * BiddingWorkspace — Stream 2 비딩관리 UI
 *
 * 기능:
 * - 확정 입찰가 + 낙찰률 표시
 * - 시나리오 비교 카드 (공격/균형/보수)
 * - 가격 변경 이력 타임라인
 * - 워크플로 완료 후 가격 조정 폼
 * - 투찰 상태 트래커
 */

import { useCallback, useEffect, useState } from "react";
import {
  bidSubmissionApi,
  type BiddingWorkspace as BiddingWorkspaceType,
  type BidPriceHistoryEntry,
} from "@/lib/api";

interface Props {
  proposalId: string;
}

function formatWon(n: number | null | undefined): string {
  if (!n) return "—";
  return new Intl.NumberFormat("ko-KR").format(n) + "원";
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

const EVENT_LABELS: Record<string, { label: string; color: string }> = {
  confirmed: { label: "확정", color: "text-[#3ecf8e]" },
  override: { label: "오버라이드", color: "text-amber-400" },
  adjusted: { label: "조정", color: "text-blue-400" },
  submitted: { label: "투찰", color: "text-purple-400" },
  verified: { label: "검증", color: "text-[#3ecf8e]" },
};

const SUBMISSION_STATUS: Record<string, { label: string; color: string }> = {
  ready: { label: "투찰 대기", color: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
  submitted: { label: "투찰 완료", color: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
  verified: { label: "검증 완료", color: "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/30" },
};

export default function BiddingWorkspace({ proposalId }: Props) {
  const [workspace, setWorkspace] = useState<BiddingWorkspaceType | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAdjustForm, setShowAdjustForm] = useState(false);
  const [adjustPrice, setAdjustPrice] = useState("");
  const [adjustReason, setAdjustReason] = useState("");
  const [adjusting, setAdjusting] = useState(false);

  const fetchWorkspace = useCallback(async () => {
    setLoading(true);
    try {
      const data = await bidSubmissionApi.getBiddingWorkspace(proposalId);
      setWorkspace(data);
    } catch { /* empty */ }
    finally { setLoading(false); }
  }, [proposalId]);

  useEffect(() => { fetchWorkspace(); }, [fetchWorkspace]);

  // ── 가격 조정 ──
  async function handleAdjust() {
    const price = parseInt(adjustPrice.replace(/,/g, ""), 10);
    if (!price || !adjustReason.trim()) {
      alert("가격과 사유를 입력하세요.");
      return;
    }
    setAdjusting(true);
    try {
      await bidSubmissionApi.adjustPrice(proposalId, {
        adjusted_price: price,
        reason: adjustReason.trim(),
      });
      setShowAdjustForm(false);
      setAdjustPrice("");
      setAdjustReason("");
      fetchWorkspace();
    } catch (e) {
      alert(e instanceof Error ? e.message : "가격 조정 실패");
    } finally { setAdjusting(false); }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-[#8c8c8c] text-sm">
        불러오는 중...
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="max-w-3xl mx-auto bg-[#1c1c1c] border border-[#262626] rounded-xl p-8 text-center">
        <p className="text-sm text-[#8c8c8c]">비딩 정보가 없습니다.</p>
        <p className="text-xs text-[#8c8c8c] mt-1">워크플로에서 입찰가격 계획(STEP 2.5)이 완료되면 표시됩니다.</p>
      </div>
    );
  }

  const bs = workspace.bid_status;
  const subStatus = bs?.bid_submission_status;
  const subBadge = subStatus ? SUBMISSION_STATUS[subStatus] : null;

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* 상단: 확정가 + 투찰 상태 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 확정 입찰가 */}
        <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-medium text-[#8c8c8c] uppercase tracking-wider">확정 입찰가</h3>
            <button
              onClick={() => setShowAdjustForm(v => !v)}
              className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
            >
              가격 조정
            </button>
          </div>
          <p className="text-xl font-bold text-[#ededed]">
            {formatWon(bs?.bid_confirmed_price)}
          </p>
          <div className="flex items-center gap-4 mt-2 text-xs text-[#8c8c8c]">
            {bs?.bid_confirmed_ratio && (
              <span>낙찰률 {bs.bid_confirmed_ratio}%</span>
            )}
            {bs?.bid_confirmed_scenario && (
              <span>시나리오: {bs.bid_confirmed_scenario}</span>
            )}
          </div>
          {workspace.market_summary && workspace.market_summary.win_probability > 0 && (
            <div className="mt-3 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-[#262626] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#3ecf8e] rounded-full transition-all"
                  style={{ width: `${workspace.market_summary.win_probability}%` }}
                />
              </div>
              <span className="text-[10px] text-[#3ecf8e]">
                수주확률 {workspace.market_summary.win_probability}%
              </span>
            </div>
          )}
        </div>

        {/* 투찰 상태 */}
        <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-5">
          <h3 className="text-xs font-medium text-[#8c8c8c] uppercase tracking-wider mb-3">투찰 상태</h3>
          {subBadge ? (
            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${subBadge.color}`}>
              {subBadge.label}
            </span>
          ) : (
            <span className="text-xs text-[#8c8c8c]">투찰 전</span>
          )}
          {bs?.bid_submitted_price && (
            <p className="text-sm text-[#ededed] mt-2">
              투찰가: {formatWon(bs.bid_submitted_price)}
            </p>
          )}
          {bs?.bid_submitted_at && (
            <p className="text-xs text-[#8c8c8c] mt-1">
              투찰 시각: {formatDate(bs.bid_submitted_at)}
            </p>
          )}
          <div className="mt-3 flex items-center gap-3 text-xs text-[#8c8c8c]">
            {workspace.market_summary && (
              <>
                <span>유사과제 {workspace.market_summary.comparable_cases}건</span>
                {workspace.market_summary.market_avg_ratio && (
                  <span>시장평균 {workspace.market_summary.market_avg_ratio}%</span>
                )}
                <span className="text-[10px] px-1.5 py-0.5 bg-[#262626] rounded">
                  {workspace.market_summary.data_quality}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 가격 조정 폼 */}
      {showAdjustForm && (
        <div className="bg-[#1c1c1c] border border-blue-500/30 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-semibold text-blue-400">가격 조정</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-[#8c8c8c] uppercase tracking-wider">조정 가격 (원)</label>
              <input
                type="text"
                value={adjustPrice}
                onChange={e => setAdjustPrice(e.target.value)}
                placeholder="1,230,000,000"
                className="mt-1 w-full px-3 py-1.5 bg-[#0f0f0f] border border-[#262626] rounded text-xs text-[#ededed] focus:outline-none focus:border-blue-500/50"
              />
            </div>
            <div>
              <label className="text-[10px] text-[#8c8c8c] uppercase tracking-wider">사유 (필수)</label>
              <input
                type="text"
                value={adjustReason}
                onChange={e => setAdjustReason(e.target.value)}
                placeholder="경쟁사 정보 반영"
                className="mt-1 w-full px-3 py-1.5 bg-[#0f0f0f] border border-[#262626] rounded text-xs text-[#ededed] focus:outline-none focus:border-blue-500/50"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowAdjustForm(false)}
              className="px-3 py-1.5 text-xs text-[#8c8c8c] hover:text-[#ededed] transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleAdjust}
              disabled={adjusting}
              className="px-4 py-1.5 text-xs font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              {adjusting ? "처리 중..." : "가격 조정"}
            </button>
          </div>
        </div>
      )}

      {/* 시나리오 비교 */}
      {workspace.scenarios && workspace.scenarios.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-[#8c8c8c] uppercase tracking-wider mb-2">시나리오 비교</h3>
          <div className="grid grid-cols-3 gap-3">
            {workspace.scenarios.map((scenario: Record<string, unknown>, idx: number) => {
              const name = (scenario.name || scenario.label || `시나리오 ${idx + 1}`) as string;
              const isSelected = name === bs?.bid_confirmed_scenario || (scenario.name as string) === bs?.bid_confirmed_scenario;
              return (
                <div
                  key={idx}
                  className={`bg-[#1c1c1c] border rounded-xl p-4 text-center transition-colors ${
                    isSelected ? "border-[#3ecf8e]/50 bg-[#3ecf8e]/5" : "border-[#262626]"
                  }`}
                >
                  <p className="text-xs font-semibold text-[#ededed] mb-1">{name}</p>
                  {scenario.bid_ratio !== undefined && (
                    <p className="text-lg font-bold text-[#ededed]">{scenario.bid_ratio as number}%</p>
                  )}
                  {scenario.win_probability !== undefined && (
                    <p className="text-[10px] text-[#8c8c8c] mt-1">
                      수주확률 {scenario.win_probability as number}%
                    </p>
                  )}
                  {scenario.bid_price !== undefined && (
                    <p className="text-[10px] text-[#8c8c8c]">
                      {formatWon(scenario.bid_price as number)}
                    </p>
                  )}
                  {isSelected && (
                    <span className="inline-flex mt-2 px-2 py-0.5 rounded text-[9px] font-medium bg-[#3ecf8e]/15 text-[#3ecf8e]">
                      선택됨
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 가격 변경 이력 */}
      {workspace.price_history && workspace.price_history.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-[#8c8c8c] uppercase tracking-wider mb-2">가격 변경 이력</h3>
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl overflow-hidden">
            <div className="divide-y divide-[#262626]/50">
              {workspace.price_history.map((entry: BidPriceHistoryEntry) => {
                const evt = EVENT_LABELS[entry.event_type] || { label: entry.event_type, color: "text-[#8c8c8c]" };
                return (
                  <div key={entry.id} className="px-4 py-3 flex items-center gap-4">
                    <span className="text-[10px] text-[#8c8c8c] w-20 shrink-0">
                      {formatDate(entry.created_at)}
                    </span>
                    <span className={`text-xs font-medium w-16 shrink-0 ${evt.color}`}>
                      {evt.label}
                    </span>
                    <span className="text-xs text-[#ededed] font-mono">
                      {formatWon(entry.price)}
                    </span>
                    {entry.scenario_name && (
                      <span className="text-[10px] text-[#8c8c8c]">({entry.scenario_name})</span>
                    )}
                    {entry.reason && (
                      <span className="text-[10px] text-[#8c8c8c] truncate flex-1">{entry.reason}</span>
                    )}
                    {entry.actor_name && (
                      <span className="text-[10px] text-[#8c8c8c] shrink-0">{entry.actor_name}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
