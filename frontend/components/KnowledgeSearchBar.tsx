'use client';

import { useState } from 'react';
import { Search, Filter, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface SearchResultItem {
  id: string;
  knowledge_type: 'capability' | 'client_intel' | 'market_price' | 'lesson_learned';
  confidence_score: number;
  freshness_score: number;
  source_doc: string;
  content_preview: string;
  created_at?: string;
}

interface SearchFiltersType {
  knowledge_types?: string[];
  freshness_min?: number;
}

interface KnowledgeSearchBarProps {
  onResultsChange?: (results: SearchResultItem[]) => void;
}

export function KnowledgeSearchBar({ onResultsChange }: KnowledgeSearchBarProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [freshnessMin, setFreshnessMin] = useState<number>(0);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const filters: SearchFiltersType = {};
      if (selectedTypes.length > 0) filters.knowledge_types = selectedTypes;
      if (freshnessMin > 0) filters.freshness_min = freshnessMin;

      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      const response = await fetch(`${baseUrl}/knowledge/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          limit: 10,
          offset: 0,
          filters: filters.knowledge_types || filters.freshness_min ? filters : undefined,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const json = await response.json();
      const searchResults = json?.items || [];
      setResults(searchResults);
      onResultsChange?.(searchResults);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setError(message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const typeLabels: Record<string, string> = {
    capability: '역량',
    client_intel: '발주기관',
    market_price: '시장가격',
    lesson_learned: '교훈',
  };

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  return (
    <div className="w-full space-y-4">
      {/* Search Input */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="조직 지식 검색 (예: IoT 플랫폼, 클라이언트 정보)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
        >
          <Search className="w-5 h-5" />
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium">타입:</span>
          {Object.entries(typeLabels).map(([type, label]) => (
            <button
              key={type}
              onClick={() => toggleType(type)}
              className={`px-3 py-1 rounded text-sm transition ${
                selectedTypes.includes(type)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">최소 신선도:</label>
          <input
            type="range"
            min="0"
            max="100"
            value={freshnessMin}
            onChange={(e) => setFreshnessMin(Number(e.target.value))}
            className="w-24"
          />
          <span className="text-sm text-gray-600">{freshnessMin}</span>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Results */}
      <div className="space-y-2">
        {loading ? (
          <p className="text-gray-600">검색 중...</p>
        ) : results.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600">{results.length}개 결과</p>
            {results.map((result) => (
              <div
                key={result.id}
                className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition"
              >
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{result.source_doc}</p>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                      {result.content_preview}
                    </p>
                    <div className="flex gap-2 mt-2 text-xs text-gray-500">
                      <span className="bg-gray-100 px-2 py-1 rounded">
                        {typeLabels[result.knowledge_type]}
                      </span>
                      <span>신선도: {result.freshness_score.toFixed(0)}</span>
                      <span>확신: {(result.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : query && !loading ? (
          <p className="text-gray-500 text-sm">결과가 없습니다.</p>
        ) : null}
      </div>
    </div>
  );
}
