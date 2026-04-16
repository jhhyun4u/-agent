/**
 * useVaultStep Hook
 * 제안 단계별 상태 관리 및 데이터 페칭
 */

import { useState, useCallback, useEffect } from 'react';

interface VaultResponse {
  step: number;
  title: string;
  content: string;
  sources: Array<{
    title: string;
    type: 'credential' | 'client' | 'bidding' | 'personnel' | 'internal';
    relevance: number;
  }>;
  confidence: number;
  lastUpdated: Date;
  dataPoints: number;
}

interface StepData {
  [key: number]: VaultResponse | null;
}

interface UseVaultStepOptions {
  proposalId: string;
  initialStep?: number;
  autoFetch?: boolean;
}

export const useVaultStep = ({
  proposalId,
  initialStep = 1,
  autoFetch = true,
}: UseVaultStepOptions) => {
  const [currentStep, setCurrentStep] = useState<number>(initialStep);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [stepData, setStepData] = useState<StepData>({});
  const [history, setHistory] = useState<Array<{ step: number; timestamp: Date }>>([]);

  /**
   * Fetch vault response for a specific step
   */
  const fetchStepData = useCallback(
    async (step: number) => {
      if (stepData[step]) {
        // Use cached data
        return stepData[step];
      }

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/vault/step/${step}?proposalId=${proposalId}`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch step ${step} data`);
        }

        const data: VaultResponse = await response.json();

        // Cache the response
        setStepData((prev) => ({
          ...prev,
          [step]: data,
        }));

        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [proposalId, stepData]
  );

  /**
   * Change current step and fetch data
   */
  const goToStep = useCallback(
    async (step: number) => {
      if (step < 1 || step > 5) {
        setError('Step must be between 1 and 5');
        return;
      }

      setCurrentStep(step);

      // Record in history
      setHistory((prev) => [
        ...prev,
        { step, timestamp: new Date() },
      ]);

      if (autoFetch) {
        await fetchStepData(step);
      }
    },
    [autoFetch, fetchStepData]
  );

  /**
   * Move to next step
   */
  const nextStep = useCallback(async () => {
    if (currentStep < 5) {
      await goToStep(currentStep + 1);
    }
  }, [currentStep, goToStep]);

  /**
   * Move to previous step
   */
  const previousStep = useCallback(async () => {
    if (currentStep > 1) {
      await goToStep(currentStep - 1);
    }
  }, [currentStep, goToStep]);

  /**
   * Refresh current step data (bypass cache)
   */
  const refreshStep = useCallback(async () => {
    setStepData((prev) => {
      const updated = { ...prev };
      delete updated[currentStep];
      return updated;
    });

    await fetchStepData(currentStep);
  }, [currentStep, fetchStepData]);

  /**
   * Get current step data
   */
  const getCurrentData = useCallback((): VaultResponse | null => {
    return stepData[currentStep] || null;
  }, [currentStep, stepData]);

  /**
   * Check if step is available (has data)
   */
  const isStepAvailable = useCallback(
    (step: number): boolean => {
      return stepData[step] !== null && stepData[step] !== undefined;
    },
    [stepData]
  );

  /**
   * Get all completed steps
   */
  const getCompletedSteps = useCallback((): number[] => {
    return Object.keys(stepData)
      .map(Number)
      .filter((step) => stepData[step] !== null);
  }, [stepData]);

  /**
   * Auto-fetch on mount and when proposalId changes
   */
  useEffect(() => {
    if (autoFetch && proposalId) {
      fetchStepData(currentStep);
    }
  }, [proposalId, autoFetch, currentStep, fetchStepData]);

  return {
    // State
    currentStep,
    loading,
    error,
    stepData,
    history,

    // Navigation
    goToStep,
    nextStep,
    previousStep,
    refreshStep,

    // Data access
    getCurrentData,
    isStepAvailable,
    getCompletedSteps,
  };
};

/**
 * Hook for managing step transitions with validation
 */
