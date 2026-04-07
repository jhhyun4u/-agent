"use client";

/**
 * 권고 #2: 초보 사용자 가이드 투어
 *
 * 각 페이지에서 핵심 기능을 단계별로 안내하는 투어 오버레이.
 * 첫 방문 시 자동 표시, 이후 "?" 버튼으로 재실행 가능.
 */

import { useCallback, useEffect, useState } from "react";

export interface TourStep {
  /** 하이라이트할 요소의 CSS selector (없으면 중앙 표시) */
  selector?: string;
  /** 제목 */
  title: string;
  /** 설명 */
  description: string;
  /** 팝오버 위치 */
  position?: "top" | "bottom" | "left" | "right" | "center";
}

interface Props {
  /** 투어 ID (localStorage 키 접미사) */
  tourId: string;
  /** 투어 단계 정의 */
  steps: TourStep[];
  /** 자동 시작 여부 (첫 방문) */
  autoStart?: boolean;
  /** 투어 완료 콜백 */
  onComplete?: () => void;
}

// ── 페이지별 투어 데이터 ──

export const TOUR_DASHBOARD: TourStep[] = [
  {
    title: "대시보드",
    description:
      "수주 현황, 파이프라인, 분석 차트를 한눈에 확인하세요. 상단 스코프 탭으로 개인/팀/본부/전체를 전환할 수 있습니다.",
    position: "center",
  },
  {
    title: "지금 해야 할 것",
    description:
      "마감이 가까운 RFP와 진행 중인 제안서가 우선순위순으로 표시됩니다. '지금 시작'을 클릭하면 제안서 작성이 바로 시작됩니다.",
    position: "center",
  },
  {
    title: "제안 파이프라인",
    description:
      "공고 등록 → 작성 중 → 완료 → 결과 대기 → 수주/실패까지 전체 흐름을 볼 수 있습니다. 숫자를 클릭하면 해당 목록으로 이동합니다.",
    position: "center",
  },
];

export const TOUR_BIDS: TourStep[] = [
  {
    title: "공고 모니터링",
    description:
      "G2B 나라장터 공고를 검색하고, AI가 우리 회사에 적합한 과제를 추천합니다. S/A 등급이 높을수록 적합도가 높습니다.",
    position: "center",
  },
  {
    title: "프리셋",
    description:
      "자주 사용하는 검색 조건(키워드, 지역, 예산)을 프리셋으로 저장하면 반복 검색이 편리합니다.",
    position: "center",
  },
  {
    title: "제안 착수",
    description:
      "관심 공고를 선택하면 AI가 RFP를 분석하고, Go/No-Go 판정부터 제안서 작성까지 5단계를 안내합니다.",
    position: "center",
  },
];

export const TOUR_PROPOSAL_DETAIL: TourStep[] = [
  {
    title: "제안서 워크플로",
    description:
      "AI가 5단계(RFP분석→전략→계획→작성→PPT)를 순서대로 진행합니다. 각 단계마다 여러분이 검토하고 승인/재작업을 결정합니다.",
    position: "center",
  },
  {
    title: "리뷰 게이트",
    description:
      "노란색 배너가 나타나면 AI가 결과를 만들고 여러분의 확인을 기다리는 중입니다. '빠른 승인'으로 바로 넘기거나, 피드백을 남길 수 있습니다.",
    position: "center",
  },
  {
    title: "3-Stream 병행",
    description:
      "Go 결정 이후부터 '정성제안서', '비딩관리', '제출서류' 3개 탭이 활성화됩니다. 각 스트림은 독립적으로 진행하되, 최종 제출 시 모두 완료되어야 합니다.",
    position: "center",
  },
  {
    title: "편집 버튼",
    description:
      "오른쪽 상단 '편집' 버튼을 클릭하면 3-Column 에디터가 열립니다. AI 제안을 직접 수정하거나, AI에게 질문할 수 있습니다.",
    position: "center",
  },
];

export const TOUR_EDITOR: TourStep[] = [
  {
    title: "3-Column 에디터",
    description:
      "왼쪽: 목차+규정 준수 현황 | 중앙: 제안서 본문 편집 | 오른쪽: AI 어시스턴트. 세 영역을 동시에 활용하며 제안서를 다듬으세요.",
    position: "center",
  },
  {
    title: "AI 어시스턴트",
    description:
      "오른쪽 패널에서 AI에게 질문하거나, 특정 문장을 선택해 '개선/확장/축소'를 요청할 수 있습니다.",
    position: "center",
  },
  {
    title: "섹션 잠금",
    description:
      "다른 팀원이 같은 섹션을 편집 중이면 잠금 아이콘이 표시됩니다. 5분 후 자동 해제됩니다.",
    position: "center",
  },
];

