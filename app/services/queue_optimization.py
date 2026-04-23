"""Queue manager optimization for production throughput"""
import asyncio
import time
from typing import Optional


class QueueOptimization:
    """Throughput optimization strategies"""
    
    BATCH_SIZE = 100
    REDIS_POOL_SIZE = 20
    DEQUEUE_TIMEOUT = 1
    HEARTBEAT_INTERVAL = 10
    METRIC_FLUSH_INTERVAL = 60

    @staticmethod
    async def batch_enqueue(redis_client, jobs: list, queue_key: str) -> int:
        """Batch enqueue jobs for throughput"""
        if not jobs:
            return 0
        
        pipeline = redis_client.pipeline()
        for job in jobs:
            pipeline.rpush(queue_key, job)
        await pipeline.execute()
        return len(jobs)

    @staticmethod
    async def dequeue_with_timeout(redis_client, queue_key: str, timeout: float):
        """Dequeue with non-blocking timeout"""
        try:
            return await asyncio.wait_for(
                redis_client.blpop(queue_key, timeout=1),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

    @staticmethod
    def calculate_worker_efficiency(metrics: dict) -> float:
        """Calculate worker utilization efficiency"""
        total_jobs = metrics.get('total_jobs', 0)
        successful_jobs = metrics.get('successful_jobs', 0)
        failed_jobs = metrics.get('failed_jobs', 0)
        
        if total_jobs == 0:
            return 0.0
        
        return (successful_jobs / total_jobs) * 100


class PerformanceTuning:
    """Performance tuning parameters for production"""
    
    TIMEOUT_GRACE_PERIOD = 10
    MAX_CONCURRENT_JOBS = 5
    BATCH_FLUSH_SIZE = 50
    METRIC_SAMPLING_RATE = 0.1
    
    @staticmethod
    def get_adaptive_timeout(job_type: str, retry_count: int) -> float:
        """Get adaptive timeout based on job type and retries"""
        base_timeouts = {
            'step4a_diagnosis': 120,
            'step4a_regenerate': 120,
            'step4b_pricing': 120,
            'step5a_pptx': 180,
            'step5b_submission': 150,
            'step6_evaluation': 150,
        }
        
        base = base_timeouts.get(job_type, 120)
        retry_factor = 1 + (retry_count * 0.1)
        return base * retry_factor
