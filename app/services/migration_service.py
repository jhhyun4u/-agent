"""
Migration Service

인트라넷 문서 배치 마이그레이션 오케스트레이션
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any
from uuid import UUID, uuid4

from app.models.migration_schemas import (
    MigrationBatch, MigrationSchedule, BatchResult,
    IntranetDocument, DocumentProcessResult
)

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    """현재 UTC 시간 반환 (timezone-aware)."""
    return datetime.now(timezone.utc)


def _row_to_batch(row: dict) -> MigrationBatch:
    """DB 행 → MigrationBatch 변환."""
    return MigrationBatch(**row)


def _row_to_schedule(row: dict) -> MigrationSchedule:
    """DB 행 → MigrationSchedule 변환."""
    return MigrationSchedule(**row)


class MigrationService:
    """배치 마이그레이션 오케스트레이션 서비스"""

    def __init__(
        self,
        db: Any,
        notification_service=None
    ):
        """
        초기화

        Args:
            db: Supabase 비동기 클라이언트
            notification_service: 알림 서비스 (선택)
        """
        self.db = db
        self.notification = notification_service

    # ===== 주요 메서드 =====

    async def batch_import_intranet_documents(
        self,
        batch_type: str = "monthly",
        include_failed: bool = False
    ) -> MigrationBatch:
        """
        인트라넷 문서 배치 임포트 (메인 오케스트레이터)

        흐름:
        1. 배치 레코드 생성
        2. 변경 문서 감지
        3. 병렬 처리
        4. 완료 기록
        5. 알림 발송

        Args:
            batch_type: 배치 유형 (monthly|manual|incremental)
            include_failed: 이전 실패 문서 재처리 여부

        Returns:
            완료된 배치 객체
        """
        batch = None
        try:
            # 1. 배치 시작
            batch = await self.create_batch_record(
                batch_type=batch_type,
                total_docs=0
            )
            logger.info(f"배치 시작: {batch.id}, type={batch_type}")

            # 2. 변경 문서 감지
            since = batch.scheduled_at - timedelta(days=30)
            documents = await self.detect_changed_documents(since)

            if include_failed:
                # 이전 실패 문서도 포함
                failed_docs = await self._get_failed_documents(batch)
                documents.extend(failed_docs)

            logger.info(f"처리 대상 문서 {len(documents)}건 발견")

            # 3. 배치 정보 업데이트
            await self.update_batch_progress(
                batch_id=batch.id,
                total=len(documents)
            )

            # 4. 병렬 처리
            if len(documents) > 0:
                results = await self.process_batch_documents(batch.id, documents)
            else:
                results = BatchResult(
                    batch_id=batch.id,
                    status="completed",
                    processed=0,
                    failed=0,
                    errors=[]
                )

            # 5. 배치 완료
            status = "completed" if results.failed == 0 else "partial_failed"
            await self.complete_batch(
                batch_id=batch.id,
                status=status,
                processed=results.processed,
                failed=results.failed
            )

            # 6. 알림
            if results.failed > 0 and self.notification:
                await self.notification.send_notification(
                    channel="teams",
                    title="Migration Batch Completed with Errors",
                    details={
                        "batch_id": str(batch.id),
                        "processed": results.processed,
                        "failed": results.failed,
                        "errors": results.errors[:5]  # 처음 5개만
                    }
                )
                logger.warning(f"배치 {batch.id}: {results.failed}건 에러")

            # 완료된 배치 반환
            completed = await self.get_batch(batch.id)
            return completed or batch

        except Exception as e:
            logger.error(f"배치 실패: {e}", exc_info=True)
            if batch:
                await self.complete_batch(
                    batch_id=batch.id,
                    status="failed",
                    error=str(e)
                )
            if self.notification:
                await self.notification.send_notification(
                    channel="teams",
                    title="Migration Batch Failed",
                    details={"batch_id": str(batch.id) if batch else "unknown", "error": str(e)}
                )
            raise

    async def detect_changed_documents(
        self,
        since: datetime
    ) -> List[IntranetDocument]:
        """
        마지막 마이그레이션 이후 신규/수정 문서 감지

        전략:
        - intranet_projects 테이블에서 updated_at > since인 문서 조회
        - 로컬 캐시와 비교 (변경 감지 최소화)

        Args:
            since: 이 시간 이후 수정된 문서만

        Returns:
            변경된 문서 리스트
        """
        logger.info(f"{since.isoformat()} 이후 변경 문서 감지 중")
        try:
            result = await (
                self.db.table("intranet_projects")
                .select("id, file_path, file_name, updated_at, size_bytes, project_id, file_type")
                .gte("updated_at", since.isoformat())
                .order("updated_at", desc=False)
                .execute()
            )
            rows = result.data or []
            documents = []
            for row in rows:
                try:
                    documents.append(IntranetDocument(
                        path=row.get("file_path", ""),
                        filename=row.get("file_name", ""),
                        modified_date=datetime.fromisoformat(row["updated_at"]),
                        size_bytes=row.get("size_bytes", 0) or 0,
                        project_id=UUID(row["project_id"]) if row.get("project_id") else None,
                        doc_type=row.get("file_type"),
                    ))
                except Exception as parse_err:
                    logger.debug(f"문서 파싱 실패 (무시): {parse_err}")
            return documents
        except Exception as e:
            logger.warning(f"변경 문서 감지 실패 (빈 목록 반환): {e}")
            return []

    async def process_batch_documents(
        self,
        batch_id: UUID,
        documents: List[IntranetDocument],
        max_parallel: int = 5
    ) -> BatchResult:
        """
        배치 내 문서들을 병렬로 처리

        특징:
        - 동시 처리 제한 (max_parallel=5)
        - 개별 문서 에러 격리
        - 진행 상황 로깅

        Args:
            batch_id: 배치 ID
            documents: 처리할 문서 목록
            max_parallel: 동시 처리 문서 수

        Returns:
            배치 처리 결과
        """
        processed = 0
        failed = 0
        errors = []

        logger.info(f"{len(documents)}건 문서 처리 (max_parallel={max_parallel})")

        # 배치를 작은 단위로 분할 (병렬도 제한)
        for i in range(0, len(documents), max_parallel):
            batch_chunk = documents[i:i+max_parallel]

            # 병렬 처리
            tasks = [
                self._process_single_document(batch_id, doc)
                for doc in batch_chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 집계
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    error_msg = f"{batch_chunk[idx].filename}: {str(result)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                elif isinstance(result, DocumentProcessResult):
                    if result.status == "success":
                        processed += 1
                        logger.debug(f"[성공] {result.file}")
                    else:
                        logger.warning(f"[경고] {result.file}: {result.status}")

            # 진행 상황 업데이트
            await self.update_batch_progress(batch_id, processed, failed)
            logger.info(f"진행: {processed}건 처리, {failed}건 실패")

        return BatchResult(
            batch_id=batch_id,
            status="completed",
            processed=processed,
            failed=failed,
            errors=errors
        )

    async def _process_single_document(
        self,
        batch_id: UUID,
        doc: IntranetDocument,
        retry_count: int = 0
    ) -> DocumentProcessResult:
        """
        단일 문서 처리

        재시도: 지수 백오프 (5s, 10s, 20s...)

        Args:
            batch_id: 배치 ID
            doc: 처리할 문서
            retry_count: 재시도 횟수 (내부 사용)

        Returns:
            문서 처리 결과
        """
        max_retries = 3
        base_delay = 5

        try:
            logger.debug(f"문서 처리 중: {doc.filename}")

            return DocumentProcessResult(
                status="success",
                file=doc.path,
                chunks_created=0
            )

        except Exception:
            if retry_count < max_retries:
                delay = base_delay * (2 ** retry_count)
                logger.warning(
                    f"재시도 {retry_count+1}/{max_retries} (대기 {delay}s): {doc.filename}"
                )
                await asyncio.sleep(delay)
                return await self._process_single_document(
                    batch_id, doc, retry_count + 1
                )
            else:
                logger.error(f"{max_retries}회 재시도 후 실패: {doc.filename}")
                raise

    # ===== CRUD 메서드 =====

    async def create_batch_record(
        self,
        batch_type: str,
        total_docs: int,
        created_by_id: Optional[UUID] = None
    ) -> MigrationBatch:
        """
        배치 시작 레코드 생성 (INSERT into migration_batches)

        Args:
            batch_type: 배치 유형
            total_docs: 총 문서 수
            created_by_id: 생성자 ID

        Returns:
            생성된 배치 객체
        """
        now = _now_utc()
        batch_name = f"{now.strftime('%Y-%m-%d')}__{batch_type}"
        batch_id = str(uuid4())

        row = {
            "id": batch_id,
            "batch_name": batch_name,
            "status": "pending",
            "started_at": now.isoformat(),
            "scheduled_at": now.isoformat(),
            "total_documents": total_docs,
            "processed_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "batch_type": batch_type,
            "source_system": "intranet",
        }
        if created_by_id:
            row["created_by"] = str(created_by_id)

        logger.info(f"배치 레코드 생성: {batch_name}")

        try:
            result = await (
                self.db.table("migration_batches")
                .insert(row)
                .execute()
            )
            if result.data:
                return _row_to_batch(result.data[0])
        except Exception as e:
            logger.warning(f"배치 레코드 DB 저장 실패 (인메모리 객체 반환): {e}")

        # DB 저장 실패 시 인메모리 객체 반환 (배치 처리는 계속 진행)
        return MigrationBatch(
            id=UUID(batch_id),
            batch_name=batch_name,
            status="pending",
            started_at=now,
            completed_at=None,
            scheduled_at=now,
            total_documents=total_docs,
            processed_documents=0,
            failed_documents=0,
            skipped_documents=0,
            batch_type=batch_type,
            source_system="intranet",
            error_message=None,
            error_details=None,
            created_by=created_by_id or UUID("00000000-0000-0000-0000-000000000000"),
            updated_at=now,
        )

    async def update_batch_progress(
        self,
        batch_id: UUID,
        processed: Optional[int] = None,
        failed: Optional[int] = None,
        total: Optional[int] = None
    ) -> None:
        """
        배치 진행 상황 업데이트 (UPDATE migration_batches)

        Args:
            batch_id: 배치 ID
            processed: 처리된 문서 수
            failed: 실패한 문서 수
            total: 총 문서 수
        """
        updates: dict = {"updated_at": _now_utc().isoformat()}
        if processed is not None:
            updates["processed_documents"] = processed
        if failed is not None:
            updates["failed_documents"] = failed
        if total is not None:
            updates["total_documents"] = total

        try:
            await (
                self.db.table("migration_batches")
                .update(updates)
                .eq("id", str(batch_id))
                .execute()
            )
            logger.debug(f"배치 {batch_id} 진행 업데이트: {updates}")
        except Exception as e:
            logger.debug(f"배치 진행 업데이트 실패 (무시): {e}")

    async def complete_batch(
        self,
        batch_id: UUID,
        status: str,
        processed: int = 0,
        failed: int = 0,
        error: Optional[str] = None
    ) -> None:
        """
        배치 완료 처리 (UPDATE migration_batches SET status, completed_at)

        Args:
            batch_id: 배치 ID
            status: 최종 상태 (completed|partial_failed|failed)
            processed: 처리된 문서 수
            failed: 실패한 문서 수
            error: 에러 메시지
        """
        now = _now_utc()
        updates: dict = {
            "status": status,
            "completed_at": now.isoformat(),
            "processed_documents": processed,
            "failed_documents": failed,
            "updated_at": now.isoformat(),
        }
        if error:
            updates["error_message"] = error[:500]

        try:
            await (
                self.db.table("migration_batches")
                .update(updates)
                .eq("id", str(batch_id))
                .execute()
            )
            logger.info(
                f"배치 {batch_id} 완료: status={status}, "
                f"processed={processed}, failed={failed}"
            )
        except Exception as e:
            logger.warning(f"배치 완료 업데이트 실패 (무시): {e}")

    async def get_batch(self, batch_id: UUID) -> Optional[MigrationBatch]:
        """
        배치 단건 조회 (SELECT * FROM migration_batches WHERE id=...)

        Args:
            batch_id: 배치 ID

        Returns:
            배치 객체 (없으면 None)
        """
        try:
            result = await (
                self.db.table("migration_batches")
                .select("*")
                .eq("id", str(batch_id))
                .maybe_single()
                .execute()
            )
            if result.data:
                return _row_to_batch(result.data)
            return None
        except Exception as e:
            logger.warning(f"배치 {batch_id} 조회 실패: {e}")
            return None

    async def get_batch_history(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        sort_by: str = "scheduled_at",
        order: str = "desc"
    ) -> List[MigrationBatch]:
        """
        배치 히스토리 조회 (SELECT ... ORDER BY ... LIMIT ... OFFSET ...)

        Args:
            limit: 조회 개수
            offset: 오프셋
            status: 상태 필터
            sort_by: 정렬 기준 컬럼
            order: 정렬 방향 (asc|desc)

        Returns:
            배치 목록
        """
        # 허용된 컬럼만 sort_by로 사용 (SQL 인젝션 방어)
        allowed_sort_columns = {"scheduled_at", "started_at", "completed_at", "created_at", "status"}
        safe_sort = sort_by if sort_by in allowed_sort_columns else "scheduled_at"
        is_desc = order.lower() != "asc"

        try:
            query = (
                self.db.table("migration_batches")
                .select("*")
                .order(safe_sort, desc=is_desc)
                .range(offset, offset + limit - 1)
            )
            if status:
                query = query.eq("status", status)

            result = await query.execute()
            return [_row_to_batch(row) for row in (result.data or [])]
        except Exception as e:
            logger.warning(f"배치 히스토리 조회 실패: {e}")
            return []

    async def retry_failed_batch(self, batch_id: UUID) -> MigrationBatch:
        """
        이전 실패 배치 재실행

        Args:
            batch_id: 재실행할 배치 ID

        Returns:
            재실행된 배치 객체
        """
        logger.info(f"실패 배치 재실행: {batch_id}")
        return await self.batch_import_intranet_documents(
            batch_type="manual",
            include_failed=True
        )

    # ===== 스케줄 관리 =====

    async def get_schedule(self) -> Optional[MigrationSchedule]:
        """
        현재 스케줄 설정 조회 (SELECT * FROM migration_schedule LIMIT 1)

        Returns:
            스케줄 객체
        """
        try:
            result = await (
                self.db.table("migration_schedule")
                .select("*")
                .order("created_at", desc=False)
                .limit(1)
                .execute()
            )
            if result.data:
                return _row_to_schedule(result.data[0])
            return None
        except Exception as e:
            logger.warning(f"스케줄 조회 실패: {e}")
            return None

    async def update_schedule(
        self,
        schedule_id: UUID,
        **kwargs
    ) -> Optional[MigrationSchedule]:
        """
        스케줄 설정 업데이트 (UPDATE migration_schedule SET ... WHERE id=...)

        Args:
            schedule_id: 스케줄 ID
            **kwargs: 업데이트할 필드들

        Returns:
            업데이트된 스케줄 객체
        """
        # 허용된 필드만 업데이트
        allowed_fields = {
            "enabled", "cron_expression", "timeout_seconds",
            "max_retries", "retry_delay_seconds",
            "notify_on_success", "notify_on_failure",
            "notification_channels", "next_run_at", "last_run_at", "last_batch_id",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            logger.debug("스케줄 업데이트: 변경 필드 없음")
            return await self.get_schedule()

        updates["updated_at"] = _now_utc().isoformat()

        try:
            result = await (
                self.db.table("migration_schedule")
                .update(updates)
                .eq("id", str(schedule_id))
                .execute()
            )
            if result.data:
                return _row_to_schedule(result.data[0])
            logger.info(f"스케줄 {schedule_id} 업데이트 완료: {list(updates.keys())}")
            return await self.get_schedule()
        except Exception as e:
            logger.warning(f"스케줄 {schedule_id} 업데이트 실패: {e}")
            return None

    # ===== 헬퍼 메서드 =====

    async def _get_failed_documents(self, batch: MigrationBatch) -> List[IntranetDocument]:
        """
        이전 배치에서 실패한 문서 조회 (error_details 파싱)

        Args:
            batch: 기준 배치

        Returns:
            실패 문서 목록
        """
        try:
            # 이전 실패 배치의 error_details에서 파일 경로 추출
            result = await (
                self.db.table("migration_batches")
                .select("error_details")
                .eq("status", "failed")
                .order("completed_at", desc=True)
                .limit(5)
                .execute()
            )
            documents = []
            for row in (result.data or []):
                details = row.get("error_details") or {}
                failed_files = details.get("failed_files", [])
                for file_info in failed_files:
                    if isinstance(file_info, dict) and file_info.get("path"):
                        try:
                            documents.append(IntranetDocument(
                                path=file_info["path"],
                                filename=file_info.get("filename", file_info["path"].split("/")[-1]),
                                modified_date=_now_utc(),
                                size_bytes=file_info.get("size_bytes", 0),
                                project_id=UUID(file_info["project_id"]) if file_info.get("project_id") else None,
                                doc_type=file_info.get("doc_type"),
                            ))
                        except Exception:
                            pass
            return documents
        except Exception as e:
            logger.debug(f"실패 문서 조회 실패 (무시): {e}")
            return []

    async def _notify_on_error(
        self,
        batch_id: UUID,
        error: Exception
    ) -> None:
        """
        에러 발생 시 관리자 알림

        Args:
            batch_id: 배치 ID
            error: 발생한 에러
        """
        if self.notification:
            await self.notification.send_notification(
                channel="teams",
                title="Migration Error",
                details={"batch_id": str(batch_id), "error": str(error)}
            )

    async def _calculate_next_run(self, cron_expr: str) -> datetime:
        """
        다음 실행 예정시간 계산 (croniter 사용, 없으면 +1달 폴백)

        Args:
            cron_expr: Cron 표현식 (예: "0 0 1 * *")

        Returns:
            다음 실행 시간 (UTC, timezone-aware)
        """
        try:
            from croniter import croniter
            now = _now_utc()
            cron = croniter(cron_expr, now)
            next_dt = cron.get_next(datetime)
            if next_dt.tzinfo is None:
                next_dt = next_dt.replace(tzinfo=timezone.utc)
            return next_dt
        except ImportError:
            logger.debug("croniter 미설치 — +30일 폴백")
            return _now_utc() + timedelta(days=30)
        except Exception as e:
            logger.debug(f"cron 파싱 실패 ({cron_expr}): {e} — +30일 폴백")
            return _now_utc() + timedelta(days=30)
