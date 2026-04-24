"""
쿼리 성능 분석 및 최적화 제안 모듈

프로덕션 데이터베이스 쿼리 패턴을 분석하여:
1. 자주 호출되는 쿼리 식별
2. 느린 쿼리 감지
3. 누락된 인덱스 추천
4. 캐시 전략 제안
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    """쿼리 성능 통계"""
    query_type: str  # 'search', 'select', 'insert', 'update', 'delete'
    table_name: str
    execution_count: int
    total_time_ms: float
    min_time_ms: float
    max_time_ms: float
    avg_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    error_count: int
    
    @property
    def throughput_per_sec(self) -> float:
        """초당 처리량"""
        return self.execution_count / max(self.total_time_ms / 1000, 0.001)
    
    @property
    def error_rate(self) -> float:
        """에러율 (0.0 ~ 1.0)"""
        total = self.execution_count + self.error_count
        return self.error_count / total if total > 0 else 0.0
    
    @property
    def slow_query_ratio(self) -> float:
        """느린 쿼리 비율 (P95 이상)"""
        # 실제로는 추적 데이터 필요
        return 0.1


@dataclass
class IndexRecommendation:
    """인덱스 추천"""
    table_name: str
    columns: List[str]  # 인덱스할 컬럼들
    reason: str
    estimated_improvement_percent: int  # 예상 개선율
    frequency_score: float  # 0.0 ~ 1.0
    
    @property
    def priority(self) -> str:
        """추천 우선순위"""
        if self.frequency_score >= 0.8:
            return "critical"
        elif self.frequency_score >= 0.6:
            return "high"
        elif self.frequency_score >= 0.4:
            return "medium"
        else:
            return "low"


class QueryAnalyzer:
    """
    데이터베이스 쿼리 성능 분석기
    
    Prometheus 메트릭과 데이터베이스 통계를 결합하여
    최적화 기회를 식별합니다.
    """
    
    def __init__(self):
        self.query_stats: Dict[str, QueryStats] = {}
        self.last_analysis: Optional[datetime] = None
        self.index_recommendations: List[IndexRecommendation] = []
    
    async def collect_query_metrics(self, client) -> Dict[str, QueryStats]:
        """
        Supabase에서 쿼리 통계 수집
        
        pg_stat_statements 뷰를 사용하여 실제 쿼리 성능 데이터 수집
        """
        try:
            # PostgreSQL의 pg_stat_statements 확장 활용
            # (실제로는 pg_stat_statements 활성화 필요)
            query_stats_data = await client.rpc(
                "get_query_statistics"
            ).execute()
            
            if not query_stats_data.data:
                logger.warning("쿼리 통계 데이터 없음 - pg_stat_statements 확인 필요")
                return {}
            
            # 통계 데이터를 QueryStats 객체로 변환
            stats = {}
            for row in query_stats_data.data:
                key = f"{row['query_type']}_{row['table_name']}"
                stats[key] = QueryStats(
                    query_type=row['query_type'],
                    table_name=row['table_name'],
                    execution_count=row['calls'],
                    total_time_ms=row['total_time'],
                    min_time_ms=row['min_time'],
                    max_time_ms=row['max_time'],
                    avg_time_ms=row['mean_time'],
                    p95_time_ms=row['p95_time'],
                    p99_time_ms=row['p99_time'],
                    error_count=row.get('error_count', 0),
                )
            
            self.query_stats = stats
            self.last_analysis = datetime.now()
            logger.info(f"쿼리 통계 수집 완료: {len(stats)}개 쿼리")
            
            return stats
        except Exception as e:
            logger.error(f"쿼리 통계 수집 실패: {e}")
            return {}
    
    def identify_slow_queries(
        self,
        p95_threshold_ms: float = 100.0,
        execution_threshold: int = 10,
    ) -> List[QueryStats]:
        """
        느린 쿼리 식별
        
        Args:
            p95_threshold_ms: P95 응답 시간 임계값 (ms)
            execution_threshold: 최소 실행 횟수
            
        Returns:
            느린 쿼리 통계 리스트 (심각도 순)
        """
        slow_queries = [
            qs for qs in self.query_stats.values()
            if qs.p95_time_ms > p95_threshold_ms
            and qs.execution_count >= execution_threshold
        ]
        
        # 영향도 순으로 정렬 (실행 횟수 × P95 시간)
        slow_queries.sort(
            key=lambda q: q.execution_count * q.p95_time_ms,
            reverse=True
        )
        
        return slow_queries
    
    def identify_frequent_queries(
        self,
        execution_threshold: int = 100,
    ) -> List[QueryStats]:
        """
        자주 실행되는 쿼리 식별
        
        Args:
            execution_threshold: 최소 실행 횟수
            
        Returns:
            실행 횟수 순 쿼리 통계 리스트
        """
        frequent_queries = [
            qs for qs in self.query_stats.values()
            if qs.execution_count >= execution_threshold
        ]
        
        # 실행 횟수 순으로 정렬
        frequent_queries.sort(
            key=lambda q: q.execution_count,
            reverse=True
        )
        
        return frequent_queries
    
    def recommend_indexes(self) -> List[IndexRecommendation]:
        """
        인덱스 추천
        
        느린 쿼리와 자주 실행되는 쿼리 분석을 통해
        도움이 될 인덱스 추천
        
        Returns:
            인덱스 추천 리스트 (우선순위 순)
        """
        recommendations = []
        
        # 느린 SELECT 쿼리 분석
        slow_selects = [
            q for q in self.identify_slow_queries()
            if q.query_type == 'select'
        ]
        
        for query in slow_selects[:5]:  # 상위 5개
            # 테이블별 인덱스 추천
            if query.table_name == 'proposals':
                # proposals 테이블의 일반적인 쿼리 패턴
                if query.avg_time_ms > 50:  # 평균 50ms 이상
                    recommendations.append(IndexRecommendation(
                        table_name='proposals',
                        columns=['user_id', 'status', 'created_at'],
                        reason=f"빈번한 필터링 쿼리 (P95: {query.p95_time_ms:.1f}ms)",
                        estimated_improvement_percent=30,
                        frequency_score=min(query.execution_count / 1000, 1.0),
                    ))
            
            elif query.table_name == 'documents':
                if query.avg_time_ms > 100:
                    recommendations.append(IndexRecommendation(
                        table_name='documents',
                        columns=['proposal_id', 'doc_type', 'created_at'],
                        reason=f"느린 조인 쿼리 (P95: {query.p95_time_ms:.1f}ms)",
                        estimated_improvement_percent=40,
                        frequency_score=min(query.execution_count / 500, 1.0),
                    ))
            
            elif query.table_name == 'proposal_sections':
                if query.avg_time_ms > 50:
                    recommendations.append(IndexRecommendation(
                        table_name='proposal_sections',
                        columns=['proposal_id', 'section_type'],
                        reason=f"섹션별 조회 최적화 (P95: {query.p95_time_ms:.1f}ms)",
                        estimated_improvement_percent=35,
                        frequency_score=min(query.execution_count / 800, 1.0),
                    ))
        
        # 자주 실행되는 쿼리 분석
        frequent = self.identify_frequent_queries()
        for query in frequent[:5]:
            if query.query_type == 'select' and query.p95_time_ms > 50:
                recommendations.append(IndexRecommendation(
                    table_name=query.table_name,
                    columns=['id', 'created_at'],  # 기본 추천
                    reason=f"고빈도 조회 최적화 ({query.execution_count}회)",
                    estimated_improvement_percent=25,
                    frequency_score=min(query.execution_count / 1000, 1.0),
                ))
        
        # 우선순위 순으로 정렬
        recommendations.sort(
            key=lambda r: (r.priority != 'critical',
                          r.priority != 'high',
                          r.frequency_score),
            reverse=True
        )
        
        self.index_recommendations = recommendations
        return recommendations
    
    def analyze_cache_hit_rate(
        self,
        cache_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        캐시 히트율 분석 및 TTL 최적화 제안
        
        Args:
            cache_stats: {cache_type: {hit_rate, items, size_mb}}
            
        Returns:
            {cache_type: {current_ttl, recommended_ttl, reason}}
        """
        ttl_recommendations = {}
        
        # 기본 TTL 설정 (초)
        default_ttl = {
            'kb_search': 600,      # 10분
            'proposals': 300,      # 5분
            'analytics': 900,      # 15분
            'search_results': 600, # 10분
        }
        
        for cache_type, stats in cache_stats.items():
            hit_rate = stats.get('hit_rate', 0)
            items_count = stats.get('items', 0)
            
            # TTL 조정 로직
            current_ttl = default_ttl.get(cache_type, 600)
            recommended_ttl = current_ttl
            reason = "최적 상태"
            
            if hit_rate < 0.80:  # 히트율 80% 미만
                # TTL 연장 (더 오래 캐시 유지)
                recommended_ttl = int(current_ttl * 1.5)
                reason = f"히트율 {hit_rate:.1%} < 80% → TTL 연장"
            
            elif hit_rate >= 0.95:  # 히트율 95% 이상
                # TTL 단축 가능 (메모리 효율)
                if items_count > 100:
                    recommended_ttl = max(int(current_ttl * 0.8), 60)
                    reason = f"히트율 {hit_rate:.1%}, 항목 {items_count}개 → TTL 단축"
            
            # 메모리 사용량 기반 조정
            size_mb = stats.get('size_mb', 0)
            if size_mb > 100:  # 100MB 이상
                recommended_ttl = int(recommended_ttl * 0.9)
                reason += f" (메모리 {size_mb}MB 관리)"
            
            ttl_recommendations[cache_type] = {
                'current_ttl_seconds': current_ttl,
                'recommended_ttl_seconds': recommended_ttl,
                'reason': reason,
                'hit_rate': hit_rate,
                'items_count': items_count,
            }
        
        return ttl_recommendations
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """
        전체 최적화 분석 보고서 생성
        
        Returns:
            {
                'slow_queries': [...],
                'frequent_queries': [...],
                'index_recommendations': [...],
                'analysis_time': datetime,
            }
        """
        slow_queries = self.identify_slow_queries()
        frequent_queries = self.identify_frequent_queries()
        index_recs = self.recommend_indexes()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'slow_queries': [
                {
                    'table': q.table_name,
                    'type': q.query_type,
                    'count': q.execution_count,
                    'p95_ms': q.p95_time_ms,
                    'avg_ms': q.avg_time_ms,
                }
                for q in slow_queries[:10]
            ],
            'frequent_queries': [
                {
                    'table': q.table_name,
                    'type': q.query_type,
                    'count': q.execution_count,
                    'avg_ms': q.avg_time_ms,
                }
                for q in frequent_queries[:10]
            ],
            'index_recommendations': [
                {
                    'table': r.table_name,
                    'columns': r.columns,
                    'reason': r.reason,
                    'improvement': f"{r.estimated_improvement_percent}%",
                    'priority': r.priority,
                }
                for r in index_recs
            ],
            'total_queries_analyzed': len(self.query_stats),
            'analysis_completed_at': self.last_analysis.isoformat() if self.last_analysis else None,
        }


# 글로벌 분석기 인스턴스
_query_analyzer: Optional[QueryAnalyzer] = None


async def get_query_analyzer() -> QueryAnalyzer:
    """쿼리 분석기 싱글톤 인스턴스 획득"""
    global _query_analyzer
    if _query_analyzer is None:
        _query_analyzer = QueryAnalyzer()
    return _query_analyzer
