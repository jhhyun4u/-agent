"""
문서 관리 API - 성능 테스트

테스트 범위:
- 1000개 이상 문서 처리
- 응답 시간 측정
- 메모리 사용량 분석
- 병목 지점 식별
"""

import pytest
import asyncio
import time
import psutil
import os
from io import BytesIO
from datetime import datetime, timezone
from typing import List
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch


# ── 성능 테스트용 Fixture ──

@pytest.fixture
def process():
    """현재 프로세스"""
    return psutil.Process(os.getpid())


@pytest.fixture
def generate_mock_documents():
    """대규모 문서 데이터 생성"""
    def _generate(count: int) -> List[dict]:
        """count개의 모의 문서 생성"""
        documents = []
        for i in range(count):
            documents.append({
                "id": f"doc-{i:06d}",
                "org_id": "org-001",
                "filename": f"document_{i:06d}.pdf",
                "doc_type": ["제안서", "보고서", "실적"][i % 3],
                "processing_status": ["completed", "chunking", "failed"][i % 3],
                "total_chars": 5000 + (i * 100),
                "chunk_count": 10 + (i % 50),
                "created_at": "2026-04-08T00:00:00Z",
                "updated_at": "2026-04-08T00:00:00Z",
            })
        return documents
    return _generate


# ── 응답 시간 테스트 ──

@pytest.mark.asyncio
async def test_list_documents_small_dataset_response_time(client, mock_user):
    """작은 데이터셋 (20개) 목록 조회 응답 시간"""
    # Arrange
    documents = [
        {
            "id": f"doc-{i:03d}",
            "org_id": "org-001",
            "filename": f"doc_{i}.pdf",
            "processing_status": "completed",
            "created_at": "2026-04-08T00:00:00Z",
            "updated_at": "2026-04-08T00:00:00Z",
        }
        for i in range(20)
    ]

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=documents))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act - 응답 시간 측정
    start_time = time.time()
    response = await client.get("/api/documents", params={"limit": 20, "offset": 0})
    end_time = time.time()

    response_time = (end_time - start_time) * 1000  # ms

    # Assert - 응답 시간 < 200ms
    assert response.status_code == 200
    assert response_time < 200, f"Response time {response_time}ms exceeds 200ms limit"


@pytest.mark.asyncio
async def test_list_documents_large_dataset_response_time(client, mock_user, generate_mock_documents):
    """큰 데이터셋 (1000개) 목록 조회 응답 시간"""
    # Arrange
    documents = generate_mock_documents(1000)[:100]  # 페이지 크기만큼만

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=documents))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act - 응답 시간 측정
    start_time = time.time()
    response = await client.get(
        "/api/documents",
        params={"limit": 100, "offset": 0}
    )
    end_time = time.time()

    response_time = (end_time - start_time) * 1000  # ms

    # Assert - 응답 시간 < 500ms
    assert response.status_code == 200
    assert response_time < 500, f"Response time {response_time}ms exceeds 500ms limit"


@pytest.mark.asyncio
async def test_concurrent_list_requests(client, mock_user, generate_mock_documents):
    """동시 요청 처리 (10개 동시 요청)"""
    # Arrange
    documents = generate_mock_documents(100)

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=documents))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act - 10개 동시 요청
    start_time = time.time()

    async def make_request():
        return await client.get("/api/documents")

    tasks = [make_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    total_time = (end_time - start_time) * 1000

    # Assert
    successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
    assert successful >= 9, f"Only {successful}/10 requests succeeded"

    # 전체 응답 시간 < 2초 (10개 동시)
    assert total_time < 2000, f"Total time {total_time}ms exceeds 2000ms limit"


# ── 메모리 사용량 테스트 ──

@pytest.mark.asyncio
async def test_memory_usage_list_documents(client, mock_user, process, generate_mock_documents):
    """목록 조회 시 메모리 사용량"""
    # Arrange
    documents = generate_mock_documents(1000)

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=documents[:100]))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act - 메모리 기준선
    import gc
    gc.collect()
    memory_before = process.memory_info().rss / 1024 / 1024  # MB

    # 요청 실행
    for _ in range(5):
        response = await client.get("/api/documents")
        assert response.status_code == 200

    # 메모리 사용량 측정
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = memory_after - memory_before

    # Assert - 메모리 증가 < 50MB
    assert memory_increase < 50, f"Memory increase {memory_increase:.2f}MB exceeds 50MB limit"


# ── 처리량 테스트 ──

