'use client';

import { useState, useEffect } from 'react';
import { ThumbsUp, ThumbsDown, Loader } from 'lucide-react';
import { api } from '@/lib/api';

interface KnowledgeRecommendation {
  id: string;
  source_doc: string;
  content_preview: string;
  knowledge_type: 'capability' | 'client_intel' | 'market_price' | 'lesson_learned';
  relevance_reason: string;
  confidence_score: number;
  freshness_score: number;
}

interface KnowledgeRecommendationsProps {
  proposalContent: string;
  proposalContext?: {
    client?: string;
    project_type?: string;
    budget_range?: string;
  };
  onFeedback?: (recommendation_id: string, feedback: 'positive' | 'negative') => void;
}

export function KnowledgeRecommendations({
  proposalContent,
  proposalContext,
  onFeedback,
}: KnowledgeRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<KnowledgeRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, 'positive' | 'negative'>>({});

  useEffect(() => {
    if (!proposalContent || proposalContent.trim().length === 0) {
      setRecommendations([]);
      return;
    }

    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);

      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        const response = await fetch(`${baseUrl}/knowledge/recommend`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            proposal_context: {
              rfp_summary: proposalContent,
              ...(proposalContext || {}),
            },
            limit: 5,
          }),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const json = await response.json();
        const data = json?.items || [];
        setRecommendations(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch recommendations';
        setError(message);
        setRecommendations([]);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(fetchRecommendations, 1000);
    return () => clearTimeout(debounceTimer);
  }, [proposalContent, proposalContext]);

  const handleFeedback = async (recommendationId: string, feedback: 'positive' | 'negative') => {
    setFeedbackGiven((prev) => ({
      ...prev,
      [recommendationId]: feedback,
    }));

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      await fetch(`${baseUrl}/knowledge/${recommendationId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feedback_type: feedback,
          proposal_context: proposalContext,
        }),
      });
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }

    onFeedback?.(recommendationId, feedback);
  };

  const typeLabels: Record<string, string> = {
    capability: '역량',
    client_intel: '발주기관',
    market_price: '시장가격',
    lesson_learned: '교훈',
  };

  return (
    <div className="w-full max-w-xs space-y-4 p-4 bg-gradient-to-b from-blue-50 to-white rounded-lg border border-blue-100">
      <div className="space-y-1">
        <h3 className="font-semibold text-gray-800">추천 지식</h3>
        <p className="text-xs text-gray-500">제안서 작성에 도움이 될 만한 지식</p>
      </div>

      {error && (
        <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex gap-2 items-center justify-center py-8 text-gray-400">
          <Loader className="w-4 h-4 animate-spin" />
          <span className="text-xs">추천 검색 중...</span>
        </div>
      )}

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {recommendations.length > 0 ? (
          recommendations.map((rec) => (
            <div
              key={rec.id}
              className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition space-y-2"
            >
              <div className="space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-medium bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    {typeLabels[rec.knowledge_type]}
                  </span>
                  <span className="text-xs text-gray-500">
                    신선도: {rec.freshness_score.toFixed(0)}
                  </span>
                </div>
                <p className="text-xs font-medium text-gray-700">{rec.source_doc}</p>
                <p className="text-xs text-gray-600 line-clamp-2">{rec.content_preview}</p>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-gray-500 italic">{rec.relevance_reason}</p>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-gray-500">확신: {(rec.confidence_score * 100).toFixed(0)}%</span>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleFeedback(rec.id, 'positive')}
                      disabled={feedbackGiven[rec.id] !== undefined}
                      className={`p-1 rounded transition ${
                        feedbackGiven[rec.id] === 'positive'
                          ? 'bg-green-100 text-green-600'
                          : 'hover:bg-gray-100 text-gray-400'
                      }`}
                      title="유용함"
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleFeedback(rec.id, 'negative')}
                      disabled={feedbackGiven[rec.id] !== undefined}
                      className={`p-1 rounded transition ${
                        feedbackGiven[rec.id] === 'negative'
                          ? 'bg-red-100 text-red-600'
                          : 'hover:bg-gray-100 text-gray-400'
                      }`}
                      title="부정확함"
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : !loading && !error && proposalContent ? (
          <p className="text-xs text-gray-500 text-center py-4">추천할 지식이 없습니다.</p>
        ) : !loading && !error ? (
          <p className="text-xs text-gray-400 text-center py-4">제안서를 작성하면 추천 지식이 나타납니다.</p>
        ) : null}
      </div>
    </div>
  );
}
