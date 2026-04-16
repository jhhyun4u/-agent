/**
 * Vault Feedback Form
 * 각 Step 사용 후 피드백 수집
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Star, ThumbsUp, ThumbsDown, MessageCircle } from 'lucide-react';

interface FeedbackFormProps {
  step: number;
  proposalId: string;
  onSubmit?: (feedback: FeedbackData) => void;
  onClose?: () => void;
}

interface FeedbackData {
  step: number;
  proposalId: string;
  timestamp: Date;

  // 만족도 (1~10 스케일)
  helpfulness: number; // "이 정보가 의사결정에 도움이 되었나?"
  accuracy: number;    // "정확도는?"
  relevance: number;   // "관련도는?"

  // 이진 응답
  wouldUseInWork: boolean; // "실무에서 사용하겠나?"

  // 텍스트 피드백
  improvements: string; // "개선할 점?"
  suggestions: string;  // "새로운 기능?"

  // 순 추천자 점수 (NPS)
  npsScore: number;    // "다른 사람에게 추천하겠나?" (0~10)
}

const STEP_QUESTIONS = {
  1: {
    title: 'Go/No-Go 의사결정 피드백',
    questions: [
      '이 Step의 정보가 의사결정에 도움이 되었나?',
      '발주처 정보가 정확했나?',
      '경쟁 분석이 신뢰할 수 있었나?',
    ],
  },
  2: {
    title: '제안 전략 피드백',
    questions: [
      '포지셔닝이 명확했나?',
      '핵심 메시지가 실행 가능했나?',
      '가격 전략이 타당했나?',
    ],
  },
  3: {
    title: '계획 & 팀 구성 피드백',
    questions: [
      '팀 구성 추천이 적절했나?',
      '일정 계획이 현실적이었나?',
      '리소스 가용성 정보가 유용했나?',
    ],
  },
  4: {
    title: '제안서 작성 피드백',
    questions: [
      '입찰가 분석이 신뢰할 수 있었나?',
      '추천 입찰가가 타당했나?',
      '신뢰성 사례가 도움이 되었나?',
    ],
  },
  5: {
    title: '발표 전략 피드백',
    questions: [
      '발주처 성향 분석이 정확했나?',
      '발표 전략이 실행 가능했나?',
      '예상 Q&A가 도움이 되었나?',
    ],
  },
};

export const FeedbackForm: React.FC<FeedbackFormProps> = ({
  step,
  proposalId,
  onSubmit,
  onClose,
}) => {
  const [helpfulness, setHelpfulness] = useState<number>(0);
  const [accuracy, setAccuracy] = useState<number>(0);
  const [relevance, setRelevance] = useState<number>(0);
  const [wouldUse, setWouldUse] = useState<boolean | null>(null);
  const [npsScore, setNpsScore] = useState<number>(0);
  const [improvements, setImprovements] = useState<string>('');
  const [suggestions, setSuggestions] = useState<string>('');
  const [submitted, setSubmitted] = useState<boolean>(false);

  const stepInfo = STEP_QUESTIONS[step as keyof typeof STEP_QUESTIONS];

  const handleSubmit = async () => {
    const feedback: FeedbackData = {
      step,
      proposalId,
      timestamp: new Date(),
      helpfulness,
      accuracy,
      relevance,
      wouldUseInWork: wouldUse || false,
      npsScore,
      improvements,
      suggestions,
    };

    try {
      // Send to backend
      await fetch('/api/vault/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedback),
      });

      setSubmitted(true);
      onSubmit?.(feedback);

      // Auto-close after 3 seconds
      setTimeout(() => onClose?.(), 3000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('피드백 전송에 실패했습니다. 다시 시도해주세요.');
    }
  };

  if (submitted) {
    return (
      <Card className="w-full bg-green-50 border border-green-200">
        <CardContent className="pt-6 text-center">
          <ThumbsUp className="w-12 h-12 text-green-600 mx-auto mb-3" />
          <p className="text-lg font-semibold text-green-700 mb-1">
            피드백이 저장되었습니다!
          </p>
          <p className="text-sm text-green-600">
            귀중한 의견 감사합니다. 계속 개선하겠습니다.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="bg-blue-50">
        <div className="flex items-start justify-between">
          <div>
            <Badge className="mb-2">Step {step}</Badge>
            <CardTitle className="text-lg">{stepInfo.title}</CardTitle>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        {/* Satisfaction Scales */}
        <div className="space-y-4">
          <p className="font-semibold text-gray-900">만족도 평가 (1~10)</p>

          {/* Helpfulness */}
          <div className="space-y-2">
            <label className="text-sm text-gray-700">
              {stepInfo.questions[0]}
            </label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                <button
                  key={num}
                  onClick={() => setHelpfulness(num)}
                  className={`w-9 h-9 rounded border text-sm font-medium transition-colors ${
                    helpfulness === num
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-blue-300'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500">
              {helpfulness > 0 && (
                <>
                  {helpfulness <= 3 && '도움이 되지 않음'}
                  {helpfulness > 3 && helpfulness <= 6 && '보통'}
                  {helpfulness > 6 && '매우 도움됨'}
                </>
              )}
            </p>
          </div>

          {/* Accuracy */}
          <div className="space-y-2">
            <label className="text-sm text-gray-700">
              {stepInfo.questions[1]}
            </label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                <button
                  key={num}
                  onClick={() => setAccuracy(num)}
                  className={`w-9 h-9 rounded border text-sm font-medium transition-colors ${
                    accuracy === num
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-blue-300'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          {/* Relevance */}
          <div className="space-y-2">
            <label className="text-sm text-gray-700">
              {stepInfo.questions[2]}
            </label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                <button
                  key={num}
                  onClick={() => setRelevance(num)}
                  className={`w-9 h-9 rounded border text-sm font-medium transition-colors ${
                    relevance === num
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-blue-300'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Yes/No Question */}
        <div className="space-y-2 border-t pt-4">
          <label className="text-sm font-medium text-gray-900">
            이 Step을 실무에서 사용하겠나?
          </label>
          <div className="flex gap-3">
            <button
              onClick={() => setWouldUse(true)}
              className={`flex-1 py-2 px-3 rounded border font-medium transition-colors flex items-center justify-center gap-2 ${
                wouldUse === true
                  ? 'bg-green-100 text-green-700 border-green-300'
                  : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-green-300'
              }`}
            >
              <ThumbsUp className="w-4 h-4" />
              네
            </button>
            <button
              onClick={() => setWouldUse(false)}
              className={`flex-1 py-2 px-3 rounded border font-medium transition-colors flex items-center justify-center gap-2 ${
                wouldUse === false
                  ? 'bg-red-100 text-red-700 border-red-300'
                  : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-red-300'
              }`}
            >
              <ThumbsDown className="w-4 h-4" />
              아니오
            </button>
          </div>
        </div>

        {/* NPS Score */}
        <div className="space-y-2 border-t pt-4">
          <label className="text-sm font-medium text-gray-900">
            얼마나 다른 사람에게 추천하겠나? (0~10)
          </label>
          <p className="text-xs text-gray-600 mb-2">
            0 = 전혀 추천 안 함, 10 = 매우 추천함
          </p>
          <div className="flex gap-1">
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
              <button
                key={num}
                onClick={() => setNpsScore(num)}
                className={`flex-1 py-2 rounded border text-sm font-medium transition-colors ${
                  npsScore === num
                    ? 'bg-purple-600 text-white border-purple-600'
                    : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-purple-300'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Text Feedback */}
        <div className="space-y-3 border-t pt-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-900 flex items-center gap-2">
              <MessageCircle className="w-4 h-4" />
              개선할 점이 있다면?
            </label>
            <Textarea
              placeholder="예: 이 정보가 부족했어요... 또는 이 부분이 헷갈렸어요..."
              value={improvements}
              onChange={(e) => setImprovements(e.target.value)}
              className="min-h-20"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-900 flex items-center gap-2">
              <Star className="w-4 h-4" />
              새로운 기능이 필요하다면?
            </label>
            <Textarea
              placeholder="예: ~라는 기능이 있으면 좋겠어요..."
              value={suggestions}
              onChange={(e) => setSuggestions(e.target.value)}
              className="min-h-20"
            />
          </div>
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-3 pt-4 border-t">
          <button
            onClick={onClose}
            className="flex-1 py-2 px-4 rounded border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
          >
            건너뛰기
          </button>
          <button
            onClick={handleSubmit}
            disabled={helpfulness === 0 || accuracy === 0 || relevance === 0}
            className="flex-1 py-2 px-4 rounded bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            피드백 제출
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="text-xs text-center text-gray-500 pt-2">
          <p>
            {helpfulness > 0 && accuracy > 0 && relevance > 0
              ? '✓ 필수 항목 완료'
              : '(1~3번 항목은 필수입니다)'}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default FeedbackForm;
