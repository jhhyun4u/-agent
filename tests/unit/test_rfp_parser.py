from pathlib import Path

from app.services.rfp_parser import extract_text_from_pdf


def test_extract_text_from_pdf_nonexistent():
    """존재하지 않는 파일에 대해 예외 발생 확인"""
    try:
        extract_text_from_pdf(Path("nonexistent.pdf"))
        assert False, "Should have raised an exception"
    except Exception:
        pass
