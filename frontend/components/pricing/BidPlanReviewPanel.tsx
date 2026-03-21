"use client";

/**
 * STEP 2.5 입찰가격계획 리뷰 패널
 *
 * 워크플로 interrupt에서 bid_plan 산출물을 표시하고
 * 시나리오 선택 + 수동 오버라이드 + 승인/거부를 처리한다.
 * 기존 pricing/ 컴포넌트(ScenarioCards, SensitivityChart, WinProbabilityGauge)를 재사용.
 */

import { useState } from "react";
import ScenarioCards from "./ScenarioCards";
import SensitivityChart from "./SensitivityChart";
import WinProbabilityGauge from "./WinProbabilityGauge";
import type { PricingScenario, SensitivityPoint } from "@/lib/api";

interface BidPlanData {
  recommended_bid: number;
  recommended_ratio: number;
  scenarios: PricingScenario[];
  selected_scenario: string;
  cost_breakdown: Record<string, unknown>;
  sensitivity_curve: SensitivityPoint[];
  win_probability: number;
  market_context: Record<string, unknown>;
  data_quality: string;
  user_override_price: number | null;
  user_override_reason: string;
}

interface Props {
  artifact: BidPlanData;
  onResume: (payload: Record<string, unknown>) => void;
}

function fmtWon(amount: number): string {
  if (Math.abs(amount) >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (Math.abs(amount) >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

export default function BidPlanReviewPanel({ artifact, onResume }: Props) {
  const [selectedScenario, setSelectedScenario] = useState(
    artifact?.selected_scenario || "balanced"
  );
  const [overrideEnabled, setOverrideEnabled] = useState(false);
  const [customPrice, setCustomPrice] = useState("");
  const [customReason, setCustomReason] = useState("");
  const [feedback, setFeedback] = useState("");

  if (!artifact) return null;

  const handleApprove = () => {
    const payload: Record<string, unknown> = {
      approved: true,
      selected_scenario: selectedScenario,
    };
    if (overrideEnabled && customPrice) {
      const parsed = parseInt(customPrice.replace(/,/g, ""), 10);
      if (isNaN(parsed) || parsed <= 0) {
        alert("올바른 입찰가를 입력하세요 (양수).");
        return;
      }
      payload.custom_bid_price = parsed;
      payload.custom_bid_reason = customReason;
    }
    onResume(payload);
  };

  const handleReject = (backToStrategy = false) => {
    onResume({
      approved: false,
      feedback,
      back_to_strategy: backToStrategy,
    });
  };

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="rounded-lg border border-[#262626] bg-[#161616] p-4">
        <h2 className="text-base font-semibold text-[#ededed] mb-2">
          STEP 2.5: 입찰가격계획
        </h2>
        <p className="text-xs text-[#8c8c8c]">
          전략에 맞는 입찰 시나리오를 선택하세요. 시나리오 선택 후 실행 계획(팀/일정/원가)이 이 예산 범위 내에서 수립됩니다.
        </p>
        <div className="mt-3 flex items-center gap-4 text-sm">
          <div>
            <span className="text-[#8c8c8c]">추천가: </span>
            <span className="text-[#ededed] font-mono font-medium">
              {fmtWon(artifact.recommended_bid)}
            </span>
            <span className="text-[#8c8c8c] ml-1">
              ({artifact.recommended_ratio.toFixed(1)}%)
            </span>
          </div>
          <div>
            <span className="text-[#8c8c8c]">데이터: </span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              artifact.data_quality === "statistical"
                ? "bg-green-400/10 text-green-400"
                : artifact.data_quality === "hybrid"
                ? "bg-blue-400/10 text-blue-400"
                : "bg-yellow-400/10 text-yellow-400"
            }`}>
              {artifact.data_quality}
            </span>
          </div>
        </div>
      </div>

      {/* 수주확률 + 시나리오 카드 */}
      <div className="grid grid-cols-[200px_1fr] gap-4">
        <WinProbabilityGauge
          probability={artifact.win_probability}
          confidence={artifact.data_quality === "statistical" ? "high" : "medium"}
        />
        <ScenarioCards
          scenarios={artifact.scenarios}
          selected={selectedScenario}
          onSelect={setSelectedScenario}
        />
      </div>

      {/* 민감도 곡선 */}
      {(artifact.sensitivity_curve ?? []).length > 0 && (
        <SensitivityChart
          points={artifact.sensitivity_curve}
          optimalRatio={artifact.recommended_ratio}
        />
      )}

      {/* 수동 오버라이드 */}
      <div className="rounded-lg border border-[#262626] bg-[#161616] p-4">
        <label className="flex items-center gap-2 text-sm text-[#ededed] cursor-pointer">
          <input
            type="checkbox"
            checked={overrideEnabled}
            onChange={(e) => setOverrideEnabled(e.target.checked)}
            className="accent-[#3ecf8e]"
          />
          수동 입찰가 오버라이드
        </label>
        {overrideEnabled && (
          <div className="mt-3 space-y-2">
            <div>
              <label className="text-xs text-[#8c8c8c]">입찰가 (원)</label>
              <input
                type="text"
                value={customPrice}
                onChange={(e) => setCustomPrice(e.target.value)}
                placeholder="예: 450000000"
                className="mt-1 w-full rounded border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-[#ededed] focus:border-[#3ecf8e] focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-[#8c8c8c]">오버라이드 사유</label>
              <input
                type="text"
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                placeholder="예: 발주기관 선호가 반영"
                className="mt-1 w-full rounded border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-[#ededed] focus:border-[#3ecf8e] focus:outline-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* 피드백 (거부 시) */}
      <div>
        <label className="text-xs text-[#8c8c8c]">피드백 (거부 시)</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-[#ededed] focus:border-[#3ecf8e] focus:outline-none resize-none"
          placeholder="가격 재검토 이유..."
        />
      </div>

      {/* 액션 버튼 */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleApprove}
          className="rounded-lg bg-[#3ecf8e] px-4 py-2 text-sm font-medium text-[#0a0a0a] hover:bg-[#3ecf8e]/90 transition-colors"
        >
          승인 ({selectedScenario === "conservative" ? "보수적" : selectedScenario === "aggressive" ? "공격적" : "균형"})
        </button>
        <button
          onClick={() => handleReject(false)}
          className="rounded-lg border border-[#333] bg-[#161616] px-4 py-2 text-sm text-[#ededed] hover:bg-[#1f1f1f] transition-colors"
        >
          재시뮬레이션
        </button>
        <button
          onClick={() => handleReject(true)}
          className="rounded-lg border border-orange-500/30 bg-orange-500/5 px-4 py-2 text-sm text-orange-400 hover:bg-orange-500/10 transition-colors"
        >
          전략 재수립
        </button>
      </div>
    </div>
  );
}