@pytest.mark.asyncio
async def test_throughput_sequential_operations(client, mock_user, generate_mock_documents):
    """순차 작업 처리량"""
    # Arrange
    documents = generate_mock_documents(100)

    supabase_mock = client._supabase_mock

    def create_query_builder():
        qb = MagicMock()
        qb.select = MagicMock(return_value=qb)
        qb.eq = MagicMock(return_value=qb)
        qb.order = MagicMock(return_value=qb)
        qb.range = MagicMock(return_value=qb)
        qb.execute = AsyncMock(return_value=MagicMock(data=documents))
        return qb

    supabase_mock.table = MagicMock(side_effect=lambda *args: create_query_builder())

    # Act - 100개 순차 요청
    start_time = time.time()
    request_count = 0

    for i in range(100):
        response = await client.get("/api/documents", params={"offset": i * 10})
        if response.status_code == 200:
            request_count += 1

    end_time = time.time()
    elapsed = end_time - start_time

    # Assert - 처리량 계산
    throughput = request_count / elapsed  # requests per second

    # 최소 처리량: 10 req/s
    assert throughput >= 10, f"Throughput {throughput:.2f} req/s is below 10 req/s minimum"


# ── 병목 지점 테스트 ──

@pytest.mark.asyncio
async def test_pagination_performance_deep_offset(client, mock_user, generate_mock_documents):
    """깊은 오프셋 (1000+) 성능"""
    # Arrange
    documents = generate_mock_documents(10)

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=documents))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act - 깊은 페이지 요청 (offset=100000)
    start_time = time.time()
    response = await client.get(
        "/api/documents",
        params={"limit": 20, "offset": 100000}
    )
    end_time = time.time()

    response_time = (end_time - start_time) * 1000

    # Assert
    assert response.status_code == 200
    # 오프셋이 커도 응답 시간 < 500ms
    assert response_time < 500, f"Deep offset response time {response_time}ms exceeds 500ms"


@pytest.mark.asyncio
async def test_search_performance_large_dataset(client, mock_user, generate_mock_documents):
    """검색 성능 (대규모 데이터셋)"""
    # Arrange
    documents = generate_mock_documents(500)

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.ilike = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    # 검색 결과는 더 적을 수 있음
    query_builder.execute = AsyncMock(return_value=MagicMock(data=documents[:50]))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act - 검색 성능 측정
    start_time = time.time()
    response = await client.get(
        "/api/documents",
        params={"search": "document_100"}
    )
    end_time = time.time()

    response_time = (end_time - start_time) * 1000

    # Assert - 검색 응답 시간 < 300ms
    assert response.status_code == 200
    assert response_time < 300, f"Search response time {response_time}ms exceeds 300ms"


# ── 스트레스 테스트 ──

@pytest.mark.asyncio
async def test_stress_high_concurrent_load(client, mock_user, generate_mock_documents):
    """스트레스 테스트 (50개 동시 요청)"""
    # Arrange
    documents = generate_mock_documents(50)

    supabase_mock = client._supabase_mock

    def create_query_builder():
        qb = MagicMock()
        qb.select = MagicMock(return_value=qb)
        qb.eq = MagicMock(return_value=qb)
        qb.order = MagicMock(return_value=qb)
        qb.range = MagicMock(return_value=qb)
        qb.execute = AsyncMock(return_value=MagicMock(data=documents))
        return qb

    supabase_mock.table = MagicMock(side_effect=lambda *args: create_query_builder())

    # Act - 50개 동시 요청
    async def make_request(offset: int):
        return await client.get("/api/documents", params={"offset": offset * 20})

    start_time = time.time()
    tasks = [make_request(i) for i in range(50)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()

    elapsed = (end_time - start_time) * 1000

    # Assert
    successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
    success_rate = (successful / len(responses)) * 100

    assert success_rate >= 90, f"Success rate {success_rate}% is below 90% threshold"
    # 50개 동시 요청 < 5초
    assert elapsed < 5000, f"Total time {elapsed}ms exceeds 5000ms limit"


# ── 캐싱 효율성 테스트 ──

@pytest.mark.asyncio
async def test_repeated_requests_caching(client, mock_user, generate_mock_documents):
    """반복 요청의 캐싱 효율성"""
    # Arrange
    documents = generate_mock_documents(100)

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=documents))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act - 첫 번째 요청
    start_time = time.time()
    response1 = await client.get("/api/documents?status=completed")
    time_first = (time.time() - start_time) * 1000

    # 두 번째 요청 (캐시되어야 함)
    start_time = time.time()
    response2 = await client.get("/api/documents?status=completed")
    time_second = (time.time() - start_time) * 1000

    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200

    # 두 번째 요청이 더 빨라야 함 (캐시 효율성)
    # 이상적으로는 두 번째가 50% 이상 빨라야 함
    if time_first > 50:  # 첫 번째가 충분히 길면
        efficiency = (time_first - time_second) / time_first
        # 캐시 효율성 > 0 (이상적으로는 > 50%)
        assert time_second <= time_first, "Second request should be faster (cached)"
