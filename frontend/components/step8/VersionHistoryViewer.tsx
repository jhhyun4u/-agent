/**
 * VersionHistoryViewer — Artifact Version Comparison
 *
 * Shows version timeline for node artifacts with diff viewer,
 * version metadata, and timeline visualization.
 */

"use client";

import { useState } from "react";
import type { ArtifactVersion } from "@/lib/types/step8";

export interface VersionMetadata {
  version_id: string;
  node_name: string;
  version_number: number;
  created_at: string;
  created_by: string;
  size_bytes: number;
  description?: string;
  change_summary?: string;
}

export interface VersionComparisonData {
  current_version: VersionMetadata;
  previous_version: VersionMetadata | null;
  diff_lines?: string[];
  additions: number;
  deletions: number;
  net_change: number;
}

export interface VersionHistoryViewerProps {
  node_name: string;
  versions: VersionMetadata[];
  onSelectVersion?: (version_id: string) => void;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export function VersionHistoryViewer({
  node_name,
  versions,
  onSelectVersion,
  isLoading = false,
  error = null,
  onRevalidate,
}: VersionHistoryViewerProps) {
  const [selectedVersion, setSelectedVersion] = useState<string | null>(
    versions.length > 0 ? versions[0].version_id : null,
  );
  const [showDiff, setShowDiff] = useState(false);
  const [comparisonMode, setComparisonMode] = useState<"prev" | "first">(
    "prev",
  );

  const getVersionColor = (index: number, total: number): string => {
    const percent = ((total - index) / total) * 100;
    if (percent >= 80) return "bg-green-50 border-green-200";
    if (percent >= 50) return "bg-blue-50 border-blue-200";
    if (percent >= 25) return "bg-yellow-50 border-yellow-200";
    return "bg-gray-50 border-gray-200";
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const generateMockDiff = (
    v1: VersionMetadata,
    v2: VersionMetadata | null,
  ) => {
    // Mock diff generation for demo purposes
    // In production, this would fetch actual diff from backend
    if (!v2) return { additions: 0, deletions: 0, diff_lines: [] };

    const v1_lines = Math.ceil(v1.size_bytes / 50);
    const v2_lines = v2 ? Math.ceil(v2.size_bytes / 50) : 0;
    const additions = Math.max(0, v1_lines - v2_lines);
    const deletions = Math.max(0, v2_lines - v1_lines);

    const diff_lines: string[] = [];
    for (let i = 0; i < Math.min(additions, 5); i++) {
      diff_lines.push(`+ Added line ${i + 1}`);
    }
    for (let i = 0; i < Math.min(deletions, 5); i++) {
      diff_lines.push(`- Removed line ${i + 1}`);
    }

    return { additions, deletions, diff_lines };
  };

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-indigo-50 to-transparent">
        <div className="h-6 w-48 bg-indigo-200 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-indigo-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-indigo-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">Failed to load version history</p>
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

  if (versions.length === 0) {
    return (
      <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
        <p className="text-sm text-gray-600">No version history available</p>
      </div>
    );
  }

  const currentSelectedVersion = versions.find(
    (v) => v.version_id === selectedVersion,
  );
  const currentIndex =
    versions.findIndex((v) => v.version_id === selectedVersion) ?? 0;
  const previousVersion =
    comparisonMode === "prev" && currentIndex < versions.length - 1
      ? versions[currentIndex + 1]
      : null;
  const firstVersion =
    comparisonMode === "first" ? versions[versions.length - 1] : null;
  const comparisonTarget =
    comparisonMode === "prev" ? previousVersion : firstVersion;

  const diffData = generateMockDiff(currentSelectedVersion!, comparisonTarget);

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Version History
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {node_name} artifact versions
          </p>
        </div>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Refresh version history"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Version Summary */}
      <div className="grid grid-cols-3 gap-3 py-3 border rounded-lg bg-gradient-to-r from-indigo-50 to-purple-50">
        <div className="text-center">
          <p className="text-xs font-semibold text-gray-600 uppercase">
            Total Versions
          </p>
          <p className="text-2xl font-bold text-indigo-600 mt-2">
            {versions.length}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs font-semibold text-gray-600 uppercase">
            Latest
          </p>
          <p className="text-2xl font-bold text-purple-600 mt-2">
            v{versions[0].version_number}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs font-semibold text-gray-600 uppercase">Size</p>
          <p className="text-sm font-bold text-gray-900 mt-2">
            {formatBytes(versions[0].size_bytes)}
          </p>
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">
          Version Timeline
        </h4>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {versions.map((version, idx) => {
            const isSelected = version.version_id === selectedVersion;
            const isLatest = idx === 0;

            return (
              <div
                key={version.version_id}
                className={`border rounded-lg p-3 cursor-pointer transition ${getVersionColor(idx, versions.length)} ${
                  isSelected ? "ring-2 ring-indigo-500" : "hover:shadow-sm"
                }`}
                onClick={() => {
                  setSelectedVersion(version.version_id);
                  onSelectVersion?.(version.version_id);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-block px-2 py-1 bg-white text-indigo-700 rounded text-xs font-bold border border-indigo-300">
                        v{version.version_number}
                      </span>
                      {isLatest && (
                        <span className="inline-block px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold border border-green-300">
                          Latest
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-900 font-medium">
                      {version.description || "Version update"}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {new Date(version.created_at).toLocaleString()} • By{" "}
                      {version.created_by}
                    </p>
                  </div>
                  <div className="text-right ml-4 flex-shrink-0">
                    <p className="text-xs text-gray-600">Size</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {formatBytes(version.size_bytes)}
                    </p>
                  </div>
                </div>

                {/* Change Summary */}
                {version.change_summary && (
                  <div className="mt-2 p-2 bg-white bg-opacity-60 rounded border border-gray-300 text-xs text-gray-700">
                    {version.change_summary}
                  </div>
                )}

                {/* Selection Indicator */}
                {isSelected && (
                  <div className="mt-2 pt-2 border-t flex items-center justify-between">
                    <span className="text-xs font-semibold text-indigo-700">
                      Selected
                    </span>
                    <span className="text-indigo-500">✓</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparison Controls */}
      {currentSelectedVersion && (
        <div className="space-y-3 p-3 rounded-lg bg-gray-50 border border-gray-200">
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-2">
              Compare With
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setComparisonMode("prev");
                  setShowDiff(true);
                }}
                disabled={currentIndex >= versions.length - 1}
                className={`flex-1 px-3 py-2 text-sm rounded font-medium transition ${
                  comparisonMode === "prev"
                    ? "bg-indigo-600 text-white"
                    : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                Previous Version
              </button>
              <button
                onClick={() => {
                  setComparisonMode("first");
                  setShowDiff(true);
                }}
                disabled={currentIndex === versions.length - 1}
                className={`flex-1 px-3 py-2 text-sm rounded font-medium transition ${
                  comparisonMode === "first"
                    ? "bg-indigo-600 text-white"
                    : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                Original
              </button>
            </div>
          </div>

          {/* Diff Viewer */}
          {showDiff && (
            <div className="space-y-2">
              <button
                onClick={() => setShowDiff(false)}
                className="w-full px-3 py-1.5 text-xs bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition"
              >
                Hide Diff
              </button>

              <div className="space-y-2 p-3 rounded-lg bg-white border border-gray-300">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-gray-700 uppercase">
                    Comparing v{currentSelectedVersion.version_number} vs v
                    {comparisonTarget?.version_number}
                  </p>
                  <span className="text-xs text-gray-600">
                    +{diffData.additions} / -{diffData.deletions}
                  </span>
                </div>

                {/* Diff Stats */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 bg-green-50 rounded text-center">
                    <p className="text-xs text-gray-600">Additions</p>
                    <p className="text-lg font-bold text-green-600">
                      {diffData.additions}
                    </p>
                  </div>
                  <div className="p-2 bg-red-50 rounded text-center">
                    <p className="text-xs text-gray-600">Deletions</p>
                    <p className="text-lg font-bold text-red-600">
                      {diffData.deletions}
                    </p>
                  </div>
                  <div className="p-2 bg-blue-50 rounded text-center">
                    <p className="text-xs text-gray-600">Net Change</p>
                    <p
                      className={`text-lg font-bold ${diffData.net_change >= 0 ? "text-blue-600" : "text-orange-600"}`}
                    >
                      {diffData.net_change >= 0 ? "+" : ""}
                      {diffData.net_change}
                    </p>
                  </div>
                </div>

                {/* Diff Lines */}
                {diffData.diff_lines.length > 0 && (
                  <div className="max-h-48 overflow-y-auto space-y-1 font-mono text-xs bg-gray-100 p-2 rounded border border-gray-300">
                    {diffData.diff_lines.map((line, idx) => (
                      <div
                        key={idx}
                        className={
                          line.startsWith("+")
                            ? "text-green-700 bg-green-50 px-1"
                            : "text-red-700 bg-red-50 px-1"
                        }
                      >
                        {line}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Metadata */}
      {currentSelectedVersion && (
        <div className="space-y-2 p-3 rounded-lg bg-blue-50 border border-blue-200">
          <p className="text-xs font-semibold text-blue-700 uppercase">
            Selected Version Details
          </p>
          <div className="grid grid-cols-2 gap-2 text-sm text-gray-900">
            <div>
              <p className="text-xs text-gray-600">Version ID</p>
              <p className="font-mono text-xs mt-1">
                {currentSelectedVersion.version_id}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Created By</p>
              <p className="mt-1">{currentSelectedVersion.created_by}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Created At</p>
              <p className="mt-1">
                {new Date(currentSelectedVersion.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Size</p>
              <p className="mt-1">
                {formatBytes(currentSelectedVersion.size_bytes)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
