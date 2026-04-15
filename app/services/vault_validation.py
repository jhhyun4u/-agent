"""
Vault Validation Engine - 3-Point Hallucination Prevention Gate
Validates AI responses before returning to users
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from app.models.vault_schemas import DocumentSource, ChatMessage

logger = logging.getLogger(__name__)


class HallucinationValidator:
    """
    3-Point Validation Gate for preventing hallucinations
    
    Point 1: Source Coherence
        - Does response text match cited sources?
        - Are all claims supported by sources?
        
    Point 2: Fact Alignment
        - Does response match SQL database facts?
        - Are there contradictions with verified data?
        
    Point 3: Confidence Threshold
        - Is overall confidence >= 80%?
        - Should response be delivered or flagged for review?
    """
    
    # Minimum confidence thresholds
    MIN_CONFIDENCE_FOR_DELIVERY = 0.80
    MIN_CONFIDENCE_FOR_WARNING = 0.60
    
    @staticmethod
    async def validate(
        response: str,
        sources: List[DocumentSource],
        confidence: float,
        source_texts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run 3-point validation on response
        
        Args:
            response: AI-generated response text
            sources: List of cited sources
            confidence: Confidence score (0-1)
            source_texts: Actual text from sources (for coherence check)
            
        Returns:
            ValidationReport with pass/fail and details
        """
        
        try:
            # Point 1: Source Coherence
            coherence_score = await HallucinationValidator._check_source_coherence(
                response, sources, source_texts or []
            )
            
            # Point 2: Fact Alignment
            alignment_score = await HallucinationValidator._check_fact_alignment(
                response, sources
            )
            
            # Point 3: Confidence Threshold
            meets_threshold = confidence >= HallucinationValidator.MIN_CONFIDENCE_FOR_DELIVERY
            
            # Overall validation
            validation_passed = (
                coherence_score >= 0.75  # Point 1
                and alignment_score >= 0.75  # Point 2
                and meets_threshold  # Point 3
            )
            
            # Final confidence (weighted average of 3 points)
            final_confidence = (coherence_score + alignment_score + (1.0 if meets_threshold else 0.0)) / 3
            
            return {
                "passed": validation_passed,
                "confidence": final_confidence,
                "source_coherence_score": coherence_score,
                "fact_alignment_score": alignment_score,
                "threshold_met": meets_threshold,
                "warnings": HallucinationValidator._generate_warnings(
                    validation_passed, 
                    coherence_score, 
                    alignment_score, 
                    confidence
                ),
                "action": (
                    "deliver" if validation_passed 
                    else ("warn" if final_confidence >= HallucinationValidator.MIN_CONFIDENCE_FOR_WARNING 
                          else "block")
                )
            }
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            # Fail closed (block suspicious responses)
            return {
                "passed": False,
                "confidence": 0.0,
                "error": str(e),
                "action": "block"
            }
    
    @staticmethod
    async def _check_source_coherence(
        response: str,
        sources: List[DocumentSource],
        source_texts: List[str]
    ) -> float:
        """
        Point 1: Source Coherence
        
        Check if response claims are directly supported by source texts
        - Extract claims from response
        - For each claim, verify it appears in source text
        - Calculate coherence as % of claims supported
        """
        
        try:
            if not sources or not source_texts:
                # No sources cited = unverifiable = low coherence
                return 0.3
            
            # Simple heuristic: check if response text contains key phrases from sources
            response_lower = response.lower()
            source_text_combined = " ".join(source_texts).lower()
            
            # Find key phrases (>4 chars) from sources in response
            key_phrases = [
                phrase for phrase in source_text_combined.split()
                if len(phrase) > 4
            ]
            
            if not key_phrases:
                return 0.5
            
            # Count how many key phrases appear in response
            matched_phrases = sum(
                1 for phrase in key_phrases
                if phrase in response_lower
            )
            
            coherence = matched_phrases / len(key_phrases)
            
            logger.debug(f"Source coherence: {matched_phrases}/{len(key_phrases)} phrases matched")
            
            return min(1.0, coherence)
            
        except Exception as e:
            logger.warning(f"Error checking source coherence: {str(e)}")
            return 0.5
    
    @staticmethod
    async def _check_fact_alignment(
        response: str,
        sources: List[DocumentSource]
    ) -> float:
        """
        Point 2: Fact Alignment
        
        Check if response contradicts verified database facts
        - Extract specific claims (numbers, dates, names)
        - Verify against source metadata
        - Flag contradictions
        """
        
        try:
            if not sources:
                return 0.5  # Unknown alignment without sources
            
            # Check for obvious contradictions
            contradictions = 0
            total_checks = 0
            
            for source in sources:
                if not source.metadata or not source.confidence:
                    continue
                
                total_checks += 1
                
                # High-confidence source: verify facts don't contradict
                if source.confidence >= 0.95:
                    # Extract numbers from response and source
                    response_numbers = HallucinationValidator._extract_numbers(response)
                    source_snippet = source.snippet or ""
                    source_numbers = HallucinationValidator._extract_numbers(source_snippet)
                    
                    # Simple check: if source has specific number, response shouldn't contradict it
                    if source_numbers and response_numbers:
                        for num in source_numbers:
                            if num not in response_numbers:
                                # Source says X but response doesn't mention it
                                contradictions += 1
            
            if total_checks == 0:
                return 0.7  # No high-confidence sources to check
            
            alignment = 1.0 - (contradictions / total_checks)
            logger.debug(f"Fact alignment: {contradictions}/{total_checks} contradictions found")
            
            return alignment
            
        except Exception as e:
            logger.warning(f"Error checking fact alignment: {str(e)}")
            return 0.5
    
    @staticmethod
    def _extract_numbers(text: str) -> List[float]:
        """Extract numerical values from text"""
        
        import re
        
        # Find patterns like "123", "1,234", "1.5M", "50%"
        pattern = r'\d+(?:,\d+)*(?:\.\d+)?(?:[MKB%]?)'
        matches = re.findall(pattern, text.lower())
        
        numbers = []
        for match in matches:
            try:
                # Remove commas and convert
                clean = match.replace(",", "")
                if clean.endswith("m"):
                    numbers.append(float(clean[:-1]) * 1_000_000)
                elif clean.endswith("k"):
                    numbers.append(float(clean[:-1]) * 1_000)
                elif clean.endswith("b"):
                    numbers.append(float(clean[:-1]) * 1_000_000_000)
                elif clean.endswith("%"):
                    numbers.append(float(clean[:-1]))
                else:
                    numbers.append(float(clean))
            except ValueError:
                continue
        
        return numbers
    
    @staticmethod
    def _generate_warnings(
        validation_passed: bool,
        coherence: float,
        alignment: float,
        confidence: float
    ) -> List[str]:
        """Generate user-facing warnings"""
        
        warnings = []
        
        if coherence < 0.75:
            warnings.append("응답의 출처와 일치도가 낮습니다. 출처를 다시 확인하세요.")
        
        if alignment < 0.75:
            warnings.append("데이터베이스 정보와 일치하지 않을 수 있습니다. 확인 후 사용하세요.")
        
        if confidence < 0.8:
            warnings.append("신뢰도가 낮습니다. 정확한 정보는 관리자에게 문의하세요.")
        
        if not validation_passed:
            warnings.append("이 응답은 신뢰도가 낮아 검토가 필요합니다.")
        
        return warnings
    
    @staticmethod
    async def extract_citations(response: str) -> List[str]:
        """
        Extract citation markers from response
        Looks for patterns like [1], [source], (from source), etc.
        """
        
        import re
        
        citations = []
        
        # Pattern 1: [1], [2], etc.
        citations.extend(re.findall(r'\[\d+\]', response))
        
        # Pattern 2: [source name]
        citations.extend(re.findall(r'\[([^\]]+)\]', response))
        
        # Pattern 3: (from ...)
        citations.extend(re.findall(r'\(from ([^)]+)\)', response))
        
        return list(set(citations))  # Deduplicate
    
    @staticmethod
    async def check_hallucination_indicators(response: str) -> List[str]:
        """
        Check for common hallucination indicators
        Returns list of suspicious patterns found
        """
        
        indicators = []
        response_lower = response.lower()
        
        # Indicator 1: Vague language
        vague_phrases = [
            "아마도", "대략", "약", "정도", "가능성", "추정",
            "아마", "아마도", "maybe", "probably", "probably",
        ]
        
        for phrase in vague_phrases:
            if phrase in response_lower:
                indicators.append(f"Vague language: '{phrase}'")
                break
        
        # Indicator 2: Confidence flip (says high confidence but shows uncertainty)
        if "확신" in response and "?" in response:
            indicators.append("Mixed confidence signals")
        
        # Indicator 3: Invented data (specific numbers without attribution)
        import re
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*', response)
        if numbers and not any(f"[{i}]" in response for i in range(1, len(numbers) + 1)):
            indicators.append(f"Specific numbers without citation: {numbers}")
        
        return indicators
