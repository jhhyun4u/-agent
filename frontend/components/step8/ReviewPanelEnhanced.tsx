/**
 * ReviewPanelEnhanced — AI-Powered Review Interface
 *
 * Enhanced review panel with AI issue flagging, inline feedback,
 * and action buttons for STEP 8 workflow integration.
 * Integrates with existing ReviewPanel component.
 */

"use client";

import { useState } from "react";
import type { AIIssueFlag, ReviewPanelData } from "@/lib/types/step8";

export interface ReviewPanelEnhancedProps {
  proposal_id: string;
  issues: AIIssueFlag[];
  total_issues: number;
  critical_count: number;
  can_proceed: boolean;
  onApprove?: () => void;
  onRequestChanges?: (feedback: string) => void;
  onRewrite?: () => void;
  isLoading?: boolean;
}

export function ReviewPanelEnhanced({
  proposal_id,
  issues,
  total_issues,
  critical_count,
  can_proceed,
  onApprove,
  onRequestChanges,
  onRewrite,
  isLoading = false,
}: ReviewPanelEnhancedProps) {
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);

  const getSeverityColor = (severity: "critical" | "major" | "minor") => {
    switch (severity) {
      case "critical":
        return {
          bg: "bg-red-50",
          border: "border-red-300",
          badge: "bg-red-100 text-red-800 border-red-200",
          dot: "bg-red-600",
        };
      case "major":
        return {
          bg: "bg-orange-50",
          border: "border-orange-300",
          badge: "bg-orange-100 text-orange-800 border-orange-200",
          dot: "bg-orange-600",
        };
      case "minor":
        return {
          bg: "bg-yellow-50",
          border: "border-yellow-300",
          badge: "bg-yellow-100 text-yellow-800 border-yellow-200",
          dot: "bg-yellow-600",
        };
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "compliance":
        return "⚖️";
      case "clarity":
        return "💭";
      case "consistency":
        return "🔄";
      case "style":
        return "✨";
      case "strategy":
        return "🎯";
      default:
        return "📌";
    }
  };

  const majorIssues = issues.filter((i) => i.severity === "critical" || i.severity === "major");
  const minorIssues = issues.filter((i) => i.severity === "minor");
  const byCategory = issues.reduce(
    (acc, issue) => {
      if (!acc[issue.category]) acc[issue.category] = [];
      acc[issue.category].push(issue);
      return acc;
    },
    {} as Record<string, AIIssueFlag[]>
  );

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-violet-50 to-purple-50">
        <div className="h-6 w-48 bg-violet-200 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-violet-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-violet-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">AI Review</h3>
          <p className="text-sm text-gray-600">Smart issue detection & recommendations</p>
        </div>
        <div
          className={`px-3 py-1 rounded-full font-medium text-sm ${
            can_proceed
              ? "bg-green-100 text-green-800 border border-green-300"
              : "bg-red-100 text-red-800 border border-red-300"
          }`}
        >
          {can_proceed ? "✓ Ready" : "⚠ Issues"}
        </div>
      </div>

      {/* Issue Summary */}
      <div className="grid grid-cols-3 gap-3 py-3 border rounded-lg bg-gradient-to-r from-violet-50 to-purple-50">
        <div className="text-center p-3">
          <p className="text-2xl font-bold text-red-600">{critical_count}</p>
          <p className="text-xs font-semibold text-gray-600 uppercase mt-1">Critical</p>
        </div>
        <div className="text-center p-3">
          <p className="text-2xl font-bold text-orange-600">
            {issues.filter((i) => i.severity === "major").length}
          </p>
          <p className="text-xs font-semibold text-gray-600 uppercase mt-1">Major</p>
        </div>
        <div className="text-center p-3">
          <p className="text-2xl font-bold text-yellow-600">
            {minorIssues.length}
          </p>
          <p className="text-xs font-semibold text-gray-600 uppercase mt-1">Minor</p>
        </div>
      </div>

      {/* Issues by Category */}
      {Object.entries(byCategory).length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700">Issues by Category</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(byCategory).map(([category, categoryIssues]) => (
              <div
                key={category}
                className="p-3 rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getCategoryIcon(category)}</span>
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {category}
                    </span>
                  </div>
                  <span className="px-2 py-1 bg-gray-300 text-gray-800 text-xs font-bold rounded">
                    {categoryIssues.length}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Major Issues List */}
      {majorIssues.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">
            🔴 Critical & Major Issues ({majorIssues.length})
          </h4>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {majorIssues.map((issue) => {
              const colors = getSeverityColor(issue.severity);
              return (
                <div
                  key={issue.issue_id}
                  className={`border rounded-lg p-3 cursor-pointer transition ${colors.bg} ${colors.border} hover:shadow-sm`}
                  onClick={() =>
                    setSelectedIssue(selectedIssue === issue.issue_id ? null : issue.issue_id)
                  }
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${colors.dot}`} />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-gray-900">
                        {issue.description}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        📍 Section: {issue.section_id}
                      </p>
                      {issue.flagged_text && (
                        <p className="text-xs text-gray-700 mt-2 p-2 bg-white rounded border border-gray-300 font-mono line-clamp-2">
                          "{issue.flagged_text}"
                        </p>
                      )}
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded border whitespace-nowrap flex-shrink-0 ${colors.badge}`}
                    >
                      {issue.severity}
                    </span>
                  </div>

                  {selectedIssue === issue.issue_id && (
                    <div className="mt-3 pt-3 border-t space-y-2">
                      <div>
                        <p className="text-xs font-semibold text-gray-700 uppercase">
                          Category
                        </p>
                        <p className="text-sm text-gray-900 mt-1 capitalize">
                          {getCategoryIcon(issue.category)} {issue.category}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-blue-700 uppercase">
                          Suggestion
                        </p>
                        <p className="text-sm text-gray-900 mt-1 bg-blue-50 p-2 rounded border border-blue-200">
                          {issue.suggestion}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Minor Issues Collapsible */}
      {minorIssues.length > 0 && (
        <details className="group border rounded-lg">
          <summary className="p-3 bg-yellow-50 border-yellow-200 cursor-pointer hover:bg-yellow-100 transition font-medium text-yellow-900 flex items-center gap-2">
            <span>➖ Minor Issues ({minorIssues.length})</span>
            <span className="group-open:rotate-180 transition ml-auto">▼</span>
          </summary>
          <div className="space-y-2 p-3 border-t border-yellow-200 max-h-64 overflow-y-auto bg-yellow-50">
            {minorIssues.map((issue) => (
              <div
                key={issue.issue_id}
                className="p-2 bg-white rounded border border-yellow-200 text-sm text-gray-800"
              >
                <p className="font-medium">{issue.description}</p>
                <p className="text-xs text-gray-600 mt-1">{issue.suggestion}</p>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* No Issues State */}
      {total_issues === 0 && (
        <div className="p-4 rounded-lg bg-green-50 border border-green-200">
          <p className="text-sm text-green-800 font-medium">✓ No issues detected</p>
          <p className="text-xs text-green-700 mt-1">This section is ready for approval.</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col gap-2 pt-3 border-t">
        <div className="flex gap-2">
          {onApprove && (
            <button
              onClick={onApprove}
              disabled={!can_proceed}
              className={`flex-1 px-4 py-2 rounded font-medium transition ${
                can_proceed
                  ? "bg-green-600 text-white hover:bg-green-700"
                  : "bg-gray-200 text-gray-500 cursor-not-allowed"
              }`}
              title={can_proceed ? "Approve this section" : "Resolve critical issues first"}
            >
              ✓ Approve
            </button>
          )}

          {onRewrite && (
            <button
              onClick={onRewrite}
              className="flex-1 px-4 py-2 rounded font-medium bg-blue-600 text-white hover:bg-blue-700 transition"
              title="Rewrite this section based on feedback"
            >
              ↻ Rewrite
            </button>
          )}
        </div>

        {onRequestChanges && (
          <button
            onClick={() => setShowFeedbackForm(!showFeedbackForm)}
            className="w-full px-4 py-2 rounded font-medium bg-orange-600 text-white hover:bg-orange-700 transition"
          >
            {showFeedbackForm ? "Cancel" : "Request Changes"}
          </button>
        )}
      </div>

      {/* Feedback Form */}
      {showFeedbackForm && onRequestChanges && (
        <div className="space-y-3 pt-3 border-t">
          <div>
            <label className="text-sm font-semibold text-gray-700">
              Feedback & Instructions
            </label>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Describe the changes you'd like to see..."
              className="w-full mt-2 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
              rows={4}
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                onRequestChanges(feedbackText);
                setFeedbackText("");
                setShowFeedbackForm(false);
              }}
              disabled={!feedbackText.trim()}
              className="flex-1 px-4 py-2 rounded font-medium bg-orange-600 text-white hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Submit Feedback
            </button>
            <button
              onClick={() => {
                setFeedbackText("");
                setShowFeedbackForm(false);
              }}
              className="px-4 py-2 rounded font-medium bg-gray-200 text-gray-800 hover:bg-gray-300 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Status Info */}
      <div className="text-xs text-gray-500 border-t pt-2">
        <p>AI powered by Claude • Real-time issue detection • {total_issues} total issues</p>
      </div>
    </div>
  );
}
