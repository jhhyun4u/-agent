"use client";

/**
 * 모의평가 결과 페이지 (§13-11)
 *
 * /proposals/[id]/evaluation
 * self_review 산출물에서 evaluation_simulation 데이터를 가져와 시각화
 */

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type EvaluationSimulation } from "@/lib/api";
import EvaluationView from "@/components/EvaluationView";

export default function EvaluationPage() {
  const { id } = useParams<{ id: string }>();
  const [evaluation, setEvaluation] = useState<EvaluationSimulation | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchEvaluation = useCallback(async () => {
    try {
      setLoading(true);
      // evaluation_simulation은 self_review 산출물에 포함
      const artifact = await api.artifacts.get(id, "self_review");
      const evalData = (artifact.data as Record<string, unknown>)
        .evaluation_simulation as EvaluationSimulation | undefined;
      if (evalData) {
        setEvaluation(evalData);
      } else {
        setError("모의평가 데이터가 아직 생성되지 않았습니다.");
      }
    } catch {
      setError("모의평가 데이터를 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchEvaluation();
  }, [fetchEvaluation]);

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      {/* 헤더 */}
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link
            href={`/proposals/${id}`}
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors shrink-0"
          >
            ← 프로젝트 상세
          </Link>
          <h1 className="text-sm font-semibold text-[#ededed] truncate flex-1">
            모의평가 결과
          </h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-6">
        {loading && (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            불러오는 중...
          </div>
        )}

        {!loading && error && (
          <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-8 text-center">
            <p className="text-sm text-[#8c8c8c] mb-4">{error}</p>
            <Link
              href={`/proposals/${id}`}
              className="text-xs text-[#3ecf8e] hover:underline"
            >
              프로젝트 상세로 돌아가기
            </Link>
          </div>
        )}

        {!loading && evaluation && (
          <EvaluationView proposalId={id} evaluation={evaluation} />
        )}
      </main>
    </div>
  );
}
