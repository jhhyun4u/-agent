/**
 * ConsolidatedProposalCard — STEP 8C Output Display
 *
 * Shows consolidated proposal state: sections after merging/conflict resolution,
 * section lineage tracking, and executive summary from the
 * proposal_sections_consolidation node.
 */

"use client";

import { useState } from "react";
import type { ConsolidatedProposal, SectionLineage } from "@/lib/types/step8";

export interface ConsolidatedProposalCardProps {
  data: ConsolidatedProposal | null;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export function ConsolidatedProposalCard({
  data,
  isLoading = false,
  error = null,
  onRevalidate,
}: ConsolidatedProposalCardProps) {
  const [expandedLineage, setExpandedLineage] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-cyan-50 to-transparent">
        <div className="h-6 w-48 bg-cyan-200 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-cyan-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-cyan-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">
          Failed to load consolidated proposal
        </p>
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
        <p className="text-sm text-gray-600">
          No consolidated proposal available
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Consolidated Proposal
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Merged & Resolved Sections
          </p>
        </div>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Re-consolidate proposal"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Section Count */}
      <div className="grid grid-cols-2 gap-4 py-3 border rounded-lg bg-gradient-to-r from-cyan-50 to-blue-50">
        <div>
          <p className="text-xs font-semibold text-gray-600 uppercase">
            Total Sections
          </p>
          <p className="text-3xl font-bold text-cyan-600 mt-2">
            {data.total_sections}
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-600 uppercase">
            Final Sections
          </p>
          <p className="text-3xl font-bold text-blue-600 mt-2">
            {data.final_sections.length}
          </p>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">
          Executive Summary
        </h4>
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
          <p className="text-sm text-gray-800 leading-relaxed">
            {data.executive_summary}
          </p>
        </div>
      </div>

      {/* Final Section List */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">
          Final Sections ({data.final_sections.length})
        </h4>
        <div className="space-y-1 bg-gray-50 rounded-lg p-3 max-h-64 overflow-y-auto">
          {data.final_sections.map((section, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 p-2 hover:bg-gray-100 rounded transition"
            >
              <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-cyan-600 text-white rounded-full text-xs font-bold">
                {idx + 1}
              </span>
              <span className="text-sm text-gray-800">{section}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Key Changes */}
      {data.key_changes.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">
            📝 Key Changes
          </h4>
          <ul className="space-y-2">
            {data.key_changes.map((change, idx) => (
              <li
                key={idx}
                className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-gray-800"
              >
                <span className="text-amber-600 font-semibold">{idx + 1}.</span>{" "}
                {change}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Section Lineage */}
      {data.section_lineage.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">
            🔗 Section Lineage
          </h4>
          <div className="space-y-2 bg-gray-50 rounded-lg p-3 max-h-72 overflow-y-auto">
            {data.section_lineage.map(
              (lineage: SectionLineage, idx: number) => (
                <div key={idx} className="space-y-1">
                  <button
                    onClick={() =>
                      setExpandedLineage(expandedLineage === idx ? null : idx)
                    }
                    className="w-full text-left p-3 rounded-lg border border-gray-300 hover:border-gray-400 transition bg-white"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm text-gray-900">
                          {lineage.original_title}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          Original index: {lineage.original_index}
                        </p>
                      </div>
                      <span
                        className={`transform transition text-gray-400 ${
                          expandedLineage === idx ? "rotate-180" : ""
                        }`}
                      >
                        ▼
                      </span>
                    </div>
                  </button>

                  {expandedLineage === idx && (
                    <div className="ml-4 p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
                      <div>
                        <p className="text-xs font-semibold text-blue-700 uppercase">
                          Merged Into
                        </p>
                        <p className="text-sm text-gray-900 mt-1">
                          <span className="font-medium">
                            {lineage.merged_into_title}
                          </span>
                          <span className="text-gray-600 ml-2">
                            (index {lineage.merged_into_index})
                          </span>
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-blue-700 uppercase">
                          Conflict Resolution
                        </p>
                        <p className="text-sm text-gray-800 mt-1">
                          {lineage.conflict_resolution}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ),
            )}
          </div>
        </div>
      )}

      {/* Consolidation Info */}
      <div className="p-4 rounded-lg bg-green-50 border border-green-200">
        <p className="text-xs font-semibold text-green-700 uppercase">Status</p>
        <p className="text-sm text-gray-900 mt-2">
          ✓ Proposal successfully consolidated with{" "}
          {data.section_lineage.length} merge{" "}
          {data.section_lineage.length === 1 ? "operation" : "operations"}.
        </p>
      </div>

      {/* Metadata */}
      <div className="pt-2 border-t text-xs text-gray-500">
        Created: {new Date(data.created_at).toLocaleString()}
      </div>
    </div>
  );
}
