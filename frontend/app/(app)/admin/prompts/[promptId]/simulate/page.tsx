"use client";

/**
 * 프롬프트 시뮬레이션 샌드박스
 *
 * /admin/prompts/[promptId]/simulate
 * - 단독 실행 (SimulationRunner)
 * - A vs B 비교 (CompareView)
 */

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import SimulationRunner from "@/components/prompt/SimulationRunner";
import CompareView from "@/components/prompt/CompareView";

type Mode = "single" | "compare";

export default function SimulatePage() {
  const params = useParams();
  const promptId = decodeURIComponent(params.promptId as string);
  const [mode, setMode] = useState<Mode>("single");

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link
            href={`/admin/prompts/${encodeURIComponent(promptId)}`}
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
          >
            &larr; {promptId}
          </Link>
          <h1 className="text-sm font-semibold">시뮬레이션 샌드박스</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* 모드 토글 */}
        <div className="flex gap-1 bg-[#1c1c1c] rounded-lg p-1 w-fit">
          <button
            onClick={() => setMode("single")}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
              mode === "single"
                ? "bg-[#262626] text-[#ededed]"
                : "text-[#8c8c8c] hover:text-[#ededed]"
            }`}
          >
            단독 실행
          </button>
          <button
            onClick={() => setMode("compare")}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
              mode === "compare"
                ? "bg-[#262626] text-[#ededed]"
                : "text-[#8c8c8c] hover:text-[#ededed]"
            }`}
          >
            A vs B 비교
          </button>
        </div>

        {/* 모드별 컴포넌트 */}
        {mode === "single" && <SimulationRunner promptId={promptId} />}
        {mode === "compare" && <CompareView promptId={promptId} />}
      </main>
    </div>
  );
}
