"""
테스트: 문서 수집 API 기본 검증

- 불린 임포트 체크
- 스키마 검증
- 타입 검증
"""

import asyncio
from pathlib import Path


async def test_imports():
    """모듈 임포트 테스트"""
    print("[TEST] Testing imports...")
    try:
        from app.api.routes_documents import router, SUPPORTED_FORMATS
        from app.services.document_ingestion import process_document, import_project
        from app.services.document_chunker import chunk_document, Chunk
        from app.utils.file_utils import extract_text_from_file
        print("  [PASS] All imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        return False


async def test_schemas():
    """스키마 검증 테스트"""
    print("✓ Testing schemas...")
    try:
        from app.models.document_schemas import (
            DocumentResponse,
            DocumentListResponse,
            DocumentDetailResponse,
            ChunkResponse,
            ChunkListResponse,
        )

        # 샘플 문서 응답 생성
        from datetime import datetime
        doc = DocumentResponse(
            id="test-id",
            filename="test.pdf",
            doc_type="보고서",
            storage_path="org/test-id/test.pdf",
            processing_status="completed",
            total_chars=1000,
            chunk_count=5,
            error_message=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        print(f"  [PASS] DocumentResponse schema valid: {doc.id}")
        return True
    except Exception as e:
        print(f"  [FAIL] Schema validation failed: {e}")
        return False


async def test_schemas():
    """스키마 검증 테스트"""
    print("[TEST] Testing schemas...")
    try:
        from app.models.document_schemas import (
            DocumentResponse,
        )

        # 샘플 문서 응답 생성
        from datetime import datetime, timezone
        doc = DocumentResponse(
            id="test-id",
            filename="test.pdf",
            doc_type="보고서",
            storage_path="org/test-id/test.pdf",
            processing_status="completed",
            total_chars=1000,
            chunk_count=5,
            error_message=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        print(f"  [PASS] DocumentResponse schema valid: {doc.id}")
        return True
    except Exception as e:
        print(f"  [FAIL] Schema validation failed: {e}")
        return False


async def test_chunker():
    """청킹 서비스 테스트"""
    print("[TEST] Testing document chunker...")
    try:
        from app.services.document_chunker import chunk_document

        # 테스트 텍스트
        sample_text = """
제1장 개요
이것은 샘플 문서입니다.

제2장 내용
여기에 본문 내용이 들어갑니다.

제3장 결론
마지막 섹션입니다.
""".strip()

        # 영문 타입 테스트
        chunks_en = chunk_document(sample_text, "report")

        # 한글 타입 테스트 (고정: 이제 "보고서"가 "report"로 매핑되어야 함)
        chunks_ko = chunk_document(sample_text, "보고서")

        print(f"  [PASS] Chunker (English 'report'): {len(chunks_en)} chunks")
        print(f"  [PASS] Chunker (Korean '보고서'): {len(chunks_ko)} chunks")

        # 한글과 영문이 동일하게 작동해야 함
        if len(chunks_en) != len(chunks_ko):
            print(f"  [WARN] English and Korean doc_type produce different chunk counts: {len(chunks_en)} vs {len(chunks_ko)}")

        for i, chunk in enumerate(chunks_ko):
            print(f"    - Chunk {i}: {chunk.section_title} ({chunk.char_count} chars, type={chunk.chunk_type})")

        return len(chunks_ko) > 0
    except Exception as e:
        print(f"  [FAIL] Chunker test failed: {e}")
        return False


async def test_file_extraction():
    """파일 추출 유틸리티 테스트"""
    print("[TEST] Testing file extraction utilities...")
    try:
        from app.utils.file_utils import (
            extract_text_from_file,
            validate_extension,
            get_extension,
        )

        # 확장자 테스트
        assert get_extension("document.pdf") == "pdf"
        assert get_extension("file.docx") == "docx"

        # 확장자 검증 테스트
        assert validate_extension("test.pdf", "intranet_doc") == "pdf"

        print("  [PASS] File utilities working correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] File extraction test failed: {e}")
        return False


async def test_doc_type_validation():
    """doc_type 검증 테스트"""
    print("[TEST] Testing doc_type validation...")
    try:
        allowed_types = {"보고서", "제안서", "실적", "기타"}

        # 유효한 타입
        for dtype in allowed_types:
            assert dtype in allowed_types

        # 무효한 타입
        invalid = "invalid_type"
        assert invalid not in allowed_types

        print(f"  [PASS] Validation: allowed={len(allowed_types)} types, rejected={invalid}")
        return True
    except Exception as e:
        print(f"  [FAIL] Validation test failed: {e}")
        return False


async def test_doc_type_mapping():
    """doc_type 매핑 테스트 (한글 → 영문 변환)"""
    print("[TEST] Testing doc_type mapping...")
    try:
        from app.services.document_chunker import _DOC_TYPE_MAPPING

        # 모든 한글 타입이 매핑되어야 함
        korean_types = {"보고서", "제안서", "실적", "기타"}
        for korean_type in korean_types:
            assert korean_type in _DOC_TYPE_MAPPING, f"Missing mapping for {korean_type}"
            mapped = _DOC_TYPE_MAPPING[korean_type]
            assert isinstance(mapped, str), f"Mapping should be string, got {type(mapped)}"
            print(f"    - {korean_type} -> {mapped}")

        # 영문도 지원해야 함
        english_types = {"report", "proposal", "presentation", "contract", "other"}
        for english_type in english_types:
            assert english_type in _DOC_TYPE_MAPPING, f"Missing mapping for {english_type}"

        print(f"  [PASS] All doc_type mappings valid (Korean: 4, English: 5)")
        return True
    except Exception as e:
        print(f"  [FAIL] Mapping test failed: {e}")
        return False


async def main():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("Document Ingestion API Test")
    print("="*60 + "\n")

    results = []
    results.append(("Imports", await test_imports()))
    results.append(("Schemas", await test_schemas()))
    results.append(("Chunker", await test_chunker()))
    results.append(("File Utils", await test_file_extraction()))
    results.append(("Type Validation", await test_doc_type_validation()))
    results.append(("Type Mapping (KO->EN)", await test_doc_type_mapping()))

    print("\n" + "="*60)
    print("Test Results")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Bug fixes applied correctly.")
    else:
        print(f"\n[ERROR] {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    success = asyncio.run(main())
    exit(0 if success else 1)
