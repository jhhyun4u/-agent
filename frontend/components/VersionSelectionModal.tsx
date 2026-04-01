"use client";

/**
 * VersionSelectionModal Component
 *
 * Phase 1: Artifact Versioning System
 *
 * Displays when moving to a node with version conflicts.
 * Allows user to select which version to use for required inputs.
 *
 * Features:
 * - Multi-tab version selector
 * - Dependency warning display
 * - Auto-recommendation based on version metadata
 * - Version history (created_at, created_by)
 * - Used_by indicators (which nodes depend on this version)
 */

import React, { useState, useMemo } from "react";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { AlertCircle, Check, ChevronRight } from "lucide-react";

export interface VersionConflict {
  input_key: string;
  versions?: number[];
  status: "SINGLE" | "MULTIPLE" | "MISSING";
  dependency_level?: string;
}

export interface VersionMetadata {
  version: number;
  created_at: string;
  created_by: string;
  is_active: boolean;
  is_deprecated: boolean;
  used_by?: Array<{ node: string; count: number }>;
  created_reason?: string;
}

export interface VersionSelectionModalProps {
  conflicts: VersionConflict[];
  availableVersions: Record<string, VersionMetadata[]>;
  onSelect: (selections: Record<string, number>) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export function VersionSelectionModal({
  conflicts,
  availableVersions,
  onSelect,
  onCancel,
  loading = false,
}: VersionSelectionModalProps) {
  const [selections, setSelections] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Recommend versions for missing selections
  const recommendations = useMemo(() => {
    const recs: Record<string, number> = {};

    conflicts.forEach((conflict) => {
      if (
        conflict.status === "MULTIPLE" &&
        conflict.versions &&
        conflict.versions.length > 0
      ) {
        const versions = availableVersions[conflict.input_key] || [];

        // Smart recommendation: active > latest > most-used
        const recommendedVersion =
          versions.find((v) => v.is_active)?.version ||
          Math.max(...versions.map((v) => v.version)) ||
          conflict.versions[0];

        recs[conflict.input_key] = recommendedVersion;
      }
    });

    return recs;
  }, [conflicts, availableVersions]);

  const handleVersionSelect = (key: string, version: number) => {
    setSelections((prev) => ({
      ...prev,
      [key]: version,
    }));
  };

  const handleConfirm = async () => {
    // Merge explicit selections with recommendations
    const finalSelections = {
      ...recommendations,
      ...selections,
    };

    setIsSubmitting(true);
    try {
      await onSelect(finalSelections);
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasConflicts = conflicts.some(
    (c) => c.status === "MULTIPLE" || c.status === "MISSING",
  );
  const hasMultipleConflicts = conflicts.some((c) => c.status === "MULTIPLE");
  const hasMissingInputs = conflicts.some((c) => c.status === "MISSING");

  const isReadyToSubmit = hasMissingInputs
    ? false
    : !hasMultipleConflicts || Object.keys(selections).length > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="border-b">
          <div className="space-y-2">
            <h3 className="card-title text-lg">산출물 버전 선택</h3>
            <p className="text-sm text-gray-600">
              작업 이동 시 어떤 버전을 사용할지 선택해주세요. 여러 버전이 있는
              경우 추천된 버전을 선택할 수 있습니다.
            </p>
          </div>
        </CardHeader>

        <CardBody className="space-y-6 p-6">
          {/* Missing inputs alert */}
          {hasMissingInputs && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                필수 입력 자료가 없어 이동할 수 없습니다. 필요한 노드를 먼저
                실행해주세요.
              </AlertDescription>
            </Alert>
          )}

          {/* Conflicts display */}
          {conflicts.map((conflict) => (
            <ConflictCard
              key={conflict.input_key}
              conflict={conflict}
              versions={availableVersions[conflict.input_key] || []}
              selected={selections[conflict.input_key]}
              recommended={recommendations[conflict.input_key]}
              onSelect={(v) => handleVersionSelect(conflict.input_key, v)}
            />
          ))}

          {/* Dependency warnings */}
          {hasConflicts && (
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              <AlertDescription className="text-yellow-800">
                이 노드의 출력물이 다른 노드에서 사용 중입니다. 버전 선택 후
                후행 노드에서 재작업이 필요할 수 있습니다.
              </AlertDescription>
            </Alert>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 justify-end pt-4 border-t">
            <Button
              variant="secondary"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              취소
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={!isReadyToSubmit || isSubmitting}
            >
              {isSubmitting ? "처리 중..." : "선택 완료"}
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

/**
 * ConflictCard: Individual conflict resolution UI
 */
function ConflictCard({
  conflict,
  versions,
  selected,
  recommended,
  onSelect,
}: {
  conflict: VersionConflict;
  versions: VersionMetadata[];
  selected?: number;
  recommended?: number;
  onSelect: (v: number) => void;
}) {
  if (conflict.status === "MISSING") {
    return (
      <div className="border rounded-lg p-4 bg-red-50">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-red-900">{conflict.input_key}</h3>
            <p className="text-sm text-red-800 mt-1">
              필수 입력이 없습니다. 필요한 노드를 먼저 실행해주세요.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (conflict.status === "SINGLE") {
    return (
      <div className="border rounded-lg p-4 bg-green-50">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-green-900">{conflict.input_key}</h3>
          <div className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-600" />
            <span className="text-sm text-green-700">
              v{conflict.versions?.[0]}
            </span>
          </div>
        </div>
        <p className="text-xs text-green-700 mt-1">
          사용 가능한 버전 1개 (자동 선택됨)
        </p>
      </div>
    );
  }

  // MULTIPLE status
  return (
    <div className="border rounded-lg p-4">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">{conflict.input_key}</h3>
          <Badge variant="warning">여러 버전</Badge>
        </div>
        <p className="text-xs text-gray-600">
          {versions.length}개의 버전 중 하나를 선택해주세요.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {versions.map((version) => (
          <button
            key={version.version}
            onClick={() => onSelect(version.version)}
            className={`
              relative px-3 py-2 rounded border text-sm transition-all
              ${
                selected === version.version
                  ? "bg-blue-100 border-blue-500 text-blue-900 ring-2 ring-blue-200"
                  : "bg-white border-gray-200 text-gray-700 hover:border-gray-300"
              }
              ${
                recommended === version.version && selected !== version.version
                  ? "ring-2 ring-yellow-300"
                  : ""
              }
            `}
          >
            <div className="font-semibold">v{version.version}</div>
            <div className="text-xs mt-1 opacity-75">
              {new Date(version.created_at).toLocaleDateString("ko-KR")}
            </div>

            {/* Recommendation badge */}
            {recommended === version.version && (
              <div className="absolute -top-2 -right-2">
                <Badge variant="success" size="xs">
                  추천
                </Badge>
              </div>
            )}

            {/* Active badge */}
            {version.is_active && (
              <div className="absolute -top-2 -left-2">
                <Badge variant="warning" size="xs">
                  활성
                </Badge>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Version details */}
      {selected !== undefined && (
        <VersionDetails
          version={versions.find((v) => v.version === selected)}
        />
      )}
    </div>
  );
}

/**
 * VersionDetails: Show metadata for selected version
 */
function VersionDetails({ version }: { version?: VersionMetadata }) {
  if (!version) return null;

  return (
    <div className="mt-3 pt-3 border-t bg-gray-50 rounded p-2 text-xs text-gray-600 space-y-1">
      <div className="flex justify-between">
        <span>작성일:</span>
        <span>{new Date(version.created_at).toLocaleString("ko-KR")}</span>
      </div>
      <div className="flex justify-between">
        <span>작성자:</span>
        <span className="truncate ml-2">{version.created_by}</span>
      </div>
      {version.created_reason && (
        <div className="flex justify-between">
          <span>사유:</span>
          <span>{version.created_reason}</span>
        </div>
      )}
      {version.used_by && version.used_by.length > 0 && (
        <div className="flex justify-between">
          <span>사용 중인 노드:</span>
          <span>{version.used_by.length}개</span>
        </div>
      )}
    </div>
  );
}
