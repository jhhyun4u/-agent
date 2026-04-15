"""
Vault Citation Service - Format and validate source citations in LLM responses
Module-2: A.3 Citation Improvements
Design Ref: §A.3, §6.1
"""

import re
import logging
from typing import List, Tuple, Optional
from app.models.vault_schemas import DocumentSource

logger = logging.getLogger(__name__)


class VaultCitationService:
    """Manage citation formatting and validation in LLM responses"""

    CITATION_PATTERN = r'\[출처\s+(\d+)\]'  # Match [출처 N] format
    INVALID_CITATION_PATTERN = r'(?<!\[)\[출처[^\]]*\](?!\w)'  # Detect malformed citations

    @staticmethod
    def inject_citation_instructions(system_prompt: str, source_count: int) -> str:
        """
        Inject citation format instructions into system prompt.

        Design Ref: §A.3 — Citation instructions for LLM

        Args:
            system_prompt: Base system prompt
            source_count: Number of sources provided

        Returns:
            Enhanced system prompt with citation instructions
        """
        if source_count == 0:
            return system_prompt

        citation_section = f"""
### 출처 인용 방식
응답에서 각 주장의 근거가 된 출처를 [출처 N] 형식으로 표시하세요.
- N은 1부터 {source_count}까지의 정수입니다
- 출처 번호는 아래 제공된 문서 목록의 순서와 일치합니다
- 같은 출처를 여러 번 인용할 수 있습니다: [출처 1], [출처 2]

**주의**: 인용 없이 주장하지 마세요. 모든 구체적인 내용은 출처를 명시하세요.

### 제공된 출처
"""
        return system_prompt + citation_section

    @staticmethod
    def parse_citations(text: str) -> Tuple[str, List[int]]:
        """
        Extract citation indices from LLM response.

        Design Ref: §A.3 — Parse [출처 N] markers from response

        Args:
            text: LLM response text

        Returns:
            Tuple of (cleaned_text, citation_indices)
            - cleaned_text: original text with citations preserved
            - citation_indices: sorted list of unique source indices (1-based)
        """
        if not text:
            return text, []

        # Find all citations in format [출처 N]
        matches = re.findall(VaultCitationService.CITATION_PATTERN, text)

        # Extract unique indices (1-based)
        citation_indices = sorted(set(int(m) for m in matches))

        return text, citation_indices

    @staticmethod
    def validate_citations(
        text: str,
        sources: List[DocumentSource],
        strict: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that citations match sources.

        Design Ref: §A.3 — Validate citation indices

        Args:
            text: LLM response text
            sources: List of provided sources
            strict: If True, fail if text has zero citations

        Returns:
            Tuple of (is_valid, error_message)
        """
        source_count = len(sources)

        if source_count == 0:
            # No sources provided - citations should not be present
            _, indices = VaultCitationService.parse_citations(text)
            if indices:
                return False, "응답에 출처가 명시되었지만 제공된 출처가 없습니다"
            return True, None

        # Parse citations from text
        _, citation_indices = VaultCitationService.parse_citations(text)

        # Check if all cited indices are within valid range
        max_index = max(citation_indices) if citation_indices else 0
        if max_index > source_count:
            return (
                False,
                f"유효하지 않은 출처 번호: [출처 {max_index}] (총 {source_count}개 출처만 제공됨)"
            )

        # Check if response has citations (optional unless strict mode)
        if strict and not citation_indices:
            return False, "응답에 출처가 명시되지 않았습니다"

        return True, None

    @staticmethod
    def build_source_reference_section(sources: List[DocumentSource]) -> str:
        """
        Build formatted source reference section for prompt.

        Design Ref: §A.3 — Source list for citation context

        Args:
            sources: List of sources

        Returns:
            Formatted section with numbered sources
        """
        if not sources:
            return ""

        lines = ["## 출처 목록"]
        for i, source in enumerate(sources, 1):
            # Format: [1] Title (Section)
            section_str = f"({source.section.value})" if source.section else ""
            lines.append(f"[{i}] {source.title} {section_str}")
            if source.document_id:
                lines.append(f"    ID: {source.document_id}")
            if hasattr(source, 'confidence') and source.confidence:
                lines.append(f"    신뢰도: {source.confidence:.1%}")

        return "\n".join(lines)

    @staticmethod
    def enhance_with_source_context(
        sources: List[DocumentSource],
        injection_point: str = "sources_context"
    ) -> dict:
        """
        Prepare source context for injection into prompts.

        Design Ref: §A.3 — Source context preparation

        Args:
            sources: List of sources
            injection_point: Where in prompt to inject (sources_context or system_prompt)

        Returns:
            Dict with formatted source reference section and count
        """
        return {
            "source_count": len(sources),
            "source_reference": VaultCitationService.build_source_reference_section(sources),
            "injection_point": injection_point,
            "sources": sources
        }

    @staticmethod
    def format_response_with_citations(
        text: str,
        sources: List[DocumentSource],
        validate: bool = True
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Validate and format response with citations.

        Design Ref: §A.3 — Complete citation processing

        Args:
            text: LLM response
            sources: Provided sources
            validate: Whether to validate citations

        Returns:
            Tuple of (formatted_text, is_valid, error_message)
        """
        if not validate:
            return text, True, None

        is_valid, error = VaultCitationService.validate_citations(text, sources, strict=False)

        if not is_valid:
            logger.warning(f"Citation validation failed: {error}")
            return text, False, error

        return text, True, None
