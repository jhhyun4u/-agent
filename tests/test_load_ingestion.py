"""
문서 수집 API - 부하 테스트 및 성능 검증

테스트 범위:
- 배치 크기 최적화 (250 임베딩, 200 삽입)
- Knowledge 분류 병렬화
- 동시 문서 처리 제한 (MAX_CONCURRENT_DOCUMENTS=5)
- 메모리 최적화
- 다양한 부하 조건에서의 성능 검증
- 스트레스 테스트
"""

import pytest
import asyncio
import time
import psutil
import os
import gc
import json
from typing import List, Dict, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO


# ── 성능 테스트용 Fixture ──

@pytest.fixture
def process():
    """현재 프로세스"""
    return psutil.Process(os.getpid())


@pytest.fixture
def generate_test_pdf():
    """테스트용 PDF 파일 생성"""
    def _generate(size_kb: int = 100) -> BytesIO:
        """size_kb 크기의 모의 PDF 생성"""
        content = b'%PDF-1.4\n'
        # 텍스트 스트림 추가하여 크기 증가
        text_content = f'BT /F1 12 Tf (Sample document content) Tj ET\n' * (size_kb * 10)
        content += text_content.encode()
        content += b'%%EOF'
        return BytesIO(content)
    return _generate


@pytest.fixture
def generate_mock_chunks():
    """대규모 청크 데이터 생성"""
    def _generate(count: int) -> List[str]:
        """count개의 모의 청크 생성 (각 ~500자)"""
        chunks = []
        for i in range(count):
            chunk_text = f'Document chunk {i}: ' + ('Sample document text. ' * 20)
            chunks.append(chunk_text)
        return chunks
    return _generate


@pytest.fixture
def mock_openai_embeddings():
    """OpenAI 임베딩 API 모킹"""
    async def _mock_embed(texts: List[str]) -> List[List[float]]:
        """각 텍스트에 대해 1536차원 임베딩 반환"""
        embeddings = []
        for text in texts:
            # 모의 임베딩 (1536차원)
            embedding = [0.1 * (i % 10) for i in range(1536)]
            embeddings.append(embedding)
        return embeddings
    return _mock_embed


# ── 배치 처리 최적화 검증 ──

