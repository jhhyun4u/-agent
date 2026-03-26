"use client";

/**
 * CompareView — A vs B 비교 시뮬레이션 UI
 *
 * 동일 입력으로 두 프롬프트 버전을 실행하고 결과를 나란히 비교.
 */

import { useCallback, useEffect, useState } from "react";
import { api, type CompareResult, type SimulationQuota } from "@/lib/api";
import { SimResultCard } from "./SimulationRunner";

const SAMPLE_OPTIONS = [
  { id: "sample_small_si", label: "소규모 SI (5천만원, 서류심사)" },
  { id: "sample_mid_consulting", label: "중규모 컨설팅 (3억원, 기술+가격)" },
  { id: "sample_large_isp", label: "대규모 ISP (15억원, 발표심사)" },
];

interface CompareViewProps {
  promptId: string;
}

export default function CompareView({ promptId }: CompareViewProps) {
  const [dataSource, setDataSource] = useState<"sample" | "project" | "custom">("sample");
  const [sampleId, setSampleId] = useState("sample_mid_consulting");
  const [runQuality, setRunQuality] = useState(true);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [quota, setQuota] = useState<SimulationQuota | null>(null);
  const [error, setError] = useState("");

  const fetchQuota = useCallback(async () => {
    try {
      setQuota(await api.prompts.simulationQuota());
    } catch {
      /* 무시 */
    }
  }, []);

  useEffect(() => {
    fetchQuota();
  }, [fetchQuota]);

  const handleRun = async () => {
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const res = await api.prompts.simulateCompare(promptId, {
        version_a: null,
        text_a: null,
        version_b: null,
        text_b: null,
        data_source: dataSource,
        data_source_id: dataSource === "sample" ? sampleId : undefined,
        run_quality_check: runQuality,
      });
      setResult(res);
      fetchQuota();
    } catch (e) {
      setError(e instanceof Error ? e.message : "비교 시뮬레이션 실패");
    }
    setRunning(false);
  };

  return (
    <div className="space-y-4">
      {/* 입력 설정 */}
      <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 space-y-4">
        <h2 className="text-sm font-semibold">A vs B 비교 설정</h2>

        <div>
          <label className="text-xs text-[#8c8c8c] block mb-2">데이터 소스</label>
          <div className="flex gap-3">
            {(["sample", "project", "custom"] as const).map((id) => (
              <button
                key={id}
                onClick={() => setDataSource(id)}
                className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                  dataSource === id
                    ? "bg-[#262626] text-[#ededed] border border-[#444]"
                    : "bg-[#111] text-[#8c8c8c] hover:bg-[#1a1a1a] border border-transparent"
                }`}
              >
                {{ sample: "샘플 RFP", project: "기존 프로젝트", custom: "커스텀" }[id]}
              </button>
            ))}
          </div>
        </div>

        {dataSource === "sample" && (
          <div>
            <label className="text-xs text-[#8c8c8c] block mb-2">샘플 RFP</label>
            <select
              value={sampleId}
              onChange={(e) => setSampleId(e.target.value)}
              className="bg-[#0a0a0a] border border-[#262626] rounded-lg px-3 py-2 text-xs focus:border-[#3ecf8e] focus:outline-none w-full"
            >
              {SAMPLE_OPTIONS.map((s) => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>
        )}

        <label className="flex items-center gap-2 text-xs cursor-pointer">
          <input
            type="checkbox"
            checked={runQuality}
            onChange={(e) => setRunQuality(e.target.checked)}
            className="accent-[#3ecf8e]"
          />
          품질 자가진단 포함
        </label>

        <div className="flex items-center gap-4">
          <button
            onClick={handleRun}
            disabled={running}
            className="px-6 py-2 bg-[#f5a623] text-black rounded-lg text-xs font-bold hover:bg-[#e09520] disabled:opacity-50 transition-colors"
          >
            {running ? "비교 중..." : "A vs B 비교 실행"}
          </button>
          {quota && (
            <span className="text-xs text-[#8c8c8c]">
              잔여: {quota.remaining}/{quota.daily_limit}회 (비교는 2회 소모)
            </span>
          )}
        </div>

        {error && <div className="text-xs text-[#ff6b6b]">{error}</div>}
      </section>

      {/* 비교 결과 */}
      {result && (
        <>
          {/* 요약 */}
          <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
            <h2 className="text-sm font-semibold mb-3">비교 요약</h2>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xs text-[#8c8c8c]">품질 차이</div>
                <div
                  className={`text-lg font-bold ${
                    result.comparison.quality_diff > 0
                      ? "text-[#3ecf8e]"
                      : result.comparison.quality_diff < 0
                        ? "text-[#ff6b6b]"
                        : ""
                  }`}
                >
                  {result.comparison.quality_diff > 0 ? "+" : ""}
                  {result.comparison.quality_diff}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#8c8c8c]">토큰 차이</div>
                <div className="text-lg font-bold">{result.comparison.token_diff}</div>
              </div>
              <div>
                <div className="text-xs text-[#8c8c8c]">추천</div>
                <div className="text-xs mt-1">{result.comparison.recommendation}</div>
              </div>
            </div>
          </section>

          {/* 나란히 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <SimResultCard result={result.result_a} compact label="A: Active" />
            <SimResultCard result={result.result_b} compact label="B: Candidate" />
          </div>
        </>
      )}
    </div>
  );
}
