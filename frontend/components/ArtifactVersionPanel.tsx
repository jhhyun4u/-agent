"use client";

/**
 * ArtifactVersionPanel Component
 *
 * Phase 1: Artifact Versioning System
 *
 * Displays version history for current node's outputs.
 * Shown as 4th tab in DetailRightPanel.
 *
 * Features:
 * - Version selector buttons (v1, v2, v3...)
 * - Active/deprecated status indicators
 * - Version metadata (created_at, created_by, used_by)
 * - Dependency info (which nodes use this version)
 * - Phase 3-4: Version-specific download buttons
 */

import React, { useState, useMemo, useCallback } from "react";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Clock, User, GitBranch, AlertCircle, Download } from "lucide-react";
import { useToast } from "@/components/ui/Toast";

export interface ArtifactVersionInfo {
  node_name: string;
  output_key: string;
  version: number;
  created_at: string;
  created_by: string;
  is_active: boolean;
  is_deprecated: boolean;
  used_by?: Array<{ node: string; count: number }>;
  created_reason?: string;
  artifact_size?: number;
}

export interface DependencyMismatch {
  input_key: string;
  expected_version: number;
  actual_version: number;
  node_name: string;
  message?: string;
}

export interface ArtifactVersionPanelProps {
  artifacts: Record<string, ArtifactVersionInfo[]>;
  currentOutputKey?: string;
  onVersionSelect?: (outputKey: string, version: number) => Promise<void>;
  dependencyMismatches?: DependencyMismatch[];
  proposalId?: string;
  downloadToken?: string;
}