export const TOUR_KB: TourStep[] = [
  {
    title: "지식 베이스",
    description:
      "콘텐츠, 발주기관, 경쟁사, 교훈, 노임단가, 낙찰정보, Q&A — 7개 영역의 조직 지식을 관리합니다. 프로젝트를 거듭할수록 자동으로 쌓입니다.",
    position: "center",
  },
  {
    title: "통합 검색",
    description:
      "상단 검색(/kb/search)에서 모든 KB를 한 번에 검색할 수 있습니다. AI가 제안서 작성 시 이 지식을 자동으로 참조합니다.",
    position: "center",
  },
];

// ── 메인 컴포넌트 ──

export default function GuidedTour({
  tourId,
  steps,
  autoStart = true,
  onComplete,
}: Props) {
  const [active, setActive] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(0);

  const storageKey = `tenopa-tour-${tourId}`;

  // 첫 방문 시 자동 시작
  useEffect(() => {
    if (!autoStart) return;
    const seen = localStorage.getItem(storageKey);
    if (!seen) {
      // 페이지 렌더 후 500ms 대기
      const timer = setTimeout(() => setActive(true), 500);
      return () => clearTimeout(timer);
    }
  }, [autoStart, storageKey]);

  const handleNext = useCallback(() => {
    if (currentIdx < steps.length - 1) {
      setCurrentIdx(currentIdx + 1);
    } else {
      // 투어 완료
      localStorage.setItem(storageKey, "1");
      setActive(false);
      setCurrentIdx(0);
      onComplete?.();
    }
  }, [currentIdx, steps.length, storageKey, onComplete]);

  const handleSkip = useCallback(() => {
    localStorage.setItem(storageKey, "1");
    setActive(false);
    setCurrentIdx(0);
  }, [storageKey]);

  // 외부에서 투어 시작 트리거
  function startTour() {
    setCurrentIdx(0);
    setActive(true);
  }

  if (!active) {
    // "?" 아이콘 — 투어 재실행
    return (
      <button
        onClick={startTour}
        className="fixed bottom-6 left-6 z-50 w-9 h-9 rounded-full bg-[#262626] border border-[#363636] text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3ecf8e]/50 flex items-center justify-center text-sm font-bold transition-all shadow-lg"
        title="가이드 투어 보기"
      >
        ?
      </button>
    );
  }

  const step = steps[currentIdx];
  const isLast = currentIdx === steps.length - 1;

  return (
    <div className="fixed inset-0 z-[100]">
      {/* 배경 오버레이 */}
      <div className="absolute inset-0 bg-black/70" onClick={handleSkip} />

      {/* 투어 카드 */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="bg-[#1c1c1c] border border-[#3ecf8e]/30 rounded-2xl p-6 max-w-md w-[90vw] shadow-2xl pointer-events-auto">
          {/* 진행률 */}
          <div className="flex items-center gap-2 mb-4">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  i <= currentIdx ? "bg-[#3ecf8e]" : "bg-[#262626]"
                }`}
              />
            ))}
          </div>

          {/* 스텝 번호 */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] text-[#3ecf8e] font-medium uppercase tracking-wider">
              {currentIdx + 1} / {steps.length}
            </span>
          </div>

          {/* 제목 */}
          <h3 className="text-base font-semibold text-[#ededed] mb-2">
            {step.title}
          </h3>

          {/* 설명 */}
          <p className="text-sm text-[#8c8c8c] leading-relaxed mb-5">
            {step.description}
          </p>

          {/* 버튼 */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleSkip}
              className="text-xs text-[#8c8c8c] hover:text-[#ededed] transition-colors"
            >
              건너뛰기
            </button>
            <button
              onClick={handleNext}
              className="px-5 py-2 text-sm font-semibold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 transition-colors"
            >
              {isLast ? "완료" : "다음"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 도움말 툴팁 — 리뷰 게이트 등 개별 요소에 "이 단계란?" 설명 추가
 */
export function HelpTooltip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-flex">
      <button
        onClick={() => setOpen(!open)}
        className="w-4 h-4 rounded-full bg-[#262626] border border-[#363636] text-[10px] text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3ecf8e]/50 flex items-center justify-center transition-colors"
        title="도움말"
      >
        ?
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-6 top-0 z-50 w-60 bg-[#1c1c1c] border border-[#262626] rounded-lg shadow-xl p-3">
            <p className="text-[10px] text-[#8c8c8c] leading-relaxed">{text}</p>
          </div>
        </>
      )}
    </span>
  );
}
