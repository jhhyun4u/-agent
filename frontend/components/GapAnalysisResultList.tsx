"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, AlertCircle } from "lucide-react";
import type {
  GapAnalysisResult,
  GapLogicGap,
  GapWeakTransition,
} from "@/lib/api";

interface GapAnalysisResultListProps {
  gapAnalysis: GapAnalysisResult;
  className?: string;
}

/**
 * STEP 4A: 갭 분석 결과 리스트
 * 스토리라인 vs 실제 작성 내용 비교 결과 표시
 * 빠진 포인트, 논리 구멍, 약한 전환, 메시지 불일관성
 */
export function GapAnalysisResultList({
  gapAnalysis,
  className = "",
}: GapAnalysisResultListProps) {
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    missing: true,
    logic: true,
    transition: true,
    inconsistency: true,
  });

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // 갯수에 따른 색상
  const getCountColor = (count: number) => {
    if (count === 0) return "bg-green-900/40 text-green-300";
    if (count <= 3) return "bg-yellow-900/40 text-yellow-300";
    return "bg-red-900/40 text-red-300";
  };

  // 섹션 제목
  const SectionHeader = ({
    title,
    count,
    icon,
    sectionKey,
  }: {
    title: string;
    count: number;
    icon: React.ReactNode;
    sectionKey: string;
  }) => (
    <button
      onClick={() => toggleSection(sectionKey)}
      className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#1a1a1a] transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="text-[#3ecf8e]">{icon}</div>
        <span className="text-[#ededed] font-medium">{title}</span>
        <span className={`text-xs px-2.5 py-1 rounded-full font-bold ${getCountColor(count)}`}>
          {count}
        </span>
      </div>
      {expandedSections[sectionKey] ? (
        <ChevronUp className="w-5 h-5 text-[#808080]" />
      ) : (
        <ChevronDown className="w-5 h-5 text-[#808080]" />
      )}
    </button>
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 전체 평가 배너 */}
      {gapAnalysis.overall_assessment && (
        <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-300 mb-1">
                전체 평가
              </p>
              <p className="text-sm text-blue-200">
                {gapAnalysis.overall_assessment}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 빠진 핵심 포인트 */}
      <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg overflow-hidden">
        <SectionHeader
          title="빠진 핵심 포인트"
          count={gapAnalysis.missing_points?.length || 0}
          icon="📍"
          sectionKey="missing"
        />
        {expandedSections["missing"] && gapAnalysis.missing_points && (
          <div className="px-4 py-3 space-y-2 border-t border-[#262626]">
            {gapAnalysis.missing_points.length === 0 ? (
              <p className="text-sm text-[#808080]">없음</p>
            ) : (
              gapAnalysis.missing_points.map((point, idx) => (
                <div key={idx} className="flex gap-2 text-sm">
                  <span className="text-[#3ecf8e] font-bold flex-shrink-0">•</span>
                  <p className="text-[#ededed]">{point}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* 논리 구멍 */}
      <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg overflow-hidden">
        <SectionHeader
          title="논리 구멍 (연결 고리 단절)"
          count={gapAnalysis.logic_gaps?.length || 0}
          icon="🔗"
          sectionKey="logic"
        />
        {expandedSections["logic"] && gapAnalysis.logic_gaps && (
          <div className="px-4 py-3 space-y-3 border-t border-[#262626]">
            {gapAnalysis.logic_gaps.length === 0 ? (
              <p className="text-sm text-[#808080]">없음</p>
            ) : (
              gapAnalysis.logic_gaps.map((gap: GapLogicGap, idx: number) => (
                <div
                  key={idx}
                  className="bg-[#1a1a1a] border border-red-700/30 rounded p-3 space-y-1"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-medium text-red-400">
                      {gap.section}
                    </p>
                  </div>
                  <p className="text-sm text-[#ededed]">{gap.issue}</p>
                  <div className="bg-red-900/20 rounded p-2 mt-2">
                    <p className="text-xs text-red-300">
                      <span className="font-medium">영향:</span> {gap.impact}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* 약한 전환 (섹션 간) */}
      <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg overflow-hidden">
        <SectionHeader
          title="약한 전환 (섹션 간)"
          count={gapAnalysis.weak_transitions?.length || 0}
          icon="➡️"
          sectionKey="transition"
        />
        {expandedSections["transition"] &&
          gapAnalysis.weak_transitions && (
            <div className="px-4 py-3 space-y-3 border-t border-[#262626]">
              {gapAnalysis.weak_transitions.length === 0 ? (
                <p className="text-sm text-[#808080]">없음</p>
              ) : (
                gapAnalysis.weak_transitions.map(
                  (trans: GapWeakTransition, idx: number) => (
                    <div
                      key={idx}
                      className="bg-[#1a1a1a] border border-yellow-700/30 rounded p-3 space-y-1"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 text-xs font-medium">
                          <span className="px-2 py-1 bg-yellow-900/30 text-yellow-300 rounded">
                            {trans.from_section}
                          </span>
                          <span className="text-[#808080]">→</span>
                          <span className="px-2 py-1 bg-yellow-900/30 text-yellow-300 rounded">
                            {trans.to_section}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-[#ededed]">{trans.issue}</p>
                    </div>
                  ),
                )
              )}
            </div>
          )}
      </div>

      {/* 메시지 불일관성 */}
      <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg overflow-hidden">
        <SectionHeader
          title="메시지 불일관성"
          count={gapAnalysis.inconsistencies?.length || 0}
          icon="⚠️"
          sectionKey="inconsistency"
        />
        {expandedSections["inconsistency"] &&
          gapAnalysis.inconsistencies && (
            <div className="px-4 py-3 space-y-2 border-t border-[#262626]">
              {gapAnalysis.inconsistencies.length === 0 ? (
                <p className="text-sm text-[#808080]">없음</p>
              ) : (
                gapAnalysis.inconsistencies.map((item, idx) => (
                  <div key={idx} className="flex gap-2 text-sm">
                    <span className="text-orange-400 font-bold flex-shrink-0">
                      !
                    </span>
                    <p className="text-[#ededa]">{item}</p>
                  </div>
                ))
              )}
            </div>
          )}
      </div>

      {/* 권장 조치사항 */}
      {gapAnalysis.recommended_actions &&
        gapAnalysis.recommended_actions.length > 0 && (
          <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-4">
            <p className="text-sm font-medium text-green-300 mb-2">권장 조치</p>
            <ul className="space-y-2">
              {gapAnalysis.recommended_actions.map((action, idx) => (
                <li key={idx} className="flex gap-2 text-sm text-green-200">
                  <span className="text-green-400 font-bold flex-shrink-0">
                    ✓
                  </span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
    </div>
  );
}
