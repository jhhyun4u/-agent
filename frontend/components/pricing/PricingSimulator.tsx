"use client";

/**
 * PricingSimulator — 입력 폼 + 실행 + 결과 통합 컴포넌트
 */

import { useState } from "react";
import {
  pricingApi,
  type PricingSimulationRequest,
  type PricingSimulationResult,
  type PricingPersonnelInput,
} from "@/lib/api";
import WinProbabilityGauge from "./WinProbabilityGauge";
import CostBreakdownCard from "./CostBreakdownCard";
import SensitivityChart from "./SensitivityChart";
import ScenarioCards from "./ScenarioCards";
import MarketContextPanel from "./MarketContextPanel";

const DOMAINS = ["SI/SW개발", "엔지니어링", "정책연구", "컨설팅"];
const EVAL_METHODS = ["종합심사", "적격심사", "최저가", "수의계약"];
const GRADES = ["기술사", "특급", "고급", "중급", "초급"];

function fmtWon(amount: number): string {
  if (Math.abs(amount) >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (Math.abs(amount) >= 10_000) return `${Math.round(amount / 10_000).toLocaleString()}만원`;
  return `${amount.toLocaleString()}원`;
}

export default function PricingSimulator() {
  // 입력
  const [budget, setBudget] = useState(500_000_000);
  const [domain, setDomain] = useState("SI/SW개발");
  const [evalMethod, setEvalMethod] = useState("종합심사");
  const [techRatio, setTechRatio] = useState(80);
  const [positioning, setPositioning] = useState("defensive");
  const [competitorCount, setCompetitorCount] = useState(5);
  const [clientName, setClientName] = useState("");
  const [personnel, setPersonnel] = useState<PricingPersonnelInput[]>([]);

  // 결과
  const [result, setResult] = useState<PricingSimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedScenario, setSelectedScenario] = useState("");

  async function runSimulation() {
    setLoading(true);
    setError("");
    try {
      const req: PricingSimulationRequest = {
        budget,
        domain,
        evaluation_method: evalMethod,
        tech_price_ratio: { tech: techRatio, price: 100 - techRatio },
        positioning,
        competitor_count: competitorCount,
        personnel: personnel.length > 0 ? personnel : undefined,
        client_name: clientName || undefined,
      };
      const res = await pricingApi.simulatePricing(req);
      setResult(res);
      if (res.scenarios?.length) setSelectedScenario(res.scenarios[1]?.name || "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "시뮬레이션 실패");
    } finally {
      setLoading(false);
    }
  }

  function addPersonnel() {
    setPersonnel([...personnel, { role: "", grade: "중급", person_months: 1 }]);
  }

  function removePersonnel(idx: number) {
    setPersonnel(personnel.filter((_, i) => i !== idx));
  }

  function updatePersonnel(idx: number, field: string, value: string | number) {
    const updated = [...personnel];
    updated[idx] = { ...updated[idx], [field]: value };
    setPersonnel(updated);
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      {/* ── 입력 패널 (2/5) ── */}
      <div className="lg:col-span-2 space-y-4">
        <div className="rounded-lg border border-[#262626] bg-[#161616] p-4 space-y-4">
          <h3 className="text-sm font-medium text-[#ededed]">시뮬레이션 입력</h3>

          {/* 예산 */}
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-1">사업예산</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full bg-[#1c1c1c] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed]"
            />
            <div className="text-xs text-[#666] mt-0.5">{fmtWon(budget)}</div>
          </div>

          {/* 도메인 */}
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-1">도메인</label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed]"
            >
              {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>

          {/* 조달방식 */}
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-1">조달방식</label>
            <select
              value={evalMethod}
              onChange={(e) => setEvalMethod(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed]"
            >
              {EVAL_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          {/* 기술:가격 비율 */}
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-1">
              기술:가격 = {techRatio}:{100 - techRatio}
            </label>
            <input
              type="range"
              min={50}
              max={95}
              value={techRatio}
              onChange={(e) => setTechRatio(Number(e.target.value))}
              className="w-full accent-[#3ecf8e]"
            />
          </div>

          {/* 포지셔닝 */}
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-1">포지셔닝</label>
            <div className="flex gap-2">
              {[
                { value: "defensive", label: "수성" },
                { value: "offensive", label: "공격" },
                { value: "adjacent", label: "인접" },
              ].map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setPositioning(value)}
                  className={`flex-1 text-sm py-1.5 rounded border transition-colors ${
                    positioning === value
                      ? "border-[#3ecf8e] bg-[#3ecf8e]/10 text-[#3ecf8e]"
                      : "border-[#333] text-[#8c8c8c] hover:border-[#555]"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 경쟁사 수 */}
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-1">
              경쟁사 수: {competitorCount}
            </label>
            <input
              type="range"
              min={1}
              max={15}
              value={competitorCount}
              onChange={(e) => setCompetitorCount(Number(e.target.value))}
              className="w-full accent-[#3ecf8e]"
            />
          </div>

          {/* 발주기관 */}
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-1">발주기관 (선택)</label>
            <input
              type="text"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              placeholder="예: 한국정보화진흥원"
              className="w-full bg-[#1c1c1c] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] placeholder:text-[#555]"
            />
          </div>

          {/* 인력 */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-[#8c8c8c]">투입 인력 (선택)</label>
              <button onClick={addPersonnel} className="text-xs text-[#3ecf8e] hover:underline">
                + 추가
              </button>
            </div>
            {personnel.map((p, i) => (
              <div key={i} className="flex gap-1.5 mb-1.5">
                <input
                  type="text"
                  value={p.role}
                  onChange={(e) => updatePersonnel(i, "role", e.target.value)}
                  placeholder="역할"
                  className="flex-1 bg-[#1c1c1c] border border-[#333] rounded px-2 py-1 text-xs text-[#ededed]"
                />
                <select
                  value={p.grade}
                  onChange={(e) => updatePersonnel(i, "grade", e.target.value)}
                  className="bg-[#1c1c1c] border border-[#333] rounded px-2 py-1 text-xs text-[#ededed]"
                >
                  {GRADES.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
                <input
                  type="number"
                  value={p.person_months}
                  onChange={(e) => updatePersonnel(i, "person_months", Number(e.target.value))}
                  className="w-16 bg-[#1c1c1c] border border-[#333] rounded px-2 py-1 text-xs text-[#ededed]"
                  min={0.5}
                  step={0.5}
                />
                <span className="self-center text-xs text-[#666]">M/M</span>
                <button onClick={() => removePersonnel(i)} className="text-red-400 text-xs px-1 hover:text-red-300">
                  X
                </button>
              </div>
            ))}
          </div>

          {/* 실행 */}
          <button
            onClick={runSimulation}
            disabled={loading || budget <= 0}
            className="w-full py-2.5 rounded bg-[#3ecf8e] text-black font-medium text-sm hover:bg-[#35b87e] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "분석 중..." : "시뮬레이션 실행"}
          </button>

          {error && <div className="text-xs text-red-400">{error}</div>}
        </div>
      </div>

      {/* ── 결과 패널 (3/5) ── */}
      <div className="lg:col-span-3 space-y-4">
        {!result && !loading && (
          <div className="rounded-lg border border-[#262626] bg-[#161616] p-8 text-center text-[#8c8c8c]">
            <div className="text-2xl mb-2">📊</div>
            <p className="text-sm">입력값을 설정하고 시뮬레이션을 실행하세요</p>
          </div>
        )}

        {loading && (
          <div className="rounded-lg border border-[#262626] bg-[#161616] p-8 text-center text-[#8c8c8c]">
            <div className="animate-pulse text-sm">시뮬레이션 분석 중...</div>
          </div>
        )}

        {result && (
          <>
            {/* 추천 입찰가 요약 */}
            <div className="rounded-lg border border-[#3ecf8e]/20 bg-[#3ecf8e]/5 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#8c8c8c] mb-0.5">추천 입찰가</div>
                  <div className="text-2xl font-bold text-[#ededed]">
                    {fmtWon(result.recommended_bid)}
                  </div>
                  <div className="text-sm text-[#8c8c8c]">
                    낙찰률 {result.recommended_ratio}%
                    {result.bid_range && (
                      <span className="ml-2 text-xs">
                        ({result.bid_range.min_ratio}% ~ {result.bid_range.max_ratio}%)
                      </span>
                    )}
                  </div>
                </div>
                <WinProbabilityGauge
                  probability={result.win_probability}
                  confidence={result.win_probability_confidence}
                />
              </div>
              <div className="flex gap-3 mt-2 text-xs text-[#8c8c8c]">
                <span>분석: {result.data_quality === "statistical" ? "통계 기반" : "규칙 기반"}</span>
                <span>유사 사례: {result.comparable_cases}건</span>
                {result.cost_standard_used && (
                  <span>비용 기준: {result.cost_standard_used}</span>
                )}
              </div>
            </div>

            {/* 민감도 */}
            {result.sensitivity_curve.length > 0 && (
              <SensitivityChart
                points={result.sensitivity_curve}
                optimalRatio={result.optimal_ratio}
              />
            )}

            {/* 시나리오 */}
            {result.scenarios.length > 0 && (
              <ScenarioCards
                scenarios={result.scenarios}
                selected={selectedScenario}
                onSelect={setSelectedScenario}
              />
            )}

            {/* 원가 구조 */}
            {result.cost_breakdown && (
              <CostBreakdownCard cost={result.cost_breakdown} />
            )}

            {/* 시장 컨텍스트 */}
            {result.market_context && result.market_context.total_cases > 0 && (
              <MarketContextPanel context={result.market_context} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
