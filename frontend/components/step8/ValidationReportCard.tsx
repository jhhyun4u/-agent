/**
 * ValidationReportCard — STEP 8B Output Display
 *
 * Shows validation results: quality score, compliance status, issues list
 * (critical/major/minor) from the proposal_section_validator node.
 */

"use client";

import { useState } from "react";
import type { ValidationReport, ValidationIssue } from "@/lib/types/step8";

export interface ValidationReportCardProps {
  data: ValidationReport | null;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export function ValidationReportCard({
  data,
  isLoading = false,
  error = null,
  onRevalidate,
}: ValidationReportCardProps) {
  const [selectedIssue, setSelectedIssue] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-amber-50 to-transparent">
        <div className="h-6 w-48 bg-amber-200 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-amber-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-amber-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">Failed to load validation report</p>
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
        <p className="text-sm text-gray-600">No validation report available</p>
      </div>
    );
  }

  const getScoreColor = (score: number): string => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (score: number): string => {
    if (score >= 80) return "bg-green-50";
    if (score >= 60) return "bg-yellow-50";
    return "bg-red-50";
  };

  const getSeverityColor = (
    severity: "critical" | "major" | "minor",
  ): string => {
    switch (severity) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-200";
      case "major":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "minor":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
    }
  };

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header & Status */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Validation Report
          </h3>
          <p
            className={`text-sm font-medium mt-1 ${
              data.pass_validation ? "text-green-600" : "text-red-600"
            }`}
          >
            {data.pass_validation ? "✓ Passed" : "✗ Issues Found"}
          </p>
        </div>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Re-validate proposal"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Quality Score Gauge */}
      <div className={`p-4 rounded-lg ${getScoreBg(data.quality_score)}`}>
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-600 uppercase">
              Quality Score
            </p>
            <p
              className={`text-4xl font-bold mt-2 ${getScoreColor(data.quality_score)}`}
            >
              {data.quality_score}
            </p>
            <p className="text-xs text-gray-600 mt-1">/ 100</p>
          </div>
          {/* Compliance Status */}
          <div className="text-right">
            <p className="text-xs font-semibold text-gray-600 uppercase">
              Compliance
            </p>
            <p
              className={`text-sm font-medium mt-2 ${
                data.compliance_status === "compliant"
                  ? "text-green-600"
                  : "text-red-600"
              }`}
            >
              {data.compliance_status}
            </p>
          </div>
        </div>

        {/* Score Progress Bar */}
        <div className="mt-4 bg-gray-300 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all ${
              data.quality_score >= 80
                ? "bg-green-600"
                : data.quality_score >= 60
                  ? "bg-yellow-600"
                  : "bg-red-600"
            }`}
            style={{ width: `${data.quality_score}%` }}
          />
        </div>
      </div>

      {/* Issue Summary */}
      <div className="grid grid-cols-3 gap-3 py-4 border-y">
        <div className="text-center p-3 bg-red-50 rounded">
          <p className="text-2xl font-bold text-red-600">
            {data.critical_issues_count}
          </p>
          <p className="text-xs font-semibold text-red-700 uppercase mt-1">
            Critical
          </p>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded">
          <p className="text-2xl font-bold text-orange-600">
            {data.major_issues_count}
          </p>
          <p className="text-xs font-semibold text-orange-700 uppercase mt-1">
            Major
          </p>
        </div>
        <div className="text-center p-3 bg-yellow-50 rounded">
          <p className="text-2xl font-bold text-yellow-600">
            {data.minor_issues_count}
          </p>
          <p className="text-xs font-semibold text-yellow-700 uppercase mt-1">
            Minor
          </p>
        </div>
      </div>

      {/* Issues List */}
      {data.issues.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">
            Issues ({data.issues.length})
          </h4>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {data.issues.map((issue: ValidationIssue, idx: number) => (
              <div
                key={idx}
                className={`border rounded-lg p-3 cursor-pointer transition ${
                  selectedIssue === idx
                    ? `${getSeverityColor(issue.severity)} border-current`
                    : `border-gray-200 hover:${getSeverityColor(issue.severity)}`
                }`}
                onClick={() =>
                  setSelectedIssue(selectedIssue === idx ? null : idx)
                }
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-sm text-gray-900">
                      {issue.issue_description}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      📍 {issue.location}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded ml-2 whitespace-nowrap ${getSeverityColor(
                      issue.severity,
                    )}`}
                  >
                    {issue.severity}
                  </span>
                </div>

                {selectedIssue === idx && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    <div>
                      <p className="text-xs font-semibold text-gray-600">
                        Issue Type
                      </p>
                      <p className="text-sm text-gray-700 mt-1">
                        {issue.issue_type}
                      </p>
                    </div>
                    {issue.fix_suggestion && (
                      <div>
                        <p className="text-xs font-semibold text-gray-600">
                          Suggestion
                        </p>
                        <p className="text-sm text-gray-700 mt-1">
                          {issue.fix_suggestion}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations_for_improvement.length > 0 && (
        <div className="space-y-2 pt-4 border-t">
          <h4 className="text-sm font-semibold text-gray-700">
            Recommendations
          </h4>
          <ul className="space-y-1">
            {data.recommendations_for_improvement.map(
              (rec: string, idx: number) => (
                <li
                  key={idx}
                  className="text-sm text-gray-700 flex items-start"
                >
                  <span className="text-blue-600 mr-2">→</span>
                  <span>{rec}</span>
                </li>
              ),
            )}
          </ul>
        </div>
      )}

      {/* Metadata */}
      <div className="pt-2 border-t text-xs text-gray-500">
        Created: {new Date(data.created_at).toLocaleString()}
      </div>
    </div>
  );
}
