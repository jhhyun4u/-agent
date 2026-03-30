/**
 * RewriteHistoryCard — STEP 8F Output Display
 *
 * Shows rewriting progress: iteration count, section-by-section history,
 * content changes, and feedback application from the proposal_write_next_v2 node.
 */

"use client";

import { useState } from "react";
import type { RewriteRecord, RewriteHistory } from "@/lib/types/step8";

export interface RewriteHistoryCardProps {
  data: RewriteRecord | null;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export function RewriteHistoryCard({
  data,
  isLoading = false,
  error = null,
  onRevalidate,
}: RewriteHistoryCardProps) {
  const [expandedHistory, setExpandedHistory] = useState<number | null>(null);
  const [showDiff, setShowDiff] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-orange-50 to-transparent">
        <div className="h-6 w-48 bg-orange-200 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-orange-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-orange-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">Failed to load rewrite history</p>
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
        <p className="text-sm text-gray-600">No rewrite history available</p>
      </div>
    );
  }

  const getIterationColor = (iteration: number, maxIteration: number): string => {
    const percent = (iteration / maxIteration) * 100;
    if (percent >= 80) return "bg-green-50 border-green-200";
    if (percent >= 50) return "bg-yellow-50 border-yellow-200";
    return "bg-orange-50 border-orange-200";
  };

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Rewrite History</h3>
          <p className="text-sm text-gray-600 mt-1">Iterative Section Improvements</p>
        </div>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Re-analyze rewrite history"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Progress Summary */}
      <div className="grid grid-cols-3 gap-3 py-3 border rounded-lg bg-gradient-to-r from-orange-50 to-red-50">
        <div className="text-center">
          <p className="text-xs font-semibold text-gray-600 uppercase">Current Section</p>
          <p className="text-2xl font-bold text-orange-600 mt-2">
            {data.current_section_index + 1}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs font-semibold text-gray-600 uppercase">Iterations</p>
          <p className="text-2xl font-bold text-red-600 mt-2">
            {data.rewrite_iteration_count}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs font-semibold text-gray-600 uppercase">Total Rewrites</p>
          <p className="text-2xl font-bold text-red-600 mt-2">
            {data.total_rewrites}
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <p className="text-xs font-semibold text-gray-700">Overall Progress</p>
          <p className="text-sm text-gray-600">
            {data.history.length} revision{data.history.length === 1 ? "" : "s"}
          </p>
        </div>
        <div className="w-full bg-gray-300 rounded-full h-3 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-orange-500 to-red-600 transition-all"
            style={{ width: `${Math.min((data.total_rewrites / 10) * 100, 100)}%` }}
          />
        </div>
      </div>

      {/* Rewrite Timeline */}
      {data.history.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">
            📋 Revision Timeline ({data.history.length})
          </h4>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {data.history.map((history: RewriteHistory, idx: number) => (
              <div
                key={idx}
                className={`border rounded-lg overflow-hidden ${getIterationColor(
                  history.iteration,
                  3
                )}`}
              >
                {/* Header */}
                <button
                  onClick={() => setExpandedHistory(expandedHistory === idx ? null : idx)}
                  className="w-full text-left p-3 hover:opacity-80 transition"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-white text-orange-700 rounded text-xs font-bold border border-orange-300">
                          Iteration {history.iteration}
                        </span>
                        <p className="font-medium text-gray-900">
                          {history.section_title}
                        </p>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        {new Date(history.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span
                      className={`transform transition text-gray-400 ${
                        expandedHistory === idx ? "rotate-180" : ""
                      }`}
                    >
                      ▼
                    </span>
                  </div>
                </button>

                {/* Expanded Details */}
                {expandedHistory === idx && (
                  <div className="border-t space-y-3 p-3 bg-white bg-opacity-50">
                    {/* Feedback Applied */}
                    <div>
                      <p className="text-xs font-semibold text-gray-700 uppercase">Feedback Applied</p>
                      <div className="mt-2 p-2 bg-blue-100 border border-blue-300 rounded text-sm text-blue-900">
                        {history.feedback_used}
                      </div>
                    </div>

                    {/* Content Preview */}
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-gray-700 uppercase">
                        Content Changes
                      </div>
                      <button
                        onClick={() => setShowDiff(showDiff === idx ? null : idx)}
                        className="w-full text-left px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm font-medium text-gray-800 transition"
                      >
                        {showDiff === idx ? "Hide" : "Show"} Diff
                      </button>

                      {showDiff === idx && (
                        <div className="bg-gray-100 rounded p-3 space-y-2 max-h-64 overflow-y-auto text-xs font-mono">
                          <div>
                            <p className="text-red-700 font-semibold mb-1">Original:</p>
                            <div className="bg-red-50 p-2 rounded border border-red-200 line-clamp-4">
                              {history.original_content.slice(0, 300)}
                              {history.original_content.length > 300 ? "..." : ""}
                            </div>
                          </div>
                          <div>
                            <p className="text-green-700 font-semibold mb-1">Rewritten:</p>
                            <div className="bg-green-50 p-2 rounded border border-green-200 line-clamp-4">
                              {history.rewritten_content.slice(0, 300)}
                              {history.rewritten_content.length > 300 ? "..." : ""}
                            </div>
                          </div>
                          <div className="text-gray-600 text-xs">
                            <p>Original length: {history.original_content.length} chars</p>
                            <p>
                              New length: {history.rewritten_content.length} chars
                              <span className="ml-2 font-semibold">
                                ({history.rewritten_content.length > history.original_content.length
                                  ? "+"
                                  : ""}
                                {history.rewritten_content.length - history.original_content.length})
                              </span>
                            </p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                      <div className="p-2 bg-blue-50 rounded text-center">
                        <p className="text-xs text-gray-600">Original Words</p>
                        <p className="text-sm font-bold text-blue-600">
                          {history.original_content.split(/\s+/).length}
                        </p>
                      </div>
                      <div className="p-2 bg-green-50 rounded text-center">
                        <p className="text-xs text-gray-600">Revised Words</p>
                        <p className="text-sm font-bold text-green-600">
                          {history.rewritten_content.split(/\s+/).length}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status */}
      <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
        <p className="text-xs font-semibold text-blue-700 uppercase">Rewriting Status</p>
        <p className="text-sm text-gray-900 mt-2">
          {data.rewrite_iteration_count > 0
            ? `Currently revising sections. ${data.total_rewrites} total rewrites completed.`
            : "Awaiting rewrite feedback."}
        </p>
      </div>

      {/* Metadata */}
      <div className="pt-2 border-t text-xs text-gray-500">
        Created: {new Date(data.created_at).toLocaleString()}
      </div>
    </div>
  );
}
