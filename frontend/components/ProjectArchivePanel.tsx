"use client";

/**
 * ProjectArchivePanel — 프로젝트 아카이브 (중간 산출물 파일 일람)
 *
 * 마스터 파일 인덱스 표시 + 스냅샷 생성 + 개별/전체 다운로드.
 */

import { useCallback, useEffect, useState } from "react";
import { api, type ProjectArchiveFile, type ProjectManifest } from "@/lib/api";

const CATEGORY_LABELS: Record<string, string> = {
  rfp: "RFP/공고",
  analysis: "분석",
  strategy: "전략",
  plan: "계획",
  proposal: "제안서",
  presentation: "발표",
  bidding: "가격/비딩",
  review: "리뷰",
  submission: "제출서류",
  reference: "참고자료",
};

const FORMAT_ICONS: Record<string, string> = {
  md: "MD",
  txt: "TXT",
  docx: "DOCX",
  hwpx: "HWPX",
  pptx: "PPTX",
  pdf: "PDF",
  json: "JSON",
};

function formatBytes(bytes: number | null): string {
  if (!bytes) return "-";
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

interface Props {
  proposalId: string;
  className?: string;
}

export default function ProjectArchivePanel({
  proposalId,
  className = "",
}: Props) {
  const [manifest, setManifest] = useState<ProjectManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [snapshotting, setSnapshotting] = useState(false);
  const [snapshotResult, setSnapshotResult] = useState<string | null>(null);

  const loadManifest = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.projectArchive.manifest(proposalId);
      setManifest(data);
    } catch (e) {
      console.error("아카이브 로드 실패:", e);
    } finally {
      setLoading(false);
    }
  }, [proposalId]);

  useEffect(() => {
    loadManifest();
  }, [loadManifest]);

  async function handleSnapshot() {
    setSnapshotting(true);
    setSnapshotResult(null);
    try {
      const result = await api.projectArchive.snapshot(proposalId);
      setSnapshotResult(`${result.archived_count}개 산출물 아카이브 완료`);
      loadManifest();
    } catch (e) {
      setSnapshotResult(
        "스냅샷 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"),
      );
    } finally {
      setSnapshotting(false);
    }
  }

  function handleDownload(file: ProjectArchiveFile) {
    const url = api.projectArchive.downloadUrl(proposalId, file.doc_type);
    window.open(url, "_blank");
  }

  function handleBundleDownload(category?: string) {
    const url = api.projectArchive.bundleUrl(proposalId, category);
    window.open(url, "_blank");
  }

  if (loading) {
    return (
      <div className={`p-6 text-[#8c8c8c] text-sm ${className}`}>
        아카이브 로딩 중...
      </div>
    );
  }

  const categories = manifest?.categories || {};
  const sortedCategories = Object.keys(CATEGORY_LABELS).filter(
    (k) => categories[k]?.length,
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[#ededed]">
            프로젝트 산출물 아카이브
          </h3>
          <p className="text-xs text-[#8c8c8c] mt-0.5">
            {manifest?.total_count || 0}개 파일 /{" "}
            {formatBytes(manifest?.total_size || 0)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSnapshot}
            disabled={snapshotting}
            className="px-3 py-1.5 text-xs font-medium rounded bg-[#3ecf8e]/15 text-[#3ecf8e] border border-[#3ecf8e]/30 hover:bg-[#3ecf8e]/25 disabled:opacity-50 transition-colors"
          >
            {snapshotting ? "스냅샷 생성 중..." : "스냅샷 생성"}
          </button>
          {(manifest?.total_count || 0) > 0 && (
            <button
              onClick={() => handleBundleDownload()}
              className="px-3 py-1.5 text-xs font-medium rounded bg-[#262626] text-[#ededed] border border-[#404040] hover:bg-[#333] transition-colors"
            >
              전체 ZIP
            </button>
          )}
        </div>
      </div>

      {snapshotResult && (
        <div
          className={`text-xs px-3 py-2 rounded ${
            snapshotResult.includes("실패")
              ? "bg-red-500/10 text-red-400 border border-red-500/20"
              : "bg-[#3ecf8e]/10 text-[#3ecf8e] border border-[#3ecf8e]/20"
          }`}
        >
          {snapshotResult}
        </div>
      )}

      {/* 카테고리별 파일 목록 */}
      {sortedCategories.length === 0 ? (
        <div className="text-center py-12 text-[#8c8c8c] text-sm">
          <p>아카이브된 산출물이 없습니다.</p>
          <p className="text-xs mt-1">
            &quot;스냅샷 생성&quot;을 눌러 현재 워크플로 산출물을 파일화하세요.
          </p>
        </div>
      ) : (
        sortedCategories.map((cat) => (
          <div
            key={cat}
            className="border border-[#262626] rounded-lg overflow-hidden"
          >
            <div className="flex items-center justify-between px-3 py-2 bg-[#1a1a1a] border-b border-[#262626]">
              <span className="text-xs font-medium text-[#ededed]">
                {CATEGORY_LABELS[cat] || cat} ({categories[cat].length})
              </span>
              {categories[cat].length > 1 && (
                <button
                  onClick={() => handleBundleDownload(cat)}
                  className="text-[10px] text-[#8c8c8c] hover:text-[#3ecf8e] transition-colors"
                >
                  ZIP
                </button>
              )}
            </div>
            <div className="divide-y divide-[#1a1a1a]">
              {categories[cat].map((file: ProjectArchiveFile) => (
                <div
                  key={file.id || `${file.doc_type}-${file.version}`}
                  className="flex items-center justify-between px-3 py-2 hover:bg-[#1a1a1a] transition-colors group"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="inline-flex items-center justify-center w-9 h-5 rounded text-[9px] font-mono font-bold bg-[#262626] text-[#8c8c8c] shrink-0">
                      {FORMAT_ICONS[file.file_format] ||
                        file.file_format?.toUpperCase()}
                    </span>
                    <span className="text-xs text-[#ededed] truncate">
                      {file.title}
                    </span>
                    {file.version > 1 && (
                      <span className="text-[9px] text-[#8c8c8c]">
                        v{file.version}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-[10px] text-[#666]">
                      {formatBytes(file.file_size)}
                    </span>
                    {file.storage_path && (
                      <button
                        onClick={() => handleDownload(file)}
                        className="text-[10px] text-[#8c8c8c] hover:text-[#3ecf8e] opacity-0 group-hover:opacity-100 transition-all"
                      >
                        다운로드
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
