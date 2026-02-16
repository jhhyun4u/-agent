"""파일 처리 관련 유틸리티"""

import logging
from pathlib import Path
from typing import Union

from PyPDF2 import PdfReader

from app.config import settings
from app.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


def validate_file_type(filename: str) -> bool:
    """
    파일 확장자 검증

    Args:
        filename: 파일명

    Returns:
        허용된 파일 타입이면 True
    """
    suffix = Path(filename).suffix.lower()
    return suffix in settings.allowed_file_extensions


def extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    """
    PDF 파일에서 텍스트 추출

    Args:
        file_path: PDF 파일 경로

    Returns:
        추출된 텍스트

    Raises:
        FileProcessingError: PDF 읽기 실패 시
    """
    try:
        reader = PdfReader(str(file_path))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF 텍스트 추출 실패: {e}")
        raise FileProcessingError(
            f"PDF 파일을 읽을 수 없습니다: {file_path}",
            details={"path": str(file_path), "error": str(e)}
        )


def extract_text_from_docx(file_path: Union[str, Path]) -> str:
    """
    DOCX 파일에서 텍스트 추출

    Args:
        file_path: DOCX 파일 경로

    Returns:
        추출된 텍스트

    Raises:
        FileProcessingError: DOCX 읽기 실패 시
    """
    try:
        from docx import Document

        doc = Document(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error(f"DOCX 텍스트 추출 실패: {e}")
        raise FileProcessingError(
            f"DOCX 파일을 읽을 수 없습니다: {file_path}",
            details={"path": str(file_path), "error": str(e)}
        )


def extract_text_from_file(file_path: Union[str, Path]) -> str:
    """
    파일에서 텍스트 추출 (통합 함수)

    Args:
        file_path: 파일 경로

    Returns:
        추출된 텍스트

    Raises:
        FileProcessingError: 파일 읽기 실패 또는 지원하지 않는 형식
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileProcessingError(
            f"파일을 찾을 수 없습니다: {file_path}",
            details={"path": str(file_path)}
        )

    suffix = file_path.suffix.lower()

    try:
        if suffix == ".pdf":
            return extract_text_from_pdf(file_path)
        elif suffix == ".docx":
            return extract_text_from_docx(file_path)
        elif suffix == ".hwp":
            raise FileProcessingError(
                "HWP 파일 형식은 아직 지원되지 않습니다.",
                details={"path": str(file_path)}
            )
        elif suffix == ".txt":
            return file_path.read_text(encoding="utf-8")
        else:
            raise FileProcessingError(
                f"지원하지 않는 파일 형식입니다: {suffix}",
                details={"path": str(file_path), "suffix": suffix}
            )
    except FileProcessingError:
        raise
    except Exception as e:
        logger.error(f"파일 텍스트 추출 실패: {e}")
        raise FileProcessingError(
            f"파일을 읽는 중 오류가 발생했습니다: {file_path}",
            details={"path": str(file_path), "error": str(e)}
        )
