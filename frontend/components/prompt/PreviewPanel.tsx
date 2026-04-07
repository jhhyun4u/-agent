"use client";

/**
 * PreviewPanel — 변수 슬롯 + 렌더링 미리보기
 *
 * 프롬프트 내 {variable}을 샘플 값으로 치환한 최종 프롬프트를 표시.
 */

import { useMemo, useState } from "react";

interface PreviewPanelProps {
  promptText: string;
}

const DEFAULT_SAMPLES: Record<string, string> = {
  rfp_text:
    "[샘플] 정보시스템 구축 용역 제안요청서. 사업 기간: 6개월, 예산: 3억원...",
  strategy: '{"win_theme": "고객 맞춤형 방법론", "positioning": "offensive"}',
  positioning_guide: "공격적 포지셔닝: 차별화된 기술력 강조",
  prev_sections_context: "(이전 섹션 요약 텍스트)",
  storyline_context:
    '{"key_message": "핵심 메시지", "narrative_arc": "서사 구조"}',
  rfp_analysis: '{"project_name": "샘플 ISP", "budget": 300000000}',
  go_no_go: '{"verdict": "go", "confidence": 85}',
  section_type: "UNDERSTAND",
  bid_text: "[샘플 공고 본문]",
};

export default function PreviewPanel({ promptText }: PreviewPanelProps) {
  const variables = useMemo(
    () => [
      ...new Set(
        (promptText.match(/\{(\w+)\}/g) ?? []).map((v) => v.slice(1, -1)),
      ),
    ],
    [promptText],
  );

  const [overrides, setOverrides] = useState<Record<string, string>>({});

  const rendered = useMemo(() => {
    let text = promptText;
    for (const v of variables) {
      const val = overrides[v] || DEFAULT_SAMPLES[v] || `[${v}]`;
      text = text.replaceAll(`{${v}}`, val);
    }
    return text;
  }, [promptText, variables, overrides]);

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold">변수 슬롯 ({variables.length})</h3>

      {variables.length > 0 ? (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {variables.map((v) => (
            <div key={v} className="flex items-start gap-2">
              <span className="text-xs font-mono text-[#60a5fa] bg-[#0a0a0a] px-2 py-1 rounded shrink-0 mt-0.5">
                {`{${v}}`}
              </span>
              <input
                type="text"
                value={overrides[v] ?? ""}
                onChange={(e) =>
                  setOverrides((p) => ({ ...p, [v]: e.target.value }))
                }
                placeholder={DEFAULT_SAMPLES[v]?.slice(0, 50) ?? `${v} 값 입력`}
                className="flex-1 bg-[#0a0a0a] border border-[#262626] rounded px-2 py-1 text-xs focus:border-[#3ecf8e] focus:outline-none"
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-[#8c8c8c]">변수 없음</div>
      )}

      <h3 className="text-xs font-semibold mt-4">렌더링된 프롬프트</h3>
      <pre className="p-3 bg-[#0a0a0a] rounded text-xs text-[#8c8c8c] overflow-x-auto max-h-72 whitespace-pre-wrap">
        {rendered.slice(0, 3000)}
        {rendered.length > 3000 && "\n... (truncated)"}
      </pre>
    </div>
  );
}