export const useStepTransition = (
  currentStep: number,
  validationRules?: Record<number, () => boolean>
) => {
  const [canProceed, setCanProceed] = useState<boolean>(true);
  const [validation, setValidation] = useState<{
    step: number;
    valid: boolean;
    errors: string[];
  }>({
    step: currentStep,
    valid: true,
    errors: [],
  });

  const validateStep = useCallback((step: number): boolean => {
    if (!validationRules || !validationRules[step]) {
      return true;
    }

    try {
      const isValid = validationRules[step]();
      const errors: string[] = [];

      if (!isValid) {
        errors.push(`Step ${step} validation failed`);
      }

      setValidation({
        step,
        valid: isValid,
        errors,
      });

      return isValid;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Validation error';
      setValidation({
        step,
        valid: false,
        errors: [errorMsg],
      });
      return false;
    }
  }, [validationRules]);

  // Validate on step change
  useEffect(() => {
    validateStep(currentStep);
  }, [currentStep, validateStep]);

  return {
    canProceed,
    validation,
    validateStep,
  };
};

/**
 * Hook for managing step-specific metadata
 */
export const useStepMetadata = () => {
  const stepMetadata = {
    1: {
      title: 'Go/No-Go 의사결정',
      description: '발주처 정보, 유사 사례, 팀 역량 분석',
      icon: 'CheckCircle',
      color: 'blue',
    },
    2: {
      title: '제안 전략',
      description: '경쟁 분석, 입찰 전략, 포지셔닝',
      icon: 'Target',
      color: 'purple',
    },
    3: {
      title: '계획 & 팀 구성',
      description: '가용 인력, 팀 추천, 일정 계획',
      icon: 'Users',
      color: 'green',
    },
    4: {
      title: '제안서 작성',
      description: '신뢰성 사례, 가격 분석, 콘텐츠 참고',
      icon: 'FileText',
      color: 'orange',
    },
    5: {
      title: '발표 전략',
      description: '발표 전략, 청중 분석, Q&A 대비',
      icon: 'Presentation',
      color: 'red',
    },
  };

  const getStepMetadata = useCallback((step: number) => {
    return (
      stepMetadata[step as keyof typeof stepMetadata] || {
        title: 'Unknown Step',
        description: '',
        icon: 'HelpCircle',
        color: 'gray',
      }
    );
  }, []);

  return {
    stepMetadata,
    getStepMetadata,
  };
};

/**
 * Hook for managing step export/download
 */
export const useStepExport = () => {
  const [exporting, setExporting] = useState<boolean>(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const exportStep = useCallback(
    async (step: number, proposalId: string, format: 'pdf' | 'docx' = 'pdf') => {
      setExporting(true);
      setExportError(null);

      try {
        const response = await fetch(`/api/vault/export`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            proposalId,
            step,
            format,
          }),
        });

        if (!response.ok) {
          throw new Error('Export failed');
        }

        // Get blob and trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `step-${step}-${Date.now()}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setExportError(message);
      } finally {
        setExporting(false);
      }
    },
    []
  );

  return {
    exporting,
    exportError,
    exportStep,
  };
};

/**
 * Hook for managing step sharing
 */
export const useStepSharing = () => {
  const [sharing, setSharing] = useState<boolean>(false);
  const [shareError, setShareError] = useState<string | null>(null);
  const [shareLink, setShareLink] = useState<string | null>(null);

  const shareStep = useCallback(
    async (
      step: number,
      proposalId: string,
      options?: { expiresIn?: number; password?: string }
    ) => {
      setSharing(true);
      setShareError(null);

      try {
        const response = await fetch(`/api/vault/share`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            proposalId,
            step,
            ...options,
          }),
        });

        if (!response.ok) {
          throw new Error('Share failed');
        }

        const data = await response.json();
        setShareLink(data.shareLink);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setShareError(message);
      } finally {
        setSharing(false);
      }
    },
    []
  );

  const copyShareLink = useCallback(() => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink);
    }
  }, [shareLink]);

  return {
    sharing,
    shareError,
    shareLink,
    shareStep,
    copyShareLink,
  };
};
