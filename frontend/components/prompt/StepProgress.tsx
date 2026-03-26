"use client";

/**
 * StepProgress — 4스텝 진행 표시기
 *
 * 문제파악 → 개선안 → 시뮬레이션 → 실험
 */

const STEPS = [
  { id: "diagnose", label: "문제파악" },
  { id: "suggest", label: "개선안" },
  { id: "simulate", label: "시뮬레이션" },
  { id: "experiment", label: "실험" },
] as const;

type StepId = (typeof STEPS)[number]["id"];

interface StepProgressProps {
  currentStep: StepId;
  onStepClick?: (step: StepId) => void;
}

export default function StepProgress({ currentStep, onStepClick }: StepProgressProps) {
  const currentIdx = STEPS.findIndex((s) => s.id === currentStep);

  return (
    <div className="flex items-center gap-1">
      {STEPS.map((step, i) => {
        const isDone = i < currentIdx;
        const isCurrent = i === currentIdx;
        const isFuture = i > currentIdx;

        return (
          <div key={step.id} className="flex items-center gap-1">
            <button
              onClick={() => onStepClick?.(step.id)}
              disabled={isFuture}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isCurrent
                  ? "bg-[#3ecf8e] text-black"
                  : isDone
                    ? "bg-[#1a3a2a] text-[#3ecf8e] hover:bg-[#2a4a3a]"
                    : "bg-[#1c1c1c] text-[#666] cursor-not-allowed"
              }`}
            >
              {isDone ? "✓ " : `${i + 1}. `}{step.label}
            </button>
            {i < STEPS.length - 1 && (
              <span className={`text-xs ${isDone ? "text-[#3ecf8e]" : "text-[#333]"}`}>→</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

export type { StepId };
