"use client";

/**
 * WorkflowMap — 제안서 작성 워크플로에서 프롬프트 위치 시각화
 */

import Link from "next/link";
import type { WorkflowMapData } from "@/lib/api";

interface WorkflowMapProps {
  data: WorkflowMapData;
  onNodeClick?: (nodeId: string) => void;
}

export default function WorkflowMap({ data, onNodeClick }: WorkflowMapProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold">워크플로 맵</h3>
      <div className="flex flex-wrap items-center gap-1">
        {data.nodes.map((node, i) => (
          <div key={node.id} className="flex items-center gap-1">
            <button
              onClick={() => onNodeClick?.(node.id)}
              className="px-3 py-2 bg-[#1c1c1c] hover:bg-[#262626] border border-[#262626] rounded-lg transition-colors text-left"
            >
              <div className="text-xs font-medium text-[#ededed]">{node.label}</div>
              <div className="text-[10px] text-[#8c8c8c]">{node.prompt_count}개 프롬프트</div>
            </button>
            {i < data.nodes.length - 1 && (
              <span className="text-[#333] text-xs">→</span>
            )}
          </div>
        ))}
      </div>
      <div className="text-[10px] text-[#666]">
        * 노드 클릭 시 해당 프롬프트만 필터링
      </div>
    </div>
  );
}
