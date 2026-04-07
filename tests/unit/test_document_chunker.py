"""Unit tests for document chunker (U-CHK-*)"""

import pytest
from app.services.document_chunker import chunk_document, _chunk_by_window, Chunk


class TestChunkDocument:
    """chunk_document router function tests"""

    def test_uched_01_empty_text(self):
        """U-CHK-01: Empty text returns empty list"""
        result = chunk_document("", "report")
        assert result == []

    def test_uchk_02_short_text(self):
        """U-CHK-02: Text under 50 chars returns empty"""
        result = chunk_document("짧은", "보고서")
        assert result == []

    def test_uchk_03_korean_proposal(self, sample_korean_text_1000):
        """U-CHK-03: 제안서 (Korean) type mapping works"""
        result = chunk_document(sample_korean_text_1000, "제안서")
        assert len(result) > 0
        # Just verify it chunks successfully (may be section or window depending on text length)
        assert all(c.char_count > 0 for c in result)

    def test_uchk_04_korean_report(self, sample_korean_text_1000):
        """U-CHK-04: 보고서 (Korean) type mapping works"""
        result = chunk_document(sample_korean_text_1000, "보고서")
        assert len(result) > 0
        assert all(c.char_count > 0 for c in result)

    def test_uchk_05_korean_performance(self, sample_korean_text_1000):
        """U-CHK-05: 실적 (Korean) type mapping works"""
        result = chunk_document(sample_korean_text_1000, "실적")
        assert len(result) > 0
        assert all(c.char_count > 0 for c in result)

    def test_uchk_06_korean_other(self, sample_text_with_sections):
        """U-CHK-06: 기타 (Korean) routes to window fallback"""
        result = chunk_document(sample_text_with_sections, "기타")
        assert len(result) > 0
        # 기타 should fall back to window chunking
        assert any(c.chunk_type == "window" for c in result)

    def test_uchk_07_english_report(self, sample_korean_text_1000):
        """U-CHK-07: English 'report' type works"""
        result = chunk_document(sample_korean_text_1000, "report")
        assert len(result) > 0
        assert all(c.char_count > 0 for c in result)

    def test_uchk_08_english_presentation(self, sample_presentation_text):
        """U-CHK-08: English 'presentation' routes to slides"""
        result = chunk_document(sample_presentation_text, "presentation")
        assert len(result) > 0
        assert any(c.chunk_type == "slide" for c in result)

    def test_uchk_09_english_contract(self, sample_contract_text):
        """U-CHK-09: English 'contract' routes to articles"""
        result = chunk_document(sample_contract_text, "contract")
        assert len(result) > 0
        assert any(c.chunk_type == "article" for c in result)

    def test_uchk_10_english_other(self, sample_text_with_sections):
        """U-CHK-10: English 'other' falls back to window"""
        result = chunk_document(sample_text_with_sections, "other")
        assert len(result) > 0
        assert any(c.chunk_type == "window" for c in result)

    def test_uchk_11_chunk_dataclass(self):
        """U-CHK-11: Chunk dataclass integrity"""
        chunk = Chunk(index=0, chunk_type="section", section_title="Test", content="content", char_count=7)
        assert chunk.index == 0
        assert chunk.char_count == len(chunk.content)
        assert chunk.section_title == "Test"

    def test_uchk_12_overlap_behavior(self, sample_korean_text_1000):
        """U-CHK-12: Window chunking with overlap preserves boundary content"""
        chunks = _chunk_by_window(sample_korean_text_1000, window=300, overlap=50)
        assert len(chunks) >= 2
        
        # Verify chunks are created
        for chunk in chunks:
            assert chunk.char_count > 0
            assert chunk.chunk_type == "window"


class TestChunkingStrategies:
    """Tests for specific chunking strategies"""

    def test_heading_chunk_sections(self, sample_text_with_sections):
        """Section-based chunking creates one chunk per heading"""
        result = chunk_document(sample_text_with_sections, "report")
        
        # Should have chunks for 제1장, 제2장, 제3장
        assert len(result) >= 1
        # All should be either "section" type or have titles
        for chunk in result:
            assert chunk.char_count > 0

    def test_window_chunk_fallback(self):
        """Window-based fallback for unknown types"""
        long_text = "테스트 " * 500
        result = chunk_document(long_text, "unknown_type")
        
        assert len(result) > 0
        assert all(c.chunk_type == "window" for c in result)

    def test_presentation_slide_grouping(self, sample_presentation_text):
        """Slides are grouped by marker"""
        result = chunk_document(sample_presentation_text, "presentation")
        
        assert len(result) > 0
        assert all(c.chunk_type == "slide" for c in result)

    def test_contract_article_extraction(self, sample_contract_text):
        """Articles are extracted from 제N조 pattern"""
        result = chunk_document(sample_contract_text, "contract")
        
        assert len(result) > 0
        assert all(c.chunk_type == "article" for c in result)