export function ArtifactVersionPanel({
  artifacts,
  currentOutputKey,
  onVersionSelect,
  dependencyMismatches = [],
  proposalId,
  downloadToken,
}: ArtifactVersionPanelProps) {
  const [selectedVersion, setSelectedVersion] = useState<number | undefined>(
    undefined,
  );
  const [expandedKey, setExpandedKey] = useState<string | undefined>(
    currentOutputKey,
  );
  const [isLoading, setIsLoading] = useState(false);

  // Group artifacts by output_key
  const groupedArtifacts = useMemo(() => {
    const groups: Record<string, ArtifactVersionInfo[]> = {};

    Object.entries(artifacts).forEach(([key, versions]) => {
      groups[key] = versions.sort((a, b) => b.version - a.version); // Latest first
    });

    return groups;
  }, [artifacts]);

  const handleVersionSelect = async (outputKey: string, version: number) => {
    setSelectedVersion(version);
    setExpandedKey(outputKey);

    if (onVersionSelect) {
      setIsLoading(true);
      try {
        await onVersionSelect(outputKey, version);
      } finally {
        setIsLoading(false);
      }
    }
  };

  if (Object.keys(groupedArtifacts).length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">아직 생성된 산출물 버전이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      {/* Overview */}
      <div className="text-xs text-gray-600 space-y-1">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4" />
          <span>총 {Object.keys(groupedArtifacts).length}개 산출물</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          <span>
            {Object.values(groupedArtifacts).reduce(
              (sum, versions) => sum + versions.length,
              0,
            )}
            개 버전
          </span>
        </div>
      </div>

      <div className="border-t pt-4 space-y-3">
        {Object.entries(groupedArtifacts).map(([outputKey, versions]) => (
          <ArtifactVersionGroup
            key={outputKey}
            outputKey={outputKey}
            versions={versions}
            isExpanded={expandedKey === outputKey}
            onExpand={() =>
              setExpandedKey(outputKey === expandedKey ? undefined : outputKey)
            }
            onVersionSelect={(version) =>
              handleVersionSelect(outputKey, version)
            }
            isLoading={isLoading}
            proposalId={proposalId}
            downloadToken={downloadToken}
          />
        ))}
      </div>

      {/* 의존성 불일치 경고 */}
      {dependencyMismatches.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="text-xs font-semibold text-orange-700 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            의존성 버전 불일치 감지
          </div>
          {dependencyMismatches.map((mismatch, idx) => (
            <Alert key={idx} className="border-orange-200 bg-orange-50 text-xs">
              <AlertCircle className="h-3 w-3 text-orange-500" />
              <AlertDescription className="text-orange-800">
                <span className="font-semibold">{mismatch.input_key}</span>:
                노드 <span className="font-mono">{mismatch.node_name}</span>가 v
                {mismatch.expected_version}을 기대하지만 현재 활성 버전은 v
                {mismatch.actual_version}입니다.
                {mismatch.message && (
                  <span className="block mt-0.5 text-orange-600">
                    {mismatch.message}
                  </span>
                )}
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Info box */}
      <Alert className="mt-4 text-xs">
        <AlertCircle className="h-3 w-3" />
        <AlertDescription>
          버전을 선택하면 상세 정보를 확인할 수 있습니다.
        </AlertDescription>
      </Alert>
    </div>
  );
}

/**
 * ArtifactVersionGroup: Group of versions for single output
 */
function ArtifactVersionGroup({
  outputKey,
  versions,
  isExpanded,
  onExpand,
  onVersionSelect,
  isLoading,
  proposalId,
  downloadToken,
}: {
  outputKey: string;
  versions: ArtifactVersionInfo[];
  isExpanded: boolean;
  onExpand: () => void;
  onVersionSelect: (version: number) => void;
  isLoading: boolean;
  proposalId?: string;
  downloadToken?: string;
}) {
  const activeVersion = versions.find((v) => v.is_active);
  const latestVersion = versions[0];

  return (
    <Card className="border">
      <CardHeader
        className="pb-3 cursor-pointer hover:bg-gray-50"
        onClick={onExpand}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="card-title text-sm">{outputKey}</h3>
            <div className="text-xs text-gray-600 mt-1">
              {versions.length}개 버전
              {activeVersion && (
                <span className="ml-2">(활성: v{activeVersion.version})</span>
              )}
            </div>
          </div>
          <div className="text-xs text-gray-500">{isExpanded ? "▼" : "▶"}</div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardBody className="border-t pt-3">
          {/* Version selector buttons */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-gray-700 mb-2">
              버전 선택
            </div>
            <div className="grid grid-cols-4 gap-2 sm:grid-cols-5">
              {versions.map((version) => (
                <button
                  key={version.version}
                  onClick={() => onVersionSelect(version.version)}
                  disabled={isLoading}
                  className={`
                    relative px-2 py-1 rounded border text-xs transition-all
                    ${
                      version.is_active
                        ? "bg-blue-100 border-blue-300 text-blue-900 font-semibold"
                        : "bg-white border-gray-200 text-gray-700 hover:border-gray-300"
                    }
                    ${version.is_deprecated ? "opacity-60 line-through" : ""}
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                >
                  v{version.version}
                  {version.is_active && (
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-blue-600 rounded-full" />
                  )}
                </button>
              ))}
            </div>

            {/* Selected version details */}
            {versions.length > 0 && (
              <VersionDetailsPanel
                version={latestVersion}
                outputKey={outputKey}
                proposalId={proposalId}
                downloadToken={downloadToken}
              />
            )}
          </div>
        </CardBody>
      )}
    </Card>
  );
}

/**
 * VersionDetailsPanel: Detailed information for selected version
 * Phase 3-4: Version-specific download buttons
 */
function VersionDetailsPanel({
  version,
  outputKey,
  proposalId,
  downloadToken,
}: {
  version?: ArtifactVersionInfo;
  outputKey?: string;
  proposalId?: string;
  downloadToken?: string;
}) {
  const toast = useToast();

  // Phase 3-4: 버전별 DOCX 다운로드
  const handleVersionDownload = useCallback(async () => {
    if (!version || !proposalId || !downloadToken || outputKey !== "proposal") {
      toast.warning("이 버전은 다운로드할 수 없습니다");
      return;
    }

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${proposalId}/download/docx?version=${version.version}`,
        { headers: { Authorization: `Bearer ${downloadToken}` } },
      );
      if (!res.ok) throw new Error(`다운로드 실패 (${res.status})`);

      // Parse filename from Content-Disposition header
      const disposition = res.headers.get("Content-Disposition") ?? "";
      const match = disposition.match(
        /filename\*?=(?:UTF-8'')?["']?([^"';\r\n]+)["']?/i,
      );
      const filename = match
        ? decodeURIComponent(match[1])
        : `proposal_v${version.version}.docx`;

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);

      toast.success(`${filename} 다운로드 완료`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "다운로드 실패");
    }
  }, [version, proposalId, downloadToken, outputKey, toast]);

  if (!version) return null;

  const createdDate = new Date(version.created_at);
  const daysAgo = Math.floor(
    (Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24),
  );

  return (
    <div className="mt-3 pt-3 border-t bg-gray-50 rounded p-3 space-y-2 text-xs">
      {/* Created info */}
      <div className="flex items-center gap-2 text-gray-700">
        <Clock className="h-3 w-3 text-gray-500" />
        <div className="flex-1">
          <div className="font-semibold">생성일</div>
          <div className="text-gray-600">
            {createdDate.toLocaleDateString("ko-KR")}
            {daysAgo > 0 && (
              <span className="text-gray-500"> ({daysAgo}일 전)</span>
            )}
          </div>
        </div>
      </div>

      {/* Created by */}
      <div className="flex items-center gap-2 text-gray-700">
        <User className="h-3 w-3 text-gray-500" />
        <div className="flex-1">
          <div className="font-semibold">작성자</div>
          <div className="text-gray-600 truncate">{version.created_by}</div>
        </div>
      </div>

      {/* Created reason */}
      {version.created_reason && (
        <div className="flex gap-2">
          <GitBranch className="h-3 w-3 text-gray-500 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <div className="font-semibold">버전 사유</div>
            <div className="text-gray-600 capitalize">
              {version.created_reason}
            </div>
          </div>
        </div>
      )}

      {/* Status badges */}
      <div className="flex gap-2 flex-wrap pt-1">
        {version.is_active && <Badge variant="success">활성</Badge>}
        {version.is_deprecated && <Badge variant="warning">deprecated</Badge>}
        {version.artifact_size && (
          <Badge variant="info">
            {(version.artifact_size / 1024).toFixed(1)} KB
          </Badge>
        )}
      </div>

      {/* Dependencies */}
      {version.used_by && version.used_by.length > 0 && (
        <div className="pt-2 border-t mt-2">
          <div className="font-semibold mb-1">사용 중인 노드</div>
          <div className="space-y-1">
            {version.used_by.map((dep, idx) => (
              <div key={idx} className="text-gray-600 flex justify-between">
                <span>• {dep.node}</span>
                <span className="text-gray-500">({dep.count})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phase 3-4: Version-specific download button */}
      {proposalId && downloadToken && outputKey === "proposal" && (
        <div className="pt-2 border-t mt-2">
          <button
            onClick={handleVersionDownload}
            className="flex items-center gap-1 px-3 py-1 rounded text-xs bg-blue-500 text-white hover:bg-blue-600 transition-colors"
            title={`v${version.version} DOCX 다운로드`}
          >
            <Download className="h-3 w-3" />
            DOCX 다운로드
          </button>
        </div>
      )}
    </div>
  );
}
