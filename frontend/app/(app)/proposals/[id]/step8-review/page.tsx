/**
 * STEP 8 Review Page
 *
 * /proposals/[id]/step8-review
 * Integrated view of all STEP 8 nodes (8A-8F) with AI issue flagging,
 * version history, and approval workflow.
 */

"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { useStep8Data } from "@/lib/hooks/useStep8Data";
import {
  NodeStatusDashboard,
  ReviewPanelEnhanced,
  VersionHistoryViewer,
} from "@/components/step8";
import type { VersionMetadata } from "@/components/step8";

export default function Step8ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const {
    status,
    customerProfile,
    validationReport,
    consolidatedProposal,
    mockEvalResult,
    feedbackSummary,
    rewriteHistory,
    reviewPanelData,
    isLoading,
    error,
    refresh,
    validateNode,
  } = useStep8Data({
    proposalId: id,
    pollingInterval: 5000,
    autoFetch: true,
  });

  const [selectedVersionNode, setSelectedVersionNode] = useState<string | null>(null);
  const [showVersionViewer, setShowVersionViewer] = useState(false);

  // Mock version history (in production, fetch from backend)
  const mockVersions: Record<string, VersionMetadata[]> = {
    step_8a: [
      {
        version_id: "v1-abc123",
        node_name: "customer_profile_extract",
        version_number: 1,
        created_at: new Date().toISOString(),
        created_by: "system",
        size_bytes: 2048,
        description: "Initial customer profile extraction",
        change_summary: "Extracted stakeholder analysis",
      },
    ],
    step_8b: [
      {
        version_id: "v1-def456",
        node_name: "validation_report",
        version_number: 1,
        created_at: new Date().toISOString(),
        created_by: "system",
        size_bytes: 3072,
        description: "Initial validation scan",
        change_summary: "Found 3 issues requiring attention",
      },
    ],
    step_8c: [
      {
        version_id: "v1-ghi789",
        node_name: "proposal_consolidation",
        version_number: 1,
        created_at: new Date().toISOString(),
        created_by: "system",
        size_bytes: 4096,
        description: "Section consolidation",
        change_summary: "Merged duplicate sections",
      },
    ],
    step_8d: [
      {
        version_id: "v1-jkl012",
        node_name: "mock_evaluation",
        version_number: 1,
        created_at: new Date().toISOString(),
        created_by: "system",
        size_bytes: 2560,
        description: "5-dimension evaluation",
        change_summary: "Score: 78/100, Win probability: 72%",
      },
    ],
    step_8e: [
      {
        version_id: "v1-mno345",
        node_name: "feedback_processor",
        version_number: 1,
        created_at: new Date().toISOString(),
        created_by: "system",
        size_bytes: 3840,
        description: "Prioritized feedback generation",
        change_summary: "3 critical gaps, 2 quick wins identified",
      },
    ],
    step_8f: [
      {
        version_id: "v1-pqr678",
        node_name: "rewrite_history",
        version_number: 1,
        created_at: new Date().toISOString(),
        created_by: "system",
        size_bytes: 5120,
        description: "Rewrite iteration 1",
        change_summary: "Section 1: Executive Summary revised",
      },
    ],
  };

  if (loading && !status) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] text-[#ededed] flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-[#8c8c8c]">STEP 8 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      {/* 헤더 */}
      <header className="bg-[#111111] border-b border-[#262626] sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href={`/proposals/${id}`}
              className="text-[#8c8c8c] hover:text-[#ededed] transition-colors"
            >
              ← 뒤로
            </Link>
            <div>
              <h1 className="text-lg font-semibold text-[#ededed]">STEP 8 검토</h1>
              <p className="text-xs text-[#8c8c8c] mt-1">AI 강화 제안서 리뷰 및 최적화</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refresh()}
              disabled={isLoading}
              className="px-4 py-2 text-sm rounded-lg font-medium bg-[#262626] text-[#ededed] hover:bg-[#333333] disabled:opacity-50 transition-colors"
            >
              {isLoading ? "새로고침 중..." : "새로고침"}
            </button>
          </div>
        </div>
      </header>

      {/* 에러 상태 */}
      {error && (
        <div className="bg-[#1c1c1c] border-b border-red-500/30 px-6 py-4 text-sm text-red-400">
          <p className="font-medium mb-2">오류 발생</p>
          <p className="text-xs text-red-300/80">{error.message}</p>
        </div>
      )}

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* 노드 상태 대시보드 */}
        {status && (
          <section className="mb-12">
            <NodeStatusDashboard
              proposal_id={id}
              status={status}
              isLoading={isLoading}
              error={error}
              onValidateAll={() => {
                ["step_8a", "step_8b", "step_8c", "step_8d", "step_8e", "step_8f"].forEach(
                  (nodeId) => validateNode(nodeId)
                );
              }}
              onValidateNode={validateNode}
              onRevalidate={refresh}
            />
          </section>
        )}

        {/* AI 이슈 검토 패널 */}
        {reviewPanelData && (
          <section className="mb-12">
            <ReviewPanelEnhanced
              proposal_id={id}
              issues={reviewPanelData.issues}
              total_issues={reviewPanelData.total_issues}
              critical_count={reviewPanelData.critical_count}
              can_proceed={reviewPanelData.can_proceed}
              isLoading={isLoading}
              onApprove={() => {
                alert("제안서를 승인했습니다.");
                // TODO: Submit approval to backend
              }}
              onRequestChanges={(feedback) => {
                alert(`변경 요청을 제출했습니다:\n${feedback}`);
                // TODO: Submit feedback to backend
              }}
              onRewrite={() => {
                alert("재작성을 요청했습니다.");
                // TODO: Trigger rewrite in backend
              }}
            />
          </section>
        )}

        {/* 버전 히스토리 비교기 */}
        <section className="mb-12">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-[#ededed] mb-2">버전 히스토리</h2>
            <p className="text-sm text-[#8c8c8c]">각 노드의 버전 변경 이력과 차이점 비교</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {["step_8a", "step_8b", "step_8c", "step_8d", "step_8e", "step_8f"].map((nodeId) => (
              <div key={nodeId} className="border border-[#262626] rounded-lg overflow-hidden">
                <VersionHistoryViewer
                  node_name={nodeId}
                  versions={mockVersions[nodeId] || []}
                  onSelectVersion={(versionId) => {
                    setSelectedVersionNode(nodeId);
                    setShowVersionViewer(true);
                  }}
                  isLoading={isLoading}
                  error={error}
                  onRevalidate={refresh}
                />
              </div>
            ))}
          </div>
        </section>

        {/* 상세 피드백 및 다음 단계 */}
        {feedbackSummary && (
          <section className="mb-12">
            <div className="bg-[#111111] border border-[#262626] rounded-lg p-6">
              <h2 className="text-lg font-semibold text-[#ededed] mb-4">피드백 요약</h2>

              {/* 핵심 소견 */}
              <div className="mb-6 p-4 bg-[#1a1a1a] rounded-lg border border-[#262626]">
                <p className="text-sm text-[#8c8c8c] uppercase font-semibold mb-2">핵심 소견</p>
                <p className="text-sm text-[#ededed] leading-relaxed">
                  {feedbackSummary.key_findings}
                </p>
              </div>

              {/* 예상 개선율 */}
              <div className="mb-6 p-4 bg-green-500/10 rounded-lg border border-green-500/30">
                <p className="text-sm text-[#8c8c8c] uppercase font-semibold mb-2">예상 개선</p>
                <p className="text-3xl font-bold text-green-400">
                  +{feedbackSummary.score_improvement_projection}점
                </p>
                <p className="text-xs text-[#8c8c8c] mt-1">모든 권고사항 반영 시</p>
              </div>

              {/* 다음 단계 안내 */}
              <div className="p-4 bg-[#1a1a1a] rounded-lg border border-[#262626]">
                <p className="text-sm text-[#8c8c8c] uppercase font-semibold mb-2">다음 단계</p>
                <p className="text-sm text-[#ededed] leading-relaxed">
                  {feedbackSummary.next_phase_guidance}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* 빈 상태 */}
        {!status && !error && (
          <div className="text-center py-12">
            <p className="text-[#8c8c8c] text-sm mb-4">STEP 8 데이터가 아직 준비되지 않았습니다.</p>
            <button
              onClick={() => refresh()}
              className="text-xs text-[#3ecf8e] hover:underline transition-colors"
            >
              새로고침
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
