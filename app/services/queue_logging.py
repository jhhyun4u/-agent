"""Queue operation logging for STEP 8 ACT phase"""
import logging
from datetime import datetime, timezone
from typing import Optional


class QueueLogger:
    def __init__(self, name: str = "queue"):
        self.logger = logging.getLogger(f"app.queue.{name}")

    def log_enqueue(self, job_id: str, priority: int, queue_key: str, 
                    duration_ms: float, error: Optional[str] = None):
        self.logger.info(
            f"Job enqueued: {job_id} (priority={priority})",
            extra={"operation": "enqueue", "job_id": job_id, 
                   "duration_ms": round(duration_ms, 2), "error": error}
        )

    def log_dequeue(self, worker_id: str, job_id: Optional[str] = None,
                    duration_ms: Optional[float] = None, error: Optional[str] = None):
        self.logger.info(
            f"Job dequeued by {worker_id}: {job_id}",
            extra={"operation": "dequeue", "worker_id": worker_id, 
                   "job_id": job_id, "duration_ms": round(duration_ms, 2) if duration_ms else None}
        )

    def log_state_update(self, job_id: str, old_status: str, new_status: str,
                        worker_id: Optional[str] = None, duration_ms: Optional[float] = None):
        self.logger.info(f"Job state: {job_id} {old_status} to {new_status}",
                        extra={"operation": "state_update", "job_id": job_id})

    def log_timeout(self, job_id: str, job_type: str, timeout_seconds: float,
                   elapsed_seconds: float, worker_id: Optional[str] = None):
        self.logger.warning(f"Job timeout: {job_id} after {elapsed_seconds}s",
                           extra={"operation": "timeout", "job_id": job_id})

    def log_retry(self, job_id: str, attempt: int, max_retries: int,
                 error: str, worker_id: Optional[str] = None):
        self.logger.info(f"Job retry: {job_id} attempt {attempt}/{max_retries}",
                        extra={"operation": "retry", "job_id": job_id})

    def log_dlq_move(self, job_id: str, reason: str, retry_count: int):
        self.logger.error(f"Job to DLQ: {job_id} - {reason}",
                         extra={"operation": "dlq_move", "job_id": job_id})


queue_logger = QueueLogger("global")
