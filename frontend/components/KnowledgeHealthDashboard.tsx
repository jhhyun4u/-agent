'use client';

import { useEffect, useState } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Database, RefreshCw, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api';

interface HealthMetrics {
  kb_size_chunks: number;
  kb_size_bytes: number;
  coverage_percentage: number;
  avg_freshness_score: number;
  total_organizations: number;
  total_shares: number;
  deprecation_rate: number;
  knowledge_type_distribution: Record<string, number>;
  confidence_distribution: {
    high: number;
    medium: number;
    low: number;
  };
  trending_topics: Array<{
    topic: string;
    occurrences: number;
  }>;
}

interface KnowledgeHealthDashboardProps {
  refreshInterval?: number;
}

export function KnowledgeHealthDashboard({ refreshInterval = 300000 }: KnowledgeHealthDashboardProps) {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      const response = await fetch(`${baseUrl}/knowledge/health`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setMetrics(data);
      setLastRefresh(new Date());
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch health metrics';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();

    const timer = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(timer);
  }, [refreshInterval]);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 10) / 10 + ' ' + sizes[i];
  };

  const typeLabels: Record<string, string> = {
    capability: '역량',
    client_intel: '발주기관',
    market_price: '시장가격',
    lesson_learned: '교훈',
  };

  const knowledgeTypeData = metrics
    ? Object.entries(metrics.knowledge_type_distribution).map(([type, count]) => ({
        name: typeLabels[type] || type,
        value: count,
      }))
    : [];

  const confidenceData = metrics
    ? [
        { name: '높음', value: metrics.confidence_distribution.high },
        { name: '중간', value: metrics.confidence_distribution.medium },
        { name: '낮음', value: metrics.confidence_distribution.low },
      ]
    : [];

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-4">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto" />
          <p className="text-gray-600">지식 기반 건강도 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg space-y-3">
        <div className="flex gap-2 items-start">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">오류 발생</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchMetrics}
          className="text-sm px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
        >
          다시 시도
        </button>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-gray-900">지식 기반 건강도</h2>
          <p className="text-sm text-gray-500">
            마지막 갱신: {lastRefresh ? lastRefresh.toLocaleTimeString('ko-KR') : '-'}
          </p>
        </div>
        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex gap-2 items-center"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          새로고침
        </button>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">청크 수</p>
            <Database className="w-5 h-5 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.kb_size_chunks.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-1">{formatBytes(metrics.kb_size_bytes)}</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">커버리지</p>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.coverage_percentage.toFixed(1)}%</p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div
              className="bg-green-500 h-2 rounded-full"
              style={{ width: `${Math.min(metrics.coverage_percentage, 100)}%` }}
            />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">평균 신선도</p>
            <RefreshCw className="w-5 h-5 text-orange-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.avg_freshness_score.toFixed(1)}</p>
          <p className="text-xs text-gray-500 mt-1">0-100 점</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">조직 공유율</p>
            <TrendingUp className="w-5 h-5 text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.total_shares.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-1">{metrics.total_organizations} 조직</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Knowledge Type Distribution */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">지식 유형 분포</h3>
          {knowledgeTypeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={knowledgeTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {knowledgeTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 py-8">데이터 없음</p>
          )}
        </div>

        {/* Confidence Distribution */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">확신도 분포</h3>
          {confidenceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={confidenceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" name="개수" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 py-8">데이터 없음</p>
          )}
        </div>
      </div>

      {/* Trending Topics */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">인기 주제</h3>
        {metrics.trending_topics.length > 0 ? (
          <div className="space-y-2">
            {metrics.trending_topics.slice(0, 10).map((topic, index) => (
              <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                <span className="text-sm font-medium text-gray-700">{index + 1}. {topic.topic}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{
                        width: `${(topic.occurrences / Math.max(...metrics.trending_topics.map(t => t.occurrences), 1)) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-12 text-right">{topic.occurrences}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-gray-500 py-8">데이터 없음</p>
        )}
      </div>

      {/* Health Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <p className="text-sm font-semibold text-green-900">신선도 지수</p>
          <p className="text-3xl font-bold text-green-700 mt-2">
            {metrics.avg_freshness_score > 75 ? '좋음' : metrics.avg_freshness_score > 50 ? '중간' : '낮음'}
          </p>
          <p className="text-xs text-green-700 mt-1">
            {metrics.avg_freshness_score > 75 ? '지식이 최신 상태입니다' : '오래된 지식을 갱신하세요'}
          </p>
        </div>

        <div
          className={`p-4 rounded-lg border ${
            metrics.deprecation_rate < 5
              ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200'
              : 'bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200'
          }`}
        >
          <p className={`text-sm font-semibold ${metrics.deprecation_rate < 5 ? 'text-blue-900' : 'text-yellow-900'}`}>
            폐기율
          </p>
          <p className={`text-3xl font-bold mt-2 ${metrics.deprecation_rate < 5 ? 'text-blue-700' : 'text-yellow-700'}`}>
            {metrics.deprecation_rate.toFixed(2)}%
          </p>
          <p className={`text-xs mt-1 ${metrics.deprecation_rate < 5 ? 'text-blue-700' : 'text-yellow-700'}`}>
            {metrics.deprecation_rate < 5 ? '건강한 수준입니다' : '폐기 지식이 많습니다'}
          </p>
        </div>
      </div>
    </div>
  );
}
