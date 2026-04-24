"""
캐시 TTL 동적 조정 모듈

캐시 히트율과 메모리 사용량을 모니터링하여
최적의 TTL(Time-To-Live) 값을 자동으로 조정합니다.

히트율 기반 조정:
- 히트율 < 80%: TTL 연장 (캐시 더 오래 유지)
- 히트율 >= 90%: TTL 유지 (최적 상태)
- 히트율 > 95%: TTL 단축 가능 (메모리 절약)

메모리 기반 조정:
- 메모리 사용량 > 100MB: TTL 단축
- 메모리 사용량 < 50MB: TTL 연장 가능
"""

import logging
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheTTLMetrics:
    """캐시 TTL 메트릭"""
    cache_type: str
    current_ttl_seconds: int
    hit_rate: float
    hit_count: int
    miss_count: int
    size_bytes: int
    item_count: int
    last_updated: datetime
    
    @property
    def total_requests(self) -> int:
        return self.hit_count + self.miss_count
    
    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)
    
    @property
    def avg_item_size_bytes(self) -> float:
        return self.size_bytes / max(self.item_count, 1)


class CacheTTLOptimizer:
    """
    캐시 TTL 동적 조정기
    
    메트릭을 기반으로 캐시 TTL을 자동으로 최적화합니다.
    """
    
    def __init__(self):
        # 기본 TTL (초)
        self.default_ttls = {
            'kb_search': 600,      # 10분
            'proposals': 300,      # 5분
            'analytics': 900,      # 15분
            'search_results': 600, # 10분
        }
        
        # 현재 TTL
        self.current_ttls = self.default_ttls.copy()
        
        # TTL 변경 이력
        self.ttl_history: Dict[str, list] = {
            cache_type: [] for cache_type in self.default_ttls.keys()
        }
        
        # 마지막 조정 시간
        self.last_optimization: Optional[datetime] = None
        
        # 조정 주기 (초)
        self.optimization_interval = 300  # 5분
    
    async def analyze_and_optimize(
        self,
        metrics: Dict[str, CacheTTLMetrics],
    ) -> Dict[str, Dict[str, any]]:
        """
        메트릭을 분석하고 TTL 최적화 수행
        
        Args:
            metrics: {cache_type: CacheTTLMetrics}
            
        Returns:
            {cache_type: {old_ttl, new_ttl, reason}}
        """
        optimizations = {}
        
        for cache_type, metric in metrics.items():
            old_ttl = self.current_ttls.get(cache_type, 600)
            new_ttl, reason = self._calculate_optimal_ttl(metric)
            
            if new_ttl != old_ttl:
                self.current_ttls[cache_type] = new_ttl
                
                # 이력 기록
                self.ttl_history[cache_type].append({
                    'timestamp': datetime.now().isoformat(),
                    'old_ttl': old_ttl,
                    'new_ttl': new_ttl,
                    'reason': reason,
                    'hit_rate': metric.hit_rate,
                    'size_mb': metric.size_mb,
                })
                
                logger.info(
                    f"TTL 조정: {cache_type} "
                    f"{old_ttl}s → {new_ttl}s "
                    f"(히트율: {metric.hit_rate:.1%}, 크기: {metric.size_mb:.1f}MB)"
                )
                
                optimizations[cache_type] = {
                    'old_ttl_seconds': old_ttl,
                    'new_ttl_seconds': new_ttl,
                    'reason': reason,
                    'hit_rate': metric.hit_rate,
                    'size_mb': metric.size_mb,
                }
        
        self.last_optimization = datetime.now()
        return optimizations
    
    def _calculate_optimal_ttl(
        self,
        metric: CacheTTLMetrics,
    ) -> Tuple[int, str]:
        """
        최적 TTL 계산
        
        Args:
            metric: 캐시 메트릭
            
        Returns:
            (새로운_TTL초, 사유)
        """
        current_ttl = metric.current_ttl_seconds
        base_ttl = self.default_ttls.get(metric.cache_type, 600)
        
        # 최소/최대 TTL 제약
        min_ttl = 60      # 최소 1분
        max_ttl = 3600    # 최대 1시간
        
        # 1. 히트율 기반 조정
        hit_rate = metric.hit_rate
        ttl_multiplier = 1.0
        reason_parts = []
        
        if hit_rate < 0.70:
            # 히트율 매우 낮음: TTL 크게 연장
            ttl_multiplier = 1.8
            reason_parts.append(f"히트율 {hit_rate:.1%} (매우 낮음)")
        
        elif hit_rate < 0.80:
            # 히트율 낮음: TTL 연장
            ttl_multiplier = 1.5
            reason_parts.append(f"히트율 {hit_rate:.1%} (낮음)")
        
        elif hit_rate < 0.90:
            # 히트율 보통: TTL 약간 연장
            ttl_multiplier = 1.2
            reason_parts.append(f"히트율 {hit_rate:.1%} (보통)")
        
        elif hit_rate >= 0.95:
            # 히트율 높음: TTL 단축 가능
            # 하지만 최소 TTL은 유지
            ttl_multiplier = 0.9
            reason_parts.append(f"히트율 {hit_rate:.1%} (높음)")
        
        else:
            # 히트율 90-95%: 유지
            ttl_multiplier = 1.0
            reason_parts.append(f"히트율 {hit_rate:.1%} (최적)")
        
        # 2. 메모리 사용량 기반 조정
        size_mb = metric.size_mb
        
        if size_mb > 200:
            # 메모리 매우 많음: TTL 크게 단축
            ttl_multiplier *= 0.6
            reason_parts.append(f"메모리 {size_mb:.1f}MB (매우 많음)")
        
        elif size_mb > 100:
            # 메모리 많음: TTL 단축
            ttl_multiplier *= 0.8
            reason_parts.append(f"메모리 {size_mb:.1f}MB (많음)")
        
        elif size_mb < 10:
            # 메모리 적음: TTL 연장 가능
            ttl_multiplier *= 1.2
            reason_parts.append(f"메모리 {size_mb:.1f}MB (적음)")
        
        # 3. 항목 개수 기반 조정
        item_count = metric.item_count
        max_items = 200  # 캐시 타입별 최대 항목 수
        
        if item_count >= max_items * 0.9:  # 90% 도달
            # 거의 가득 참: TTL 단축하여 항목 제거
            ttl_multiplier *= 0.7
            reason_parts.append(f"항목 {item_count}/{max_items} (거의 가득)")
        
        # 4. 최종 TTL 계산
        new_ttl = int(base_ttl * ttl_multiplier)
        new_ttl = max(min_ttl, min(new_ttl, max_ttl))  # 범위 내로 제약
        
        reason = " + ".join(reason_parts) if reason_parts else "최적 상태 유지"
        
        return new_ttl, reason
    
    def get_current_ttl(self, cache_type: str) -> int:
        """현재 TTL 조회"""
        return self.current_ttls.get(cache_type, self.default_ttls.get(cache_type, 600))
    
    def reset_to_defaults(self):
        """TTL을 기본값으로 리셋"""
        self.current_ttls = self.default_ttls.copy()
        logger.info("캐시 TTL을 기본값으로 리셋")
    
    def get_optimization_history(
        self,
        cache_type: str,
        limit: int = 20,
    ) -> list:
        """
        TTL 조정 이력 조회
        
        Args:
            cache_type: 캐시 타입
            limit: 반환할 이력 개수
            
        Returns:
            최근 이력 리스트
        """
        history = self.ttl_history.get(cache_type, [])
        return history[-limit:] if history else []
    
    def get_summary(self) -> Dict[str, any]:
        """
        현재 상태 요약
        
        Returns:
            {cache_type: {current_ttl, default_ttl, optimization_count}}
        """
        summary = {}
        for cache_type in self.default_ttls.keys():
            history = self.ttl_history.get(cache_type, [])
            summary[cache_type] = {
                'current_ttl_seconds': self.current_ttls.get(cache_type),
                'default_ttl_seconds': self.default_ttls.get(cache_type),
                'optimization_count': len(history),
                'last_optimization': history[-1] if history else None,
            }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'last_optimization': self.last_optimization.isoformat() if self.last_optimization else None,
            'ttl_status': summary,
        }


# 글로벌 최적화기 인스턴스
_ttl_optimizer: Optional[CacheTTLOptimizer] = None


async def get_cache_ttl_optimizer() -> CacheTTLOptimizer:
    """캐시 TTL 최적화기 싱글톤 인스턴스 획득"""
    global _ttl_optimizer
    if _ttl_optimizer is None:
        _ttl_optimizer = CacheTTLOptimizer()
    return _ttl_optimizer
