/**
 * NodeStatusDashboard — STEP 8 Progress Overview
 *
 * Grid layout showing all 6 node cards (8A-8F) with overall STEP 8
 * progress percentage, manual validation triggers, and status indicators.
 */

"use client";

import { useState } from "react";
import type { Step8Status, NodeStatus } from "@/lib/types/step8";
import {
  CustomerProfileCard,
  ValidationReportCard,
  ConsolidatedProposalCard,
  MockEvalCard,
  FeedbackSummaryCard,
  RewriteHistoryCard,
} from "./index";

export interface NodeStatusDashboardProps {
  proposal_id: string;
  status: Step8Status | null;
  isLoading?: boolean;
  error?: Error | null;
  onValidateAll?: () => void;
  onValidateNode?: (node_id: string) => void;
  onRevalidate?: () => void;
}

export function NodeStatusDashboard({
  proposal_id,
  status,
  isLoading = false,
  error = null,
  onValidateAll,
  onValidateNode,
  onRevalidate,
}: NodeStatusDashboardProps) {
  const [expandedNode, setExpandedNode] = useState<string | null>(null);

  const getNodeCompletionColor = (node: NodeStatus | undefined): string => {
    if (!node) return "bg-gray-100 border-gray-300";
    if (node.status === "completed") return "bg-green-100 border-green-300";
    if (node.status === "in_progress") return "bg-blue-100 border-blue-300";
    if (node.status === "failed") return "bg-red-100 border-red-300";
    return "bg-yellow-100 border-yellow-300";
  };

  const calculateOverallProgress = (): number => {
    if (!status?.nodes) return 0;
    const nodes = status.nodes;
    const completed = nodes.filter((n) => n.status === "completed").length;
    return Math.round((completed / nodes.length) * 100);
  };

  const getProgressColor = (percent: number): string => {
    if (percent >= 80) return "from-green-500 to-green-600";
    if (percent >= 50) return "from-yellow-500 to-yellow-600";
    if (percent >= 20) return "from-orange-500 to-orange-600";
    return "from-red-500 to-red-600";
  };

  const nodeConfig = [
    {
      id: "step_8a",
      label: "8A: Customer Profile",
      icon: "👤",
      description: "Client intelligence extraction",
    },
    {
      id: "step_8b",
      label: "8B: Validation Report",
      icon: "✓",
      description: "Quality validation & issues",
    },
    {
      id: "step_8c",
      label: "8C: Consolidated Proposal",
      icon: "📋",
      description: "Section merging & consolidation",
    },
    {
      id: "step_8d",
      label: "8D: Mock Evaluation",
      icon: "🎯",
      description: "Win probability & scoring",
    },
    {
      id: "step_8e",
      label: "8E: Feedback Summary",
      icon: "💡",
      description: "Prioritized improvements",
    },
    {
      id: "step_8f",
      label: "8F: Rewrite History",
      icon: "↻",
      description: "Iterative revisions",
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-8 w-64 bg-violet-200 rounded animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-48 bg-gray-200 rounded-lg animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700 font-medium">
          Failed to load STEP 8 dashboard
        </p>
        <p className="text-xs text-red-600 mt-1">{error.message}</p>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="mt-3 px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  const overallProgress = calculateOverallProgress();
  const progressColor = getProgressColor(overallProgress);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">STEP 8 Workflow</h2>
          <p className="text-sm text-gray-600 mt-1">
            AI-Enhanced Proposal Review & Optimization
          </p>
        </div>
        <div className="flex gap-2">
          {onValidateAll && (
            <button
              onClick={onValidateAll}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Validate All Nodes
            </button>
          )}
          {onRevalidate && (
            <button
              onClick={onRevalidate}
              className="px-4 py-2 text-sm bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
            >
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Overall Progress */}
      <div className="space-y-3 p-4 rounded-lg bg-gradient-to-r from-slate-50 to-slate-100 border border-slate-200">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-700">
              Overall Progress
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {status?.nodes
                ? status.nodes.filter((n) => n.status === "completed").length
                : 0}{" "}
              of 6 nodes completed
            </p>
          </div>
          <div className={`text-3xl font-bold bg-gradient-to-r ${progressColor} bg-clip-text text-transparent`}>
            {overallProgress}%
          </div>
        </div>
        <div className="w-full bg-gray-300 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full bg-gradient-to-r ${progressColor} transition-all duration-500`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      {/* Node Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {nodeConfig.map((config) => {
          const node = status?.nodes?.find((n) => n.output_key === config.id.replace("step_8", "step_8"));
          const isExpanded = expandedNode === config.id;

          return (
            <div
              key={config.id}
              className={`border rounded-lg p-4 transition cursor-pointer ${getNodeCompletionColor(node)}`}
              onClick={() =>
                setExpandedNode(isExpanded ? null : config.id)
              }
            >
              {/* Node Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3 flex-1">
                  <span className="text-2xl">{config.icon}</span>
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-900 text-sm">
                      {config.label}
                    </p>
                    <p className="text-xs text-gray-600 mt-0.5">
                      {config.description}
                    </p>
                  </div>
                </div>
                <span
                  className={`transform transition ${isExpanded ? "rotate-180" : ""} ml-2 flex-shrink-0`}
                >
                  ▼
                </span>
              </div>

              {/* Status Badge */}
              {node && (
                <div className="flex items-center gap-2 mb-3">
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      node.status === "completed"
                        ? "bg-green-600"
                        : node.status === "in_progress"
                        ? "bg-blue-600"
                        : node.status === "failed"
                        ? "bg-red-600"
                        : "bg-yellow-600"
                    }`}
                  />
                  <span className="text-xs font-medium text-gray-700 capitalize">
                    {node.status}
                  </span>
                </div>
              )}

              {/* Validate Button */}
              {onValidateNode && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onValidateNode(config.id);
                  }}
                  className="w-full px-3 py-1.5 text-xs bg-white bg-opacity-70 hover:bg-opacity-100 text-gray-700 rounded border border-gray-300 transition"
                >
                  Validate Node
                </button>
              )}

              {/* Expanded Details */}
              {isExpanded && node && (
                <div className="mt-3 pt-3 border-t space-y-2">
                  <div>
                    <p className="text-xs font-semibold text-gray-600 uppercase">
                      Updated
                    </p>
                    <p className="text-sm text-gray-900 mt-1">
                      {new Date(node.updated_at).toLocaleString()}
                    </p>
                  </div>
                  {node.version && (
                    <div>
                      <p className="text-xs font-semibold text-gray-600 uppercase">
                        Version
                      </p>
                      <p className="text-sm text-gray-900 mt-1">
                        v{node.version}
                      </p>
                    </div>
                  )}
                  {node.error && (
                    <div className="p-2 bg-red-100 rounded border border-red-200">
                      <p className="text-xs font-semibold text-red-700">
                        Error
                      </p>
                      <p className="text-xs text-red-600 mt-1">{node.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Node Details */}
      {status && (
        <div className="space-y-6">
          {/* Details would be embedded here based on node data */}
          <p className="text-xs text-gray-500 text-center py-4">
            Detailed node cards can be embedded here when data is available
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="pt-4 border-t text-xs text-gray-500">
        <p>
          Last synced:{" "}
          {status?.last_updated
            ? new Date(status.last_updated).toLocaleString()
            : "Never"}
        </p>
      </div>
    </div>
  );
}