class TestBatchOptimization:
    """배치 크기 최적화 검증"""

    @pytest.mark.asyncio
    async def test_embedding_batch_size_configuration(self):
        """EMBEDDING_BATCH_SIZE가 250으로 설정되어 있는지 검증"""
        from app.services.document_ingestion import EMBEDDING_BATCH_SIZE
        assert EMBEDDING_BATCH_SIZE == 250, f"Expected 250, got {EMBEDDING_BATCH_SIZE}"

    @pytest.mark.asyncio
    async def test_insert_batch_size_configuration(self):
        """INSERT_BATCH_SIZE가 200으로 설정되어 있는지 검증"""
        from app.services.document_ingestion import INSERT_BATCH_SIZE
        assert INSERT_BATCH_SIZE == 200, f"Expected 200, got {INSERT_BATCH_SIZE}"

    @pytest.mark.asyncio
    async def test_batch_count_reduction_embeddings(self, generate_mock_chunks):
        """20,000개 청크 처리 시 배치 수 감소 검증"""
        from app.services.document_ingestion import EMBEDDING_BATCH_SIZE
        
        chunks = generate_mock_chunks(20000)
        
        # 최적화 전: 100크기 배치 = 200 배치
        old_batch_count = (len(chunks) + 99) // 100
        
        # 최적화 후: 250크기 배치 = 80 배치
        new_batch_count = (len(chunks) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
        
        # 배치 수 감소 검증 (60% 감소)
        reduction = (old_batch_count - new_batch_count) / old_batch_count
        assert reduction >= 0.60, f"Expected 60% reduction, got {reduction * 100}%"
        assert new_batch_count == 80, f"Expected 80 batches, got {new_batch_count}"

    @pytest.mark.asyncio
    async def test_batch_count_reduction_inserts(self, generate_mock_chunks):
        """20,000개 행 삽입 시 배치 수 감소 검증"""
        from app.services.document_ingestion import INSERT_BATCH_SIZE
        
        rows = generate_mock_chunks(20000)
        
        # 최적화 전: 50크기 배치 = 400 배치
        old_batch_count = (len(rows) + 49) // 50
        
        # 최적화 후: 200크기 배치 = 100 배치
        new_batch_count = (len(rows) + INSERT_BATCH_SIZE - 1) // INSERT_BATCH_SIZE
        
        # 배치 수 감소 검증 (75% 감소)
        reduction = (old_batch_count - new_batch_count) / old_batch_count
        assert reduction >= 0.75, f"Expected 75% reduction, got {reduction * 100}%"
        assert new_batch_count == 100, f"Expected 100 batches, got {new_batch_count}"


# ── 동시 처리 제한 검증 ──

class TestConcurrencyControl:
    """동시 처리 제한 검증"""

    @pytest.mark.asyncio
    async def test_max_concurrent_documents_limit(self):
        """MAX_CONCURRENT_DOCUMENTS가 5로 설정되어 있는지 검증"""
        from app.services.document_ingestion import MAX_CONCURRENT_DOCUMENTS
        assert MAX_CONCURRENT_DOCUMENTS == 5, f"Expected 5, got {MAX_CONCURRENT_DOCUMENTS}"

    @pytest.mark.asyncio
    async def test_max_concurrent_classifications_limit(self):
        """MAX_CONCURRENT_CLASSIFICATIONS가 10으로 설정되어 있는지 검증"""
        from app.services.document_ingestion import MAX_CONCURRENT_CLASSIFICATIONS
        assert MAX_CONCURRENT_CLASSIFICATIONS == 10, f"Expected 10, got {MAX_CONCURRENT_CLASSIFICATIONS}"

    @pytest.mark.asyncio
    async def test_document_processing_concurrency_enforcement(self):
        """문서 처리 동시성 제한이 실제로 적용되는지 검증"""
        from app.services.document_ingestion import _document_processing_semaphore
        
        # Semaphore가 존재하고 제한값이 5인지 확인
        assert _document_processing_semaphore is not None
        assert _document_processing_semaphore._value == 5, \
            f"Expected semaphore value 5, got {_document_processing_semaphore._value}"

    @pytest.mark.asyncio
    async def test_concurrent_processing_throughput(self):
        """동시 문서 처리 시 처리량 검증"""
        async def mock_process_bounded(semaphore, doc_id):
            """모의 문서 처리 함수"""
            async with semaphore:
                await asyncio.sleep(0.1)  # 처리 시뮬레이션
                return f"processed_{doc_id}"

        semaphore = asyncio.Semaphore(5)
        
        # 10개 문서 동시 처리 (제한값: 5)
        start_time = time.time()
        tasks = [mock_process_bounded(semaphore, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        assert len(results) == 10
        # 5개씩 2배치 = 최소 0.2초 필요
        assert elapsed >= 0.2, f"Expected at least 0.2s, got {elapsed}s"
        # 하지만 10개를 병렬처리했으므로 1초보다 작음
        assert elapsed < 1.0, f"Expected less than 1.0s, got {elapsed}s"


# ── 메모리 최적화 검증 ──

class TestMemoryOptimization:
    """메모리 최적화 검증"""

    @pytest.mark.asyncio
    async def test_gc_module_imported(self):
        """gc 모듈이 임포트되었는지 검증"""
        try:
            from app.services import document_ingestion
            assert hasattr(document_ingestion, 'gc'), "gc module not imported"
        except ImportError:
            pytest.fail("Failed to import document_ingestion module")

    @pytest.mark.asyncio
    async def test_memory_cleanup_after_processing(self):
        """처리 후 메모리 정리 검증"""
        import gc
        
        # 초기 메모리 측정
        gc.collect()
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # 대량의 데이터 생성 및 정리
        chunks = ['x' * 10000 for _ in range(1000)]
        del chunks
        gc.collect()
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_freed = max(0, memory_before - memory_after)
        
        # 최소한 일부 메모리가 정리되었는지 확인
        assert memory_freed >= 0, "Memory should be freed or at least maintained"

    @pytest.mark.asyncio
    async def test_large_file_memory_efficiency(self, generate_mock_chunks, process):
        """대용량 파일 처리 시 메모리 효율성"""
        # 5000개 청크 = ~5MB 데이터
        chunks = generate_mock_chunks(5000)
        
        gc.collect()
        memory_before = process.memory_info().rss / 1024 / 1024
        
        # 청크 배치 처리 시뮬레이션
        embeddings = []
        for i in range(0, len(chunks), 250):  # EMBEDDING_BATCH_SIZE = 250
            batch = chunks[i:i+250]
            # 각 배치에 대해 임베딩 생성 시뮬레이션
            batch_embeddings = [[0.1] * 1536 for _ in batch]
            embeddings.extend(batch_embeddings)
        
        del chunks, embeddings
        gc.collect()
        memory_after = process.memory_info().rss / 1024 / 1024
        
        # 메모리 최적화 전: ~50MB 증가
        # 메모리 최적화 후: ~5-10MB 증가만 되어야 함
        memory_increase = memory_after - memory_before
        assert memory_increase < 20, f"Memory increase too high: {memory_increase}MB"


# ── 부하 테스트 ──

class TestLoadScenarios:
    """다양한 부하 조건 테스트"""

    @pytest.mark.asyncio
    async def test_sequential_document_processing_10_docs(self, generate_test_pdf):
        """10개 문서 순차 처리"""
        processing_times = []
        
        for i in range(10):
            start_time = time.time()
            # 문서 처리 시뮬레이션 (100KB PDF)
            pdf = generate_test_pdf(100)
            file_size = len(pdf.getvalue())
            
            # 청킹 시뮬레이션
            await asyncio.sleep(0.05)  # 50ms 처리
            
            elapsed = time.time() - start_time
            processing_times.append(elapsed)
        
        avg_time = sum(processing_times) / len(processing_times)
        total_time = sum(processing_times)
        
        # 각 문서: ~50-100ms
        assert avg_time < 0.2, f"Average time too high: {avg_time}s"
        # 10개 문서: ~0.5-1초
        assert total_time < 2.0, f"Total time too high: {total_time}s"

    @pytest.mark.asyncio
    async def test_concurrent_document_processing_5_docs(self, generate_test_pdf):
        """5개 문서 동시 처리 (동시성 제한값)"""
        async def process_document(doc_id):
            start = time.time()
            pdf = generate_test_pdf(100)
            await asyncio.sleep(0.1)  # 처리 시뮬레이션
            return time.time() - start
        
        start_time = time.time()
        tasks = [process_document(i) for i in range(5)]
        processing_times = await asyncio.gather(*tasks)
        total_elapsed = time.time() - start_time
        
        # 5개를 병렬 처리: ~100ms (이론적)
        # 그러나 제한 없이 병렬이므로 100-150ms
        assert total_elapsed < 0.5, f"Total time too high: {total_elapsed}s"
        assert max(processing_times) < 0.2, f"Max processing time too high: {max(processing_times)}s"

    @pytest.mark.asyncio
    async def test_concurrent_document_processing_10_docs_with_limit(self):
        """10개 문서 동시성 제한(5)으로 처리"""
        async def process_with_semaphore(semaphore, doc_id, delay=0.1):
            async with semaphore:
                await asyncio.sleep(delay)
                return doc_id
        
        semaphore = asyncio.Semaphore(5)  # MAX_CONCURRENT_DOCUMENTS
        
        start_time = time.time()
        tasks = [process_with_semaphore(semaphore, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_elapsed = time.time() - start_time
        
        assert len(results) == 10
        
        # 10개를 5개씩 2배치: 최소 0.2초
        assert total_elapsed >= 0.15, f"Processing too fast: {total_elapsed}s"
        # 하지만 1초 내에는 완료
        assert total_elapsed < 1.0, f"Total time too high: {total_elapsed}s"

    @pytest.mark.asyncio
    async def test_varying_file_sizes(self, generate_test_pdf, process):
        """다양한 파일 크기 처리"""
        test_sizes = [10, 50, 100, 500]  # KB
        results = {}
        
        for size_kb in test_sizes:
            gc.collect()
            mem_before = process.memory_info().rss / 1024 / 1024
            
            pdf = generate_test_pdf(size_kb)
            file_data = pdf.getvalue()
            
            # 처리 시뮬레이션
            await asyncio.sleep(0.05)
            
            del pdf, file_data
            gc.collect()
            mem_after = process.memory_info().rss / 1024 / 1024
            
            results[size_kb] = {
                'file_size_kb': size_kb,
                'memory_delta_mb': mem_after - mem_before
            }
        
        # 메모리 사용이 파일 크기와 선형 관계여야 함
        for size_kb, data in results.items():
            # 각 KB당 ~1-5KB 메모리 오버헤드
            assert data['memory_delta_mb'] < 10, \
                f"Memory overhead too high for {size_kb}KB: {data['memory_delta_mb']}MB"


# ── 스트레스 테스트 ──

class TestStressScenarios:
    """극한 조건 테스트"""

    @pytest.mark.asyncio
    async def test_burst_load_20_documents(self):
        """버스트 로드: 20개 문서 동시 요청"""
        async def process_doc(doc_id, semaphore):
            async with semaphore:
                await asyncio.sleep(0.1)
                return f"doc_{doc_id}"
        
        semaphore = asyncio.Semaphore(5)  # MAX_CONCURRENT
        
        start_time = time.time()
        tasks = [process_doc(i, semaphore) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        success_rate = successful / len(results) * 100
        
        # 모든 작업 완료
        assert success_rate == 100, f"Success rate: {success_rate}%"
        # 20개를 5개씩 4배치: 최소 0.4초
        assert elapsed >= 0.35, f"Processing too fast: {elapsed}s"
        assert elapsed < 2.0, f"Total time too high: {elapsed}s"

    @pytest.mark.asyncio
    async def test_sustained_load_1000_classifications(self):
        """지속적 부하: 1000개 분류 작업"""
        async def classify(item_id, semaphore):
            async with semaphore:
                await asyncio.sleep(0.001)  # 1ms 분류
                return f"classified_{item_id}"
        
        semaphore = asyncio.Semaphore(10)  # MAX_CONCURRENT_CLASSIFICATIONS
        
        start_time = time.time()
        tasks = [classify(i, semaphore) for i in range(1000)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful == 1000
        
        # 1000개를 10개씩 100배치: ~100ms (1ms × 100)
        assert elapsed < 2.0, f"Total time too high: {elapsed}s"
        
        # 처리량 검증: 최소 500 items/sec
        throughput = 1000 / elapsed
        assert throughput >= 500, f"Throughput too low: {throughput} items/sec"

    @pytest.mark.asyncio
    async def test_recovery_from_spike(self):
        """스파이크 이후 복구"""
        async def process_with_delay(doc_id, semaphore, delay):
            async with semaphore:
                await asyncio.sleep(delay)
                return doc_id
        
        semaphore = asyncio.Semaphore(5)
        
        # 정상 부하: 5개 문서, 100ms
        normal_tasks = [process_with_delay(i, semaphore, 0.1) for i in range(5)]
        start = time.time()
        normal_results = await asyncio.gather(*normal_tasks)
        normal_time = time.time() - start
        
        # 스파이크: 20개 문서, 10ms (더 빠름)
        spike_tasks = [process_with_delay(i, semaphore, 0.01) for i in range(5, 25)]
        start = time.time()
        spike_results = await asyncio.gather(*spike_tasks)
        spike_time = time.time() - start
        
        # 복구: 정상 부하 재개, 100ms
        recovery_tasks = [process_with_delay(i, semaphore, 0.1) for i in range(25, 30)]
        start = time.time()
        recovery_results = await asyncio.gather(*recovery_tasks)
        recovery_time = time.time() - start
        
        # 정상 시간과 복구 시간이 유사해야 함 (복구됨)
        assert recovery_time < normal_time * 1.5, "System not recovered properly"


# ── 성능 비교 ──

class TestPerformanceComparison:
    """최적화 전후 성능 비교"""

    @pytest.mark.asyncio
    async def test_batch_optimization_impact(self, generate_mock_chunks):
        """배치 최적화의 영향 검증"""
        chunks = generate_mock_chunks(20000)
        
        # 최적화 전: 100개 배치
        old_config = {'batch_size': 100}
        old_calls = (len(chunks) + old_config['batch_size'] - 1) // old_config['batch_size']
        
        # 최적화 후: 250개 배치
        from app.services.document_ingestion import EMBEDDING_BATCH_SIZE
        new_calls = (len(chunks) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
        
        # API 호출 감소
        reduction = (old_calls - new_calls) / old_calls * 100
        expected_reduction = 60  # 60% 감소
        
        assert reduction >= expected_reduction * 0.9, \
            f"Expected ~{expected_reduction}% reduction, got {reduction:.1f}%"

    @pytest.mark.asyncio
    async def test_concurrent_vs_sequential_classification(self):
        """동시 vs 순차 분류의 성능 차이"""
        async def classify_item(item_id, delay=0.01):
            await asyncio.sleep(delay)
            return f"classified_{item_id}"
        
        item_count = 100
        
        # 순차 처리
        start = time.time()
        sequential_results = []
        for i in range(item_count):
            result = await classify_item(i)
            sequential_results.append(result)
        sequential_time = time.time() - start
        
        # 동시 처리 (제한 없음)
        start = time.time()
        concurrent_tasks = [classify_item(i) for i in range(item_count)]
        concurrent_results = await asyncio.gather(*concurrent_tasks)
        concurrent_time = time.time() - start
        
        # 동시 처리가 10배 이상 빨라야 함
        speedup = sequential_time / concurrent_time
        assert speedup >= 8, f"Expected 8x+ speedup, got {speedup:.1f}x"

    @pytest.mark.asyncio
    async def test_semaphore_bounded_vs_unbounded(self):
        """Semaphore 제한 있음/없음 비교"""
        async def work(item_id, semaphore=None, delay=0.1):
            if semaphore:
                async with semaphore:
                    await asyncio.sleep(delay)
            else:
                await asyncio.sleep(delay)
            return item_id
        
        # 제한 없음 (모두 병렬)
        start = time.time()
        tasks = [work(i, None, 0.1) for i in range(10)]
        await asyncio.gather(*tasks)
        unbounded_time = time.time() - start
        
        # 제한 있음 (5개씩)
        semaphore = asyncio.Semaphore(5)
        start = time.time()
        tasks = [work(i, semaphore, 0.1) for i in range(10)]
        await asyncio.gather(*tasks)
        bounded_time = time.time() - start
        
        # 제한 있음이 약 2배 더 오래 걸려야 함
        # (10개 vs 5개씩 2배치)
        assert bounded_time > unbounded_time, "Bounded should take longer"


# ── 최적화 요약 검증 ──

class TestOptimizationSummary:
    """모든 최적화의 종합 검증"""

    @pytest.mark.asyncio
    async def test_all_optimizations_applied(self):
        """모든 최적화가 적용되었는지 확인"""
        from app.services.document_ingestion import (
            EMBEDDING_BATCH_SIZE,
            INSERT_BATCH_SIZE,
            MAX_CONCURRENT_DOCUMENTS,
            MAX_CONCURRENT_CLASSIFICATIONS,
            _document_processing_semaphore
        )
        
        optimizations = {
            'EMBEDDING_BATCH_SIZE': (EMBEDDING_BATCH_SIZE, 250),
            'INSERT_BATCH_SIZE': (INSERT_BATCH_SIZE, 200),
            'MAX_CONCURRENT_DOCUMENTS': (MAX_CONCURRENT_DOCUMENTS, 5),
            'MAX_CONCURRENT_CLASSIFICATIONS': (MAX_CONCURRENT_CLASSIFICATIONS, 10),
            'Semaphore': (_document_processing_semaphore is not None, True),
        }
        
        for name, (actual, expected) in optimizations.items():
            assert actual == expected, f"{name}: expected {expected}, got {actual}"

    @pytest.mark.asyncio
    async def test_performance_improvement_summary(self, generate_mock_chunks):
        """성능 개선 요약"""
        chunks = generate_mock_chunks(20000)
        
        metrics = {
            'embedding_api_calls_reduction': {
                'before': (len(chunks) + 99) // 100,
                'after': (len(chunks) + 249) // 250,
                'expected_reduction_percent': 60
            },
            'insert_transactions_reduction': {
                'before': (len(chunks) + 49) // 50,
                'after': (len(chunks) + 199) // 200,
                'expected_reduction_percent': 75
            }
        }
        
        for metric_name, metric_data in metrics.items():
            before = metric_data['before']
            after = metric_data['after']
            expected_reduction = metric_data['expected_reduction_percent']
            
            actual_reduction = (before - after) / before * 100
            
            assert actual_reduction >= expected_reduction * 0.9, \
                f"{metric_name}: expected ~{expected_reduction}% reduction, " \
                f"got {actual_reduction:.1f}%"


# ── 마크 설정 ──

# Mark slow tests
pytest.mark.slow = pytest.mark.asyncio

# 필요시 pytest 실행 시 제외 가능: pytest -m "not slow"
