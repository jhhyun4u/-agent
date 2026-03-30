/**
 * FeedbackSummaryCard — STEP 8E Output Display
 *
 * Shows prioritized feedback: critical gaps, quick wins, strategic
 * recommendations, and score improvement projections from the
 * mock_evaluation_feedback_processor node.
 */

"use client";

import { useState } from "react";
import type { FeedbackSummary, FeedbackItem } from "@/lib/types/step8";

export interface FeedbackSummaryCardProps {
  data: FeedbackSummary | null;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export function FeedbackSummaryCard({
  data,
  isLoading = false,
  error = null,
  onRevalidate,
}: FeedbackSummaryCardProps) {
  const [expandedCategory, setExpandedCategory] = useState<"gaps" | "wins" | "section" | null>(
    null
  );
  const [selectedSection, setSelectedSection] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-emerald-50 to-transparent">
        <div className="h-6 w-48 bg-emerald-200 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-emerald-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-emerald-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">Failed to load feedback summary</p>
        <p className="text-xs text-red-600 mt-1">{error.message}</p>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="mt-2 px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
        <p className="text-sm text-gray-600">No feedback available</p>
      </div>
    );
  }

  const getEffortColor = (effort: string): string => {
    switch (effort) {
      case "quick":
        return "bg-green-100 text-green-800 border-green-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "complex":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const FeedbackItemRow = ({ item }: { item: FeedbackItem }) => (
    <div className="border rounded-lg p-3 bg-gray-50 hover:bg-gray-100 transition">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-medium text-sm text-gray-900">{item.section_title}</p>
          <p className="text-xs text-gray-600 mt-1">{item.issue_description}</p>
        </div>
        <div className="flex gap-2 ml-4 whitespace-nowrap">
          <span
            className={`px-2 py-1 text-xs font-semibold rounded border ${
              item.priority === "high"
                ? "bg-red-100 text-red-800 border-red-200"
                : item.priority === "medium"
                ? "bg-yellow-100 text-yellow-800 border-yellow-200"
                : "bg-green-100 text-green-800 border-green-200"
            }`}
          >
            {item.priority}
          </span>
          <span className={`px-2 py-1 text-xs font-semibold rounded border ${getEffortColor(item.estimated_effort)}`}>
            {item.estimated_effort}
          </span>
        </div>
      </div>
      <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
        <p className="text-xs text-blue-700">
          <span className="font-semibold">Action:</span> {item.recommended_action}
        </p>
      </div>
    </div>
  );

  const sectionIds = Object.keys(data.section_feedback);

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Feedback Summary</h3>
          <p className="text-sm text-gray-600 mt-1">Prioritized Improvement Actions</p>
        </div>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Re-generate feedback"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Key Findings */}
      <div className="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200">
        <p className="text-xs font-semibold text-blue-700 uppercase">Key Findings</p>
        <p className="text-sm text-gray-900 mt-2">{data.key_findings}</p>
      </div>

      {/* Score Improvement Projection */}
      <div className="p-4 rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-green-700 uppercase">Expected Improvement</p>
            <p className="text-sm text-gray-900 mt-1">
              If all recommendations are implemented
            </p>
          </div>
          <div className="text-3xl font-bold text-green-600">+{data.score_improvement_projection}</div>
        </div>
      </div>

      {/* Critical Gaps */}
      <div className="space-y-2">
        <button
          onClick={() =>
            setExpandedCategory(expandedCategory === "gaps" ? null : "gaps")
          }
          className="w-full flex items-center justify-between p-3 rounded-lg bg-red-50 border border-red-200 hover:bg-red-100 transition font-medium text-red-900"
        >
          <span className="flex items-center gap-2">
            🔴 Critical Gaps ({data.critical_gaps.length})
          </span>
          <span className={`transform transition ${expandedCategory === "gaps" ? "rotate-180" : ""}`}>
            ▼
          </span>
        </button>
        {expandedCategory === "gaps" && (
          <div className="space-y-2 pl-1">
            {data.critical_gaps.length === 0 ? (
              <p className="text-sm text-gray-600 italic">No critical gaps found</p>
            ) : (
              data.critical_gaps.map((item, idx) => (
                <FeedbackItemRow key={idx} item={item} />
              ))
            )}
          </div>
        )}
      </div>

      {/* Quick Wins */}
      <div className="space-y-2">
        <button
          onClick={() =>
            setExpandedCategory(expandedCategory === "wins" ? null : "wins")
          }
          className="w-full flex items-center justify-between p-3 rounded-lg bg-green-50 border border-green-200 hover:bg-green-100 transition font-medium text-green-900"
        >
          <span className="flex items-center gap-2">
            ⚡ Quick Wins ({data.quick_wins.length})
          </span>
          <span className={`transform transition ${expandedCategory === "wins" ? "rotate-180" : ""}`}>
            ▼
          </span>
        </button>
        {expandedCategory === "wins" && (
          <div className="space-y-2 pl-1">
            {data.quick_wins.length === 0 ? (
              <p className="text-sm text-gray-600 italic">No quick wins identified</p>
            ) : (
              data.quick_wins.map((item, idx) => (
                <FeedbackItemRow key={idx} item={item} />
              ))
            )}
          </div>
        )}
      </div>

      {/* Strategic Recommendations */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">💡 Strategic Recommendations</h4>
        <ul className="space-y-2">
          {data.strategic_recommendations.map((rec, idx) => (
            <li
              key={idx}
              className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-sm text-gray-900"
            >
              <span className="font-semibold text-indigo-600">{idx + 1}.</span> {rec}
            </li>
          ))}
        </ul>
      </div>

      {/* Section-Specific Feedback */}
      {sectionIds.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() =>
              setExpandedCategory(expandedCategory === "section" ? null : "section")
            }
            className="w-full flex items-center justify-between p-3 rounded-lg bg-purple-50 border border-purple-200 hover:bg-purple-100 transition font-medium text-purple-900"
          >
            <span className="flex items-center gap-2">
              📋 Section-Specific Feedback ({sectionIds.length})
            </span>
            <span className={`transform transition ${expandedCategory === "section" ? "rotate-180" : ""}`}>
              ▼
            </span>
          </button>
          {expandedCategory === "section" && (
            <div className="space-y-2 pl-1">
              {sectionIds.map((sectionId) => (
                <div key={sectionId}>
                  <button
                    onClick={() =>
                      setSelectedSection(selectedSection === sectionId ? null : sectionId)
                    }
                    className="w-full text-left p-3 rounded-lg bg-purple-100 border border-purple-300 hover:bg-purple-200 transition font-medium text-purple-900"
                  >
                    {data.section_feedback[sectionId]?.[0]?.section_title || sectionId}
                    <span className="float-right">
                      {selectedSection === sectionId ? "▲" : "▼"}
                    </span>
                  </button>
                  {selectedSection === sectionId && (
                    <div className="mt-2 space-y-2 pl-1">
                      {data.section_feedback[sectionId].map((item, idx) => (
                        <FeedbackItemRow key={idx} item={item} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Next Phase Guidance */}
      <div className="p-4 rounded-lg bg-orange-50 border border-orange-200">
        <p className="text-xs font-semibold text-orange-700 uppercase">Next Phase Guidance</p>
        <p className="text-sm text-gray-900 mt-2">{data.next_phase_guidance}</p>
      </div>

      {/* Metadata */}
      <div className="pt-2 border-t text-xs text-gray-500">
        Created: {new Date(data.created_at).toLocaleString()}
      </div>
    </div>
  );
}
