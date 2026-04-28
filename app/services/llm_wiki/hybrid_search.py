"""LLM-Wiki HybridSearch — Sprint 1에서 실제 구현 예정. 현재 스텁."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class WikiSearchResult:
    section_id: str = ""
    title: str = ""
    content: str = ""
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    rank: int = 0
    final_score: float = 0.0


class HybridSearch:
    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    async def search(self, query: str, org_id: str, top_k: int = 5) -> List[WikiSearchResult]:
        return []
