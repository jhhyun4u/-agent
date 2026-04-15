import { Metadata } from 'next';
import { KnowledgeHealthDashboard } from '@/components/KnowledgeHealthDashboard';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export const metadata: Metadata = {
  title: '지식 기반 건강도',
  description: '지식 기반의 규모, 신선도, 신뢰도 현황',
};

export default function HealthPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header with Back Button */}
        <div className="mb-8 flex items-center gap-4">
          <Link
            href="/knowledge"
            className="flex items-center gap-2 text-blue-600 hover:text-blue-700"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>지식 기반으로 돌아가기</span>
          </Link>
        </div>

        {/* Dashboard */}
        <KnowledgeHealthDashboard refreshInterval={300000} />
      </div>
    </div>
  );
}
