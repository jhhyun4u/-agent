"use client";

import React, { useState } from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { SectionDiagnostic, DiagnosticIssue } from "@/lib/api";

interface DiagnosticScoreCardProps {
  diagnostic: SectionDiagnostic;
  className?: string;
}

/**
 * STEP 4A: 섹션 품질 진단 카드
 * 4축 레이더 차트 (규격, 스토리라인, 근거, 차별성) + 점수 + 권고사항 + 이슈 목록
 */
export function DiagnosticScoreCard({
  diagnostic,
  className = "",
}: DiagnosticScoreCardProps) {
  const [expandedIssues, setExpandedIssues] = useState(false);

  // 4축 점수 계산
  // overall_score = compliance(25) + storyline(0-25) + evidence(0-25) + diff(0-25)
  // compliance_ok? 25 : 0
  // storyline_score = (overall_score * 4) - (compliance_ok ? 25 : 0) - (evidence_score * 0.25) - (diff_score * 0.25)
  // → normalize to 0-100
  const complianceScore = diagnostic.compliance_ok ? 100 : 0;
  const storylineScore = Math.max(
    0,
    Math.min(
      100,
      ((diagnostic.overall_score * 4 -
        (diagnostic.compliance_ok ? 25 : 0) -
        diagnostic.evidence_score * 0.25 -
        diagnostic.diff_score * 0.25) *
        4) /
        25,
    ),
  );

  const radarData = [
    { axis: "규격 준수", score: complianceScore, target: 75 },
    { axis: "스토리라인 반영", score: storylineScore, target: 75 },
    { axis: "근거 충족", score: diagnostic.evidence_score, target: 75 },
    { axis: "차별성", score: diagnostic.diff_score, target: 75 },
  ];

  // 권고사항 색상
  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case "approve":
        return "bg-green-900/30 text-green-200 border-green-700";
      case "modify":
        return "bg-yellow-900/30 text-yellow-200 border-yellow-700";
      case "rework":
        return "bg-red-900/30 text-red-200 border-red-700";
      default:
        return "bg-gray-900/30 text-gray-200 border-gray-700";
    }
  };

  // 점수 색상
  const getScoreColor = (score: number) => {
    if (score >= 75) return "text-green-400";
    if (score >= 50) return "text-yellow-400";
    return "text-red-400";
  };

  // 심각도 색상
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-900/40 text-red-300 border-red-700";
      case "high":
        return "bg-orange-900/40 text-orange-300 border-orange-700";
      case "medium":
        return "bg-yellow-900/40 text-yellow-300 border-yellow-700";
      case "low":
        return "bg-blue-900/40 text-blue-300 border-blue-700";
      default:
        return "bg-gray-900/40 text-gray-300 border-gray-700";
    }
  };

  const getRecommendationLabel = (rec: string) => {
    switch (rec) {
      case "approve":
        return "승인 가능";
      case "modify":
        return "수정 필요";
      case "rework":
        return "재작업";
      default:
        return rec;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 섹션 정보 + 전체 점수 */}
      <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg p-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-[#ededed]">
              {diagnostic.section_title}
            </h3>
            {diagnostic.section_id && (
              <p className="text-sm text-[#808080]">{diagnostic.section_id}</p>
            )}
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${getScoreColor(diagnostic.overall_score)}`}>
              {diagnostic.overall_score.toFixed(1)}
            </div>
            <p className="text-xs text-[#808080]">전체 점수</p>
          </div>
        </div>

        {/* 권고사항 배지 */}
        <div className="flex gap-2 mb-4">
          <span
            className={`px-3 py-1 rounded border text-sm font-medium ${getRecommendationColor(
              diagnostic.recommendation,
            )}`}
          >
            {getRecommendationLabel(diagnostic.recommendation)}
          </span>
        </div>

        {/* 4축 레이더 차트 */}
        <div className="bg-[#1a1a1a] rounded p-4 mb-4">
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#404040" />
              <PolarAngleAxis
                dataKey="axis"
                stroke="#808080"
                tick={{ fill: "#808080", fontSize: 12 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                stroke="#404040"
                tick={{ fill: "#808080", fontSize: 11 }}
              />
              <Radar
                name="점수"
                dataKey="score"
                stroke="#3ecf8e"
                fill="#3ecf8e"
                fillOpacity={0.25}
              />
              <Radar
                name="목표"
                dataKey="target"
                stroke="#808080"
                fill="none"
                strokeDasharray="5 5"
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* 점수 세부 항목 */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          {radarData.map((item) => (
            <div
              key={item.axis}
              className="bg-[#1a1a1a] rounded p-2 text-center border border-[#262626]"
            >
              <p className="text-xs text-[#808080] mb-1">{item.axis}</p>
              <p className={`text-lg font-bold ${getScoreColor(item.score)}`}>
                {item.score.toFixed(0)}
              </p>
            </div>
          ))}
        </div>

        {/* 스토리라인 갭 (있으면) */}
        {diagnostic.storyline_gap && (
          <div className="bg-yellow-900/20 border border-yellow-700/50 rounded p-3 text-sm text-yellow-300">
            <p className="font-medium mb-1">스토리라인 갭:</p>
            <p>{diagnostic.storyline_gap}</p>
          </div>
        )}
      </div>

      {/* 이슈 목록 (접을 수 있음) */}
      {diagnostic.issues && diagnostic.issues.length > 0 && (
        <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg overflow-hidden">
          <button
            onClick={() => setExpandedIssues(!expandedIssues)}
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#1a1a1a] transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-[#ededed] font-medium">
                식별된 이슈
              </span>
              <span className="bg-red-900/40 text-red-300 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                {diagnostic.issues.length}
              </span>
            </div>
            {expandedIssues ? (
              <ChevronUp className="w-5 h-5 text-[#808080]" />
            ) : (
              <ChevronDown className="w-5 h-5 text-[#808080]" />
            )}
          </button>

          {expandedIssues && (
            <div className="px-4 py-3 space-y-3 border-t border-[#262626]">
              {diagnostic.issues.map((issue: DiagnosticIssue, idx: number) => (
                <div
                  key={idx}
                  className={`rounded p-3 border ${getSeverityColor(issue.severity)}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-sm font-medium">{issue.type}</span>
                    <span className={`text-xs px-2 py-1 rounded ${getSeverityColor(issue.severity)}`}>
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm mb-2">{issue.description}</p>
                  <div className="bg-black/30 rounded p-2 text-sm">
                    <p className="text-[#808080] text-xs mb-1">수정 가이드:</p>
                    <p className="text-[#ededed]">{issue.fix_guidance}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
