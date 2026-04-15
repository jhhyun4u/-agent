/**
 * Government Guidelines Section View
 * Displays government guidelines and regulations retrieved from Vault
 */

import { AlertCircle } from "lucide-react";

interface Guideline {
  id: string;
  title: string;
  agency: string;
  category: string;
  content: string;
  effective_date?: string;
  reference_url?: string;
}

interface GovernmentGuidelinesViewProps {
  guidelines: Guideline[];
  isLoading: boolean;
  error?: string;
}

export default function GovernmentGuidelinesView({
  guidelines,
  isLoading,
  error,
}: GovernmentGuidelinesViewProps) {
  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div>
          <div className="font-medium text-red-400">오류 발생</div>
          <div className="text-sm text-red-300">{error}</div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-4 text-center text-[#b4b4b4]">
        <div className="text-sm">로드 중...</div>
      </div>
    );
  }

  if (guidelines.length === 0) {
    return (
      <div className="p-4 text-center text-[#b4b4b4]">
        <div className="text-sm">발주기관 지침이 없습니다</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {guidelines.map((guideline) => (
        <div
          key={guideline.id}
          className="p-3 bg-[#2d2d2d] border border-[#404040] rounded-lg hover:border-[#10a37f] transition-colors"
        >
          <div className="flex items-start justify-between gap-3 mb-2">
            <div>
              <h4 className="font-medium text-white">{guideline.title}</h4>
              <div className="flex gap-2 text-xs text-[#b4b4b4] mt-1">
                <span>{guideline.agency}</span>
                <span className="text-[#888888]">•</span>
                <span>{guideline.category}</span>
              </div>
            </div>
          </div>

          <p className="text-sm text-[#e5e5e5] mb-2 line-clamp-3">
            {guideline.content}
          </p>

          <div className="flex items-center justify-between gap-2 text-xs">
            {guideline.effective_date && (
              <span className="text-[#888888]">
                발효: {new Date(guideline.effective_date).toLocaleDateString("ko-KR")}
              </span>
            )}
            {guideline.reference_url && (
              <a
                href={guideline.reference_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#10a37f] hover:underline"
              >
                원문 보기
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
