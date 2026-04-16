/**
 * Vault Chat Step Selector
 * 제안 단계(1~5) 선택 드롭다운 및 자동 감지
 */

import React, { useState, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface VaultStepSelectorProps {
  currentStep: number;
  proposalStep?: number;
  onChange: (step: number) => void;
  disabled?: boolean;
}

const STEP_LABELS = {
  1: 'Go/No-Go 의사결정',
  2: '제안 전략',
  3: '계획 & 팀 구성',
  4: '제안서 작성',
  5: '발표 전략',
};

const STEP_DESCRIPTIONS = {
  1: '발주처 정보, 유사 사례, 팀 역량 분석',
  2: '경쟁 분석, 입찰 전략, 포지셔닝',
  3: '가용 인력, 팀 추천, 일정 계획',
  4: '신뢰성 사례, 가격 분석, 콘텐츠 참고',
  5: '발표 전략, 청중 분석, Q&A 대비',
};

export const VaultStepSelector: React.FC<VaultStepSelectorProps> = ({
  currentStep,
  proposalStep,
  onChange,
  disabled = false,
}) => {
  const [autoDetected, setAutoDetected] = useState(false);

  // 제안서의 현재 단계에서 자동으로 Step 감지
  useEffect(() => {
    if (proposalStep && proposalStep !== currentStep) {
      // 제안서 단계를 Vault Step으로 매핑
      const mappedStep = Math.min(proposalStep, 5);
      onChange(mappedStep);
      setAutoDetected(true);

      // 3초 후 자동 감지 배지 숨김
      const timer = setTimeout(() => setAutoDetected(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [proposalStep]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">Vault Step 선택</label>
        {autoDetected && (
          <Badge variant="outline" className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            자동 감지됨
          </Badge>
        )}
      </div>

      <Select
        value={currentStep.toString()}
        onValueChange={(value) => onChange(parseInt(value))}
        disabled={disabled}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Step 선택" />
        </SelectTrigger>
        <SelectContent>
          {[1, 2, 3, 4, 5].map((step) => (
            <SelectItem key={step} value={step.toString()}>
              <div className="flex items-center gap-2">
                <span className="font-medium">Step {step}:</span>
                <span className="text-sm">{STEP_LABELS[step as keyof typeof STEP_LABELS]}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Step 설명 */}
      <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
        <p className="text-xs text-blue-900">
          <span className="font-semibold">Step {currentStep}:</span>{' '}
          {STEP_DESCRIPTIONS[currentStep as keyof typeof STEP_DESCRIPTIONS]}
        </p>
      </div>

      {/* Step 진행도 시각화 */}
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((step) => (
          <div
            key={step}
            className={`flex-1 h-1 rounded-full transition-colors ${
              step === currentStep
                ? 'bg-blue-600'
                : step < currentStep
                  ? 'bg-green-500'
                  : 'bg-gray-300'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default VaultStepSelector;
