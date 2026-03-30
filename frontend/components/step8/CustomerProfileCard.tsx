/**
 * CustomerProfileCard — STEP 8A Output Display
 *
 * Shows client intelligence: stakeholders, decision drivers, budget authority,
 * pain points extracted by the proposal_customer_analysis node.
 */

"use client";

import { useState } from "react";
import type { CustomerProfile } from "@/lib/types/step8";

export interface CustomerProfileCardProps {
  data: CustomerProfile | null;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export function CustomerProfileCard({
  data,
  isLoading = false,
  error = null,
  onRevalidate,
}: CustomerProfileCardProps) {
  const [expandedStakeholder, setExpandedStakeholder] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-blue-50 to-transparent">
        <div className="h-6 w-48 bg-blue-200 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-blue-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-blue-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">Failed to load customer profile</p>
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
        <p className="text-sm text-gray-600">No customer profile available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{data.client_name}</h3>
          <p className="text-sm text-gray-600">{data.client_org}</p>
        </div>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Re-analyze customer profile"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Key Info */}
      <div className="grid grid-cols-2 gap-4 py-4 border-y">
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase">Budget Authority</p>
          <p className="text-sm text-gray-900 mt-1">{data.budget_authority}</p>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase">Key Drivers</p>
          <p className="text-sm text-gray-900 mt-1">
            {data.decision_drivers.slice(0, 2).join(", ")}
          </p>
        </div>
      </div>

      {/* Stakeholders */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">Stakeholders ({data.stakeholders.length})</h4>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.stakeholders.map((stakeholder, idx) => (
            <div
              key={idx}
              className="border rounded p-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition"
              onClick={() =>
                setExpandedStakeholder(
                  expandedStakeholder === stakeholder.name ? null : stakeholder.name
                )
              }
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm text-gray-900">{stakeholder.name}</p>
                  <p className="text-xs text-gray-600">{stakeholder.role}</p>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded ${
                    stakeholder.influence_level === "high"
                      ? "bg-red-100 text-red-800"
                      : stakeholder.influence_level === "medium"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-green-100 text-green-800"
                  }`}
                >
                  {stakeholder.influence_level}
                </span>
              </div>

              {expandedStakeholder === stakeholder.name && (
                <div className="mt-3 pt-3 border-t space-y-2">
                  <div>
                    <p className="text-xs font-semibold text-gray-600">Priorities</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {stakeholder.priorities.map((p, i) => (
                        <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-600">Concerns</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {stakeholder.concerns.map((c, i) => (
                        <span key={i} className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Pain Points */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">Pain Points</h4>
        <div className="flex flex-wrap gap-2">
          {data.pain_points.map((point, idx) => (
            <div
              key={idx}
              className="px-3 py-1 bg-red-50 border border-red-200 text-red-700 rounded text-xs"
            >
              {point}
            </div>
          ))}
        </div>
      </div>

      {/* Metadata */}
      <div className="pt-2 border-t text-xs text-gray-500">
        Created: {new Date(data.created_at).toLocaleString()}
      </div>
    </div>
  );
}
