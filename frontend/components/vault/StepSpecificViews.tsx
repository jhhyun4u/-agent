/**
 * Vault Step-Specific Response Views
 * 제안 단계별 맞춤형 응답 레이아웃
 */

import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

// Step 1: Go/No-Go
interface ClientInfo {
  name: string;
  type: string;
  budget: number;
  industry: string;
  frequency: string;
}

interface CompetitiveAnalysis {
  competitorName: string;
  marketShare: number;
  winRate: number;
  strength: string[];
  weakness: string[];
}

export const Step1GoNoGoView: React.FC<{
  clientInfo: ClientInfo;
  competitors: CompetitiveAnalysis[];
  winProbability: number;
  recommendation: string;
}> = ({ clientInfo, competitors, winProbability, recommendation }) => (
  <div className="space-y-4">
    {/* Client Info */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">발주처 정보</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-xs text-gray-500">기관명</span>
            <p className="font-medium">{clientInfo.name}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500">유형</span>
            <p className="font-medium">{clientInfo.type}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500">산업</span>
            <p className="font-medium">{clientInfo.industry}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500">예산</span>
            <p className="font-medium">{(clientInfo.budget / 100000000).toFixed(1)}억원</p>
          </div>
        </div>
      </CardContent>
    </Card>

    {/* Competitive Landscape */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">경쟁 현황</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {competitors.map((comp, idx) => (
          <div key={idx} className="border-b pb-3 last:border-0">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-sm">{comp.competitorName}</span>
              <Badge variant="outline">
                시장점유율 {comp.marketShare}%
              </Badge>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-500">낙찰률:</span>
                <span className="ml-2 font-medium">{comp.winRate}%</span>
              </div>
              <div className="text-green-600">
                강점: {comp.strength.slice(0, 1).join(', ')}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>

    {/* Win Probability */}
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <TrendingUp className="w-4 h-4 text-blue-600" />
        <span className="font-medium text-sm">낙찰 확률 분석</span>
      </div>
      <p className="text-2xl font-bold text-blue-600 mb-2">
        {Math.round(winProbability * 100)}%
      </p>
      <p className="text-xs text-gray-700">{recommendation}</p>
    </div>
  </div>
);

// Step 2: Strategy
interface StrategyPoint {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

interface PricingStrategy {
  recommended: number;
  range: [number, number];
  competitive: number;
}

export const Step2StrategyView: React.FC<{
  positioning: string;
  keyMessages: StrategyPoint[];
  pricing: PricingStrategy;
  clientPreferences: string[];
}> = ({ positioning, keyMessages, pricing, clientPreferences }) => (
  <div className="space-y-4">
    {/* Positioning */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">포지셔닝</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="bg-gray-50 rounded p-3">
          <p className="text-sm text-gray-700">{positioning}</p>
        </div>
      </CardContent>
    </Card>

    {/* Key Messages */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">핵심 메시지</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {keyMessages.map((msg, idx) => (
          <div key={idx} className="flex gap-2">
            {msg.priority === 'high' && (
              <div className="w-1 bg-red-500 rounded-full flex-shrink-0" />
            )}
            {msg.priority === 'medium' && (
              <div className="w-1 bg-yellow-500 rounded-full flex-shrink-0" />
            )}
            {msg.priority === 'low' && (
              <div className="w-1 bg-blue-500 rounded-full flex-shrink-0" />
            )}
            <div className="flex-1">
              <p className="font-medium text-sm">{msg.title}</p>
              <p className="text-xs text-gray-600">{msg.description}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>

    {/* Pricing Strategy */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">가격 전략</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-3 gap-3 text-center text-sm">
          <div className="bg-gray-50 rounded p-2">
            <span className="text-xs text-gray-500">최소</span>
            <p className="font-bold text-gray-700">
              {(pricing.range[0] / 100000000).toFixed(1)}억
            </p>
          </div>
          <div className="bg-green-50 rounded p-2">
            <span className="text-xs text-gray-500">추천</span>
            <p className="font-bold text-green-700">
              {(pricing.recommended / 100000000).toFixed(1)}억
            </p>
          </div>
          <div className="bg-gray-50 rounded p-2">
            <span className="text-xs text-gray-500">최대</span>
            <p className="font-bold text-gray-700">
              {(pricing.range[1] / 100000000).toFixed(1)}억
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    {/* Client Preferences */}
    {clientPreferences.length > 0 && (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">발주처 선호도</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {clientPreferences.map((pref, idx) => (
            <Badge key={idx} variant="secondary">
              {pref}
            </Badge>
          ))}
        </CardContent>
      </Card>
    )}
  </div>
);

// Step 3: Planning
interface PersonnelRecommendation {
  name: string;
  role: string;
  expertise: string[];
  experience: number;
  available: boolean;
}

export const Step3PlanningView: React.FC<{
  team: PersonnelRecommendation[];
  schedule: Array<{ phase: string; duration: string; start: string }>;
  availability: number;
}> = ({ team, schedule, availability }) => (
  <div className="space-y-4">
    {/* Team Composition */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Users className="w-4 h-4" />
          추천 팀 구성
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {team.map((member, idx) => (
          <div
            key={idx}
            className={`border rounded p-3 ${
              member.available ? 'bg-green-50' : 'bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-medium">{member.name}</p>
                <p className="text-sm text-gray-600">{member.role}</p>
              </div>
              {member.available ? (
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
              )}
            </div>
            <div className="flex flex-wrap gap-1">
              {member.expertise.map((skill, i) => (
                <Badge key={i} variant="outline" className="text-xs py-0">
                  {skill}
                </Badge>
              ))}
            </div>
            <p className="text-xs text-gray-600 mt-2">
              경력: {member.experience}년
            </p>
          </div>
        ))}
      </CardContent>
    </Card>

    {/* Project Schedule */}
    {schedule.length > 0 && (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">프로젝트 일정</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {schedule.map((item, idx) => (
            <div key={idx} className="flex justify-between items-center text-sm">
              <span className="font-medium">{item.phase}</span>
              <span className="text-gray-600">{item.duration}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    )}

    {/* Resource Availability */}
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
      <p className="text-xs text-gray-600 mb-1">리소스 가용성</p>
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-blue-200 rounded-full h-2">
          <div
            className="bg-blue-600 rounded-full h-2 transition-all"
            style={{ width: `${availability}%` }}
          />
        </div>
        <span className="text-sm font-bold text-blue-600">{availability}%</span>
      </div>
    </div>
  </div>
);

// Step 4: Proposal Writing
interface BidPriceData {
  month: string;
  recommended: number;
  competitive: number;
  maximum: number;
}

export const Step4ProposalView: React.FC<{
  bidRange: BidPriceData[];
  recommendedBid: number;
  winProbability: number;
  pricePosition: string;
  caseReferences: Array<{ title: string; relevance: number }>;
}> = ({ bidRange, recommendedBid, winProbability, pricePosition, caseReferences }) => (
  <div className="space-y-4">
    {/* Bid Price Chart */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">입찰가 분석</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={bidRange}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="recommended"
              stroke="#10b981"
              name="추천 입찰가"
            />
            <Line
              type="monotone"
              dataKey="competitive"
              stroke="#3b82f6"
              name="경쟁 입찰가"
            />
            <Line
              type="monotone"
              dataKey="maximum"
              stroke="#ef4444"
              name="최대 입찰가"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>

    {/* Recommended Bid */}
    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-gray-600 mb-1">추천 입찰가</p>
          <p className="text-3xl font-bold text-green-700">
            {(recommendedBid / 100000000).toFixed(1)}억원
          </p>
          <p className="text-xs text-gray-600 mt-2">
            가격 포지셔닝: <span className="font-medium">{pricePosition}</span>
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-600">예상 낙찰률</p>
          <p className="text-2xl font-bold text-green-600">
            {Math.round(winProbability * 100)}%
          </p>
        </div>
      </div>
    </div>

    {/* Case References */}
    {caseReferences.length > 0 && (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">신뢰성 사례</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {caseReferences.map((caseRef, idx) => (
            <div key={idx} className="flex justify-between items-start text-sm">
              <span className="text-gray-700">{caseRef.title}</span>
              <span className="text-gray-500">
                관련도 {caseRef.relevance}%
              </span>
            </div>
          ))}
        </CardContent>
      </Card>
    )}
  </div>
);

// Step 5: Presentation Strategy
interface PredictedQA {
  question: string;
  expectedAnswer: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

export const Step5PresentationView: React.FC<{
  clientPersonality: string[];
  pressurePoints: string[];
  predictedQuestions: PredictedQA[];
  presentationStrategy: string;
}> = ({ clientPersonality, pressurePoints, predictedQuestions, presentationStrategy }) => (
  <div className="space-y-4">
    {/* Client Personality */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">발주처 성향</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex flex-wrap gap-2">
          {clientPersonality.map((trait, idx) => (
            <Badge key={idx} variant="outline">
              {trait}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>

    {/* Presentation Strategy */}
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">발표 전략</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="bg-gray-50 rounded p-3">
          <p className="text-sm text-gray-700">{presentationStrategy}</p>
        </div>
      </CardContent>
    </Card>

    {/* Pressure Points */}
    {pressurePoints.length > 0 && (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">유의 포인트</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {pressurePoints.map((point, idx) => (
            <div key={idx} className="flex gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-gray-700">{point}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    )}

    {/* Predicted Q&A */}
    {predictedQuestions.length > 0 && (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">예상 질문 & 답변</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {predictedQuestions.map((qa, idx) => (
            <div key={idx} className="border-b pb-3 last:border-0">
              <div className="flex items-start justify-between mb-2">
                <p className="font-medium text-sm flex-1">{qa.question}</p>
                <Badge
                  variant="outline"
                  className={
                    qa.difficulty === 'hard'
                      ? 'text-red-600'
                      : qa.difficulty === 'medium'
                        ? 'text-yellow-600'
                        : 'text-green-600'
                  }
                >
                  {qa.difficulty === 'hard'
                    ? '어려움'
                    : qa.difficulty === 'medium'
                      ? '중간'
                      : '쉬움'}
                </Badge>
              </div>
              <p className="text-xs text-gray-600">{qa.expectedAnswer}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    )}
  </div>
);
