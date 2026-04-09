"use client";

/**
 * 제안작업 시작 시 참여자 선택 모달
 *
 * 사용 예:
 * <ProposalMemberSelectionModal
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   onConfirm={handleStartProposal}
 *   teamMembers={[...]}
 *   isLoading={false}
 * />
 */

import { useCallback, useMemo, useState } from "react";

interface TeamMember {
  id: string;
  name: string;
  email: string;
}

interface ProposalMemberSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedMembers: string[]) => Promise<void>;
  teamMembers: TeamMember[];
  isLoading?: boolean;
}

export default function ProposalMemberSelectionModal({
  isOpen,
  onClose,
  onConfirm,
  teamMembers,
  isLoading = false,
}: ProposalMemberSelectionModalProps) {
  const [selectedMembers, setSelectedMembers] = useState<Set<string>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleToggleMember = useCallback((memberId: string) => {
    setSelectedMembers((prev) => {
      const next = new Set(prev);
      if (next.has(memberId)) {
        next.delete(memberId);
      } else {
        next.add(memberId);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedMembers.size === teamMembers.length) {
      setSelectedMembers(new Set());
    } else {
      setSelectedMembers(new Set(teamMembers.map((m) => m.id)));
    }
  }, [teamMembers, selectedMembers.size]);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      await onConfirm(Array.from(selectedMembers));
      setSelectedMembers(new Set());
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const isAllSelected = selectedMembers.size === teamMembers.length && teamMembers.length > 0;
  const isSomeSelected = selectedMembers.size > 0 && selectedMembers.size < teamMembers.length;

  if (!isOpen) return null;

  return (
    <>
      {/* 오버레이 */}
      <div
        className="fixed inset-0 z-40 bg-black/50"
        onClick={onClose}
        role="presentation"
      />

      {/* 모달 */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-[#111111] border border-[#262626] rounded-lg w-full max-w-md shadow-lg">
          {/* 헤더 */}
          <div className="px-6 py-4 border-b border-[#262626] flex items-center justify-between">
            <h2 className="text-base font-semibold text-[#ededed]">
              제안 팀원 선택
            </h2>
            <button
              onClick={onClose}
              className="text-[#8c8c8c] hover:text-[#ededed] transition-colors"
              aria-label="닫기"
            >
              ✕
            </button>
          </div>

          {/* 콘텐츠 */}
          <div className="px-6 py-4 max-h-[400px] overflow-y-auto">
            {/* 설명 */}
            <p className="text-sm text-[#8c8c8c] mb-4">
              이 제안작업에 참여할 팀원들을 선택해주세요.
            </p>

            {/* 전체 선택 */}
            <div className="mb-4 pb-4 border-b border-[#262626]">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  ref={(el) => {
                    if (el) el.indeterminate = isSomeSelected;
                  }}
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={handleSelectAll}
                  className="w-4 h-4 rounded border border-[#3ecf8e] cursor-pointer"
                  aria-label="모두 선택"
                />
                <span className="text-sm font-medium text-[#ededed]">
                  모두 선택
                </span>
              </label>
            </div>

            {/* 멤버 리스트 */}
            {teamMembers.length > 0 ? (
              <div className="space-y-2">
                {teamMembers.map((member) => (
                  <label
                    key={member.id}
                    className="flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-[#1a1a1a] transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedMembers.has(member.id)}
                      onChange={() => handleToggleMember(member.id)}
                      className="w-4 h-4 rounded border border-[#3ecf8e] cursor-pointer"
                      aria-label={`${member.name} 선택`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-[#ededed] truncate">
                        {member.name}
                      </div>
                      <div className="text-xs text-[#8c8c8c] truncate">
                        {member.email}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[#8c8c8c] text-sm">
                팀원이 없습니다
              </div>
            )}
          </div>

          {/* 푸터 */}
          <div className="px-6 py-4 border-t border-[#262626] flex items-center justify-between gap-2">
            <p className="text-xs text-[#8c8c8c]">
              {selectedMembers.size > 0
                ? `${selectedMembers.size}명 선택됨`
                : "선택한 멤버가 없습니다"}
            </p>
            <div className="flex gap-2">
              <button
                onClick={onClose}
                disabled={isSubmitting || isLoading}
                className="px-4 py-2 text-sm font-medium text-[#8c8c8c] hover:text-[#ededed] border border-[#262626] rounded transition-colors disabled:opacity-50"
              >
                취소
              </button>
              <button
                onClick={handleConfirm}
                disabled={
                  isSubmitting || isLoading || selectedMembers.size === 0
                }
                className="px-4 py-2 text-sm font-medium bg-[#3ecf8e] text-[#0f0f0f] rounded hover:bg-[#4fe0a0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting || isLoading ? "진행 중..." : "확인"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
