/**
 * Vault AI Response Card
 * 제안 단계별 응답 표시 및 메타데이터 표시
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, Clock, FileText } from 'lucide-react';

interface Source {
  title: string;
  type: 'credential' | 'client' | 'bidding' | 'personnel' | 'internal';
  relevance: number; // 0-100
}

interface VaultResponseCardProps {
  step: number;
  title: string;
  content: React.ReactNode;
  sources?: Source[];
  confidence?: number; // 0-1
  lastUpdated?: Date;
  dataPoints?: number;
  children?: React.ReactNode;
}

const getConfidenceBadgeColor = (confidence: number): string => {
  if (confidence >= 0.85) return 'bg-green-100 text-green-800';
  if (confidence >= 0.70) return 'bg-yellow-100 text-yellow-800';
  return 'bg-red-100 text-red-800';
};

const getConfidenceIcon = (confidence: number) => {
  if (confidence >= 0.85) return <CheckCircle className="w-4 h-4" />;
  if (confidence >= 0.70) return <AlertCircle className="w-4 h-4" />;
  return <AlertCircle className="w-4 h-4" />;
};

const formatTimeAgo = (date: Date): string => {
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return '방금 전';
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}분 전`;
  }
  if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600);
    return `${hours}시간 전`;
  }

  const days = Math.floor(seconds / 86400);
  return `${days}일 전`;
};

const getSourceTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    credential: '자격증명',
    client: '클라이언트',
    bidding: '낙찰가',
    personnel: '인력',
    internal: '내부 데이터',
  };
  return labels[type] || type;
};

export const VaultResponseCard: React.FC<VaultResponseCardProps> = ({
  step,
  title,
  content,
  sources = [],
  confidence = 0.85,
  lastUpdated,
  dataPoints = 0,
  children,
}) => {
  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-gray-500">
                Step {step}
              </span>
              {dataPoints > 0 && (
                <span className="text-xs text-gray-400">
                  {dataPoints}개 데이터 기반
                </span>
              )}
            </div>
            <CardTitle className="text-lg">{title}</CardTitle>
          </div>

          {/* Confidence Badge */}
          {confidence !== undefined && (
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${getConfidenceBadgeColor(
                confidence
              )}`}
            >
              {getConfidenceIcon(confidence)}
              <span className="text-sm font-medium">
                {Math.round(confidence * 100)}%
              </span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Main Content */}
        <div className="space-y-3">{content}</div>

        {/* Metadata Section */}
        {(sources.length > 0 || lastUpdated) && (
          <div className="pt-3 border-t border-gray-200 space-y-3">
            {/* Last Updated */}
            {lastUpdated && (
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <Clock className="w-3 h-3" />
                <span>{formatTimeAgo(lastUpdated)} 업데이트됨</span>
              </div>
            )}

            {/* Sources */}
            {sources.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-medium text-gray-700">
                  <FileText className="w-3 h-3" />
                  <span>데이터 출처</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {sources.map((source, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className="text-xs py-0.5 px-2"
                      >
                        <span className="text-gray-600">
                          {getSourceTypeLabel(source.type)}
                        </span>
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {source.title}
                      </span>
                      {source.relevance > 0 && (
                        <span className="text-xs text-gray-400">
                          ({source.relevance}%)
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Additional Content (Step-specific) */}
        {children && <div className="pt-3">{children}</div>}
      </CardContent>
    </Card>
  );
};

export default VaultResponseCard;
