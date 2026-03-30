"use client";

/**
 * SimulationRunner — 시뮬레이션 실행 UI + 결과 + 품질 점수
 *
 * 단독 실행 모드. 데이터 소스 선택, 실행, 결과 표시.
 */

import { useCallback, useEffect, useState } from "react";
import { api, type SimulationResult, type SimulationQuota } from "@/lib/api";

const SAMPLE_OPTIONS = [
  { id: "sample_small_si", label: "소규모 SI (5천만원, 서류심사)" },
  { id: "sample_mid_consulting", label: "중규모 컨설팅 (3억원, 기술+가격)" },
  { id: "sample_large_isp", label: "대규모 ISP (15억원, 발표심사)" },
];

interface SimulationRunnerProps {
  promptId: string;
  promptText?: string | null;
}

export default function SimulationRunner({ promptId, promptText }: SimulationRunnerProps) {
  const [dataSource, setDataSource] = useState<"sample" | "project" | "custom">("sample");
  const [sampleId, setSampleId] = useState("sample_mid_consulting");
  const [runQuality, setRunQuality] = useState(true);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
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
      const res = await api.prompts.simulate(promptId, {
        prompt_text: promptText ?? undefined,
        data_source: dataSource,
        data_source_id: dataSource === "sample" ? sampleId : undefined,
        run_quality_check: runQuality,
      });
      setResult(res);
      fetchQuota();
    } catch (e) {
      setError(e instanceof Error ? e.message : "시뮬레이션 실패");
    }
    setRunning(false);
  };

  return (
    <div className="space-y-4">
      {/* 입력 설정 */}
      <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 space-y-4">
        <h2 className="text-sm font-semibold">입력 설정</h2>

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
            className="px-6 py-2 bg-[#3ecf8e] text-black rounded-lg text-xs font-bold hover:bg-[#35b87d] disabled:opacity-50 transition-colors"
          >
            {running ? "실행 중..." : "시뮬레이션 실행"}
          </button>
          {quota && (
            <span className="text-xs text-[#8c8c8c]">
              잔여: {quota.remaining}/{quota.daily_limit}회
            </span>
          )}
        </div>

        {error && <div className="text-xs text-[#ff6b6b]">{error}</div>}
      </section>

      {/* 결과 */}
      {result && <SimResultCard result={result} />}
    </div>
  );
}

export function SimResultCard({
  result,
  compact,
  label,
}: {
  result: SimulationResult;
  compact?: boolean;
  label?: string;
}) {
  return (
    <section className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 space-y-4 ${compact ? "text-xs" : ""}`}>
      {label && <h3 className="text-xs font-semibold text-[#8c8c8c] mb-2">{label}</h3>}

      <div className="flex flex-wrap gap-4 text-xs text-[#8c8c8c]">
        <span>입력: {result.tokens_input} 토큰</span>
        <span>출력: {result.tokens_output} 토큰</span>
        <span>시간: {(result.duration_ms / 1000).toFixed(1)}s</span>
        {result.format_valid ? (
          <span className="text-[#3ecf8e]">형식 정상</span>
        ) : (
          <span className="text-[#ff6b6b]">형식 오류: {result.format_errors.join(", ")}</span>
        )}
        {result.variables_missing.length > 0 && (
          <span className="text-[#f5a623]">누락 변수: {result.variables_missing.join(", ")}</span>
        )}
      </div>

      {result.quality_score != null && result.quality_detail && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <QualityCard label="적합성" value={result.quality_detail.compliance} max={25} />
          <QualityCard label="전략 정합성" value={result.quality_detail.strategy} max={25} />
          <QualityCard label="품질" value={result.quality_detail.quality} max={25} />
          <QualityCard label="신뢰성" value={result.quality_detail.trustworthiness} max={25} />
          <div className="bg-[#111] rounded-lg p-3 border border-[#262626]">
            <div className="text-xs text-[#8c8c8c]">총점</div>
            <div className={`text-lg font-bold ${
              result.quality_score >= 80 ? "text-[#3ecf8e]"
                : result.quality_score >= 60 ? "text-[#f5a623]"
                : "text-[#ff6b6b]"
            }`}>
              {result.quality_score}/100
            </div>
          </div>
        </div>
      )}

      <div>
        <h3 className="text-xs font-semibold mb-2">AI 출력</h3>
        <pre className="p-3 bg-[#0a0a0a] rounded-lg text-xs text-[#8c8c8c] overflow-x-auto max-h-96 whitespace-pre-wrap">
          {result.output_text}
        </pre>
      </div>
    </section>
  );
}

function QualityCard({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = (value / max) * 100;
  return (
    <div className="bg-[#111] rounded-lg p-3 border border-[#262626]">
      <div className="text-xs text-[#8c8c8c]">{label}</div>
      <div className="text-sm font-bold mt-0.5">{value}/{max}</div>
      <div className="h-1 bg-[#262626] rounded-full mt-2">
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            backgroundColor: pct >= 80 ? "#3ecf8e" : pct >= 60 ? "#f5a623" : "#ff6b6b",
          }}
        />
      </div>
    </div>
  );
}
