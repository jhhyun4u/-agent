"use client";

import { ProposalSummary } from "@/lib/api";
import { getStepInfo, formatDeadline, formatBudget, deriveStatus } from "@/lib/proposals-utils";
import { useState, useEffect } from "react";

interface TeamMember {
  id: string;
  name: string;
  email?: string;
}

interface ProposalDetailModalProps {
  proposal: ProposalSummary | null;
  isOpen: boolean;
  onClose: () => void;
  onStartWork?: () => void;
  isStarting?: boolean;
  teamMembers?: TeamMember[];
  onSelectOwner?: (ownerId: string) => Promise<void>;
}

export function ProposalDetailModal({ proposal, isOpen, onClose, onStartWork, isStarting, teamMembers = [], onSelectOwner }: ProposalDetailModalProps) {
  const [showOwnerSelection, setShowOwnerSelection] = useState(false);
  const [selectedOwnerId, setSelectedOwnerId] = useState<string | null>(null);
  const [selectingOwner, setSelectingOwner] = useState(false);

  useEffect(() => {
    if (proposal?.owner_id) {
      setSelectedOwnerId(proposal.owner_id);
    }
  }, [proposal?.owner_id]);

  const handleSelectOwner = async (ownerId: string) => {
    setSelectingOwner(true);
    try {
      await onSelectOwner?.(ownerId);
      setSelectedOwnerId(ownerId);
      setShowOwnerSelection(false);
    } catch (err) {
      console.error("담당자 선택 실패:", err);
    } finally {
      setSelectingOwner(false);
    }
  };

  if (!isOpen || !proposal) return null;

  const stepInfo = getStepInfo(proposal.current_phase);
  const dl = formatDeadline(proposal.deadline);
  const st = deriveStatus(proposal);

  return (
    <>
      {/* 배경 오버레이 */}
      <div
        className="fixed inset-0 bg-black/60 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* 모달 창 */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-[#1c1c1c] border border-[#262626] rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 헤더 */}
          <div className="sticky top-0 bg-[#0f0f0f] border-b border-[#262626] px-6 py-4 flex items-start justify-between">
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-[#ededed]">{proposal.title}</h2>
              <p className="text-xs text-[#5c5c5c] mt-1">{proposal.client_name || "미지정"}</p>
            </div>
            <button
              onClick={onClose}
              className="text-[#5c5c5c] hover:text-[#ededed] transition-colors p-1"
            >
              ✕
            </button>
          </div>

          {/* 콘텐츠 */}
          <div className="p-6 space-y-6">
            {/* 기본 정보 */}
            <section>
              <h3 className="text-sm font-semibold text-[#ededed] mb-3">기본 정보</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">공고번호</p>
                  <p className="text-sm text-[#ededed]">{proposal.bid_no || "미지정"}</p>
                </div>
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">상태</p>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${st.dotColor}`} />
                    <span className={`text-sm font-medium ${st.textColor}`}>{st.label}</span>
                  </div>
                </div>
              </div>
            </section>

            {/* 분석 정보 */}
            <section>
              <h3 className="text-sm font-semibold text-[#ededed] mb-3">분석 정보</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">진행 단계</p>
                  <p className="text-sm text-[#ededed]">{stepInfo.label}</p>
                  <div className="flex gap-0.5 mt-1">
                    {[1, 2, 3, 4, 5, 6, 7].map((s) => (
                      <div
                        key={s}
                        className={`flex-1 h-1 rounded-full ${
                          s <= stepInfo.step ? "bg-[#3ecf8e]" : "bg-[#262626]"
                        }`}
                      />
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">점수</p>
                  <p className="text-sm text-[#ededed]">{proposal.score || "—"}</p>
                </div>
              </div>
            </section>

            {/* 예산 정보 */}
            <section>
              <h3 className="text-sm font-semibold text-[#ededed] mb-3">예산 정보</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">예정가</p>
                  <p className="text-sm text-[#ededed]">{formatBudget(proposal.budget)}</p>
                </div>
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">입찰가</p>
                  {proposal.bid_amount ? (
                    <p className="text-sm text-[#3ecf8e] font-medium">{formatBudget(proposal.bid_amount)}</p>
                  ) : (
                    <p className="text-sm text-[#5c5c5c]">미결정</p>
                  )}
                </div>
              </div>
            </section>

            {/* 일정 정보 */}
            <section>
              <h3 className="text-sm font-semibold text-[#ededed] mb-3">일정 정보</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">마감일</p>
                  <p
                    className={`text-sm ${dl.urgent ? "text-red-400 font-semibold" : "text-[#ededed]"}`}
                  >
                    {dl.text}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">생성일</p>
                  <p className="text-sm text-[#ededed]">
                    {proposal.created_at
                      ? new Date(proposal.created_at).toLocaleDateString("ko-KR")
                      : "—"}
                  </p>
                </div>
              </div>
            </section>

            {/* 담당자 정보 (작업대기 상태일 때) */}
            {proposal.status === "initialized" && (
              <section>
                <h3 className="text-sm font-semibold text-[#ededed] mb-3">담당자</h3>
                <div className="flex items-center justify-between gap-3 p-3 bg-[#262626] rounded-lg border border-[#363636]">
                  <div>
                    <p className="text-xs text-[#5c5c5c] mb-1">지정된 담당자</p>
                    <p className="text-sm font-medium text-[#ededed]">
                      {selectedOwnerId
                        ? teamMembers.find(m => m.id === selectedOwnerId)?.name || "—"
                        : "미지정"}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowOwnerSelection(!showOwnerSelection)}
                    disabled={selectingOwner}
                    className="px-3 py-1.5 bg-[#3ecf8e]/20 hover:bg-[#3ecf8e]/30 disabled:opacity-50 text-[#3ecf8e] text-xs font-medium rounded-lg transition-colors"
                  >
                    {selectingOwner ? "지정 중..." : "변경"}
                  </button>
                </div>

                {/* 담당자 선택 UI */}
                {showOwnerSelection && (
                  <div className="mt-3 p-3 bg-[#1c1c1c] border border-[#262626] rounded-lg space-y-2">
                    {teamMembers.length === 0 ? (
                      <p className="text-xs text-[#5c5c5c] py-2">팀 멤버 정보를 불러올 수 없습니다</p>
                    ) : (
                      <>
                        {teamMembers.map((member) => (
                          <button
                            key={member.id}
                            onClick={() => handleSelectOwner(member.id)}
                            disabled={selectingOwner}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                              selectedOwnerId === member.id
                                ? "bg-[#3ecf8e]/20 text-[#3ecf8e] border border-[#3ecf8e]/40"
                                : "text-[#ededed] hover:bg-[#262626]"
                            } disabled:opacity-50`}
                          >
                            <p className="font-medium">{member.name}</p>
                            {member.email && (
                              <p className="text-xs text-[#5c5c5c]">{member.email}</p>
                            )}
                          </button>
                        ))}
                      </>
                    )}
                  </div>
                )}
              </section>
            )}

            {/* 추가 정보 */}
            {proposal.positioning && (
              <section>
                <h3 className="text-sm font-semibold text-[#ededed] mb-3">추가 정보</h3>
                <div>
                  <p className="text-xs text-[#5c5c5c] mb-1">포지셔닝</p>
                  <p className="text-sm text-[#ededed]">{proposal.positioning}</p>
                </div>
              </section>
            )}
          </div>

          {/* 푸터 */}
          <div className="border-t border-[#262626] px-6 py-4 bg-[#0f0f0f] flex justify-end gap-2">
            {proposal.status === "initialized" && onStartWork && (
              <button
                onClick={onStartWork}
                disabled={isStarting}
                className="px-4 py-2 bg-[#3ecf8e] text-[#0f0f0f] rounded-lg text-sm font-medium hover:bg-[#5ae0a8] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isStarting ? "진행 중..." : "제안작업 착수"}
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[#262626] text-[#ededed] rounded-lg text-sm hover:bg-[#363636] transition-colors"
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
