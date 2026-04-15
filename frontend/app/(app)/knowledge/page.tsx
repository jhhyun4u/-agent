import { Metadata } from 'next';
import { KnowledgeSearchBar } from '@/components/KnowledgeSearchBar';
import { Link } from 'lucide-react';

export const metadata: Metadata = {
  title: '지식 기반',
  description: '조직 지식 검색 및 관리',
};

export default function KnowledgePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">지식 기반</h1>
          <p className="text-lg text-gray-600">조직이 축적한 역량, 발주기관, 시장 정보, 교훈을 검색하세요</p>
        </div>

        {/* Search Component */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <KnowledgeSearchBar />
        </div>

        {/* Info Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">역량</h3>
            <p className="text-sm text-gray-600">
              조직이 보유한 기술 능력, 인프라, 인력 역량에 관한 정보
            </p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">발주기관</h3>
            <p className="text-sm text-gray-600">
              과거 발주기관 정보, 입찰 이력, 의사결정 특성 등
            </p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">시장 가격</h3>
            <p className="text-sm text-gray-600">
              유사 과제 낙찰가, 시장 시세, 경쟁 가격 정보
            </p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">교훈</h3>
            <p className="text-sm text-gray-600">
              과거 프로젝트에서 배운 성공 및 실패 사례
            </p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 md:col-span-2">
            <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <Link className="w-4 h-4" />
              제안서 작성 중 활용
            </h3>
            <p className="text-sm text-gray-600">
              제안서 작성 중 오른쪽 사이드바에서 추천 지식을 확인할 수 있습니다. 추천 지식에 대한 피드백(유용함/부정확함)을 제공하면 다음 제안에서 더 정확한 추천을 받을 수 있습니다.
            </p>
          </div>
        </div>

        {/* Health Link */}
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold text-blue-900">지식 기반 건강도</h3>
              <p className="text-sm text-blue-700">
                지식 기반의 규모, 신선도, 신뢰도를 모니터링하세요
              </p>
            </div>
            <a
              href="/knowledge/health"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium whitespace-nowrap"
            >
              보기
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
