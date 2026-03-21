"""
공고별 최적 제안팀 추천 모듈

3-시그널 스코어링 (100점 만점):
  1. 전문분야 키워드 매칭 (50점)
  2. 실적 기반 친화도 (30점)
  3. 사업영역 도메인 정렬 (20점)

사용법:
    # 모듈로 임포트
    from scripts.team_recommender import TeamRecommender
    recommender = TeamRecommender()
    results = recommender.recommend("바이오빅데이터 활용 AI 기반 신규사업 기획")

    # CLI 단독 테스트
    uv run python scripts/team_recommender.py "바이오빅데이터 활용 AI 기반 신규사업 기획"
    uv run python scripts/team_recommender.py "사무용품 구매"  # 매칭 없는 경우
"""

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEAM_PATH = PROJECT_ROOT / "data" / "team_structure.json"
PROFILE_PATH = PROJECT_ROOT / "data" / "company_profile.json"


# ── 도메인 분류 키워드 ──────────────────────────

DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "R&D Nexus": {
        "기획연구", "성과분석", "연구개발", "기술개발", "예비타당성", "로드맵", "중장기",
        "바이오", "정밀의료", "재생의료", "건강관리", "임상시험", "신약",
        "바이오빅데이터", "바이오헬스", "감염병", "의료기기", "정신건강",
        "마약류", "고령친화", "만성질환", "동향조사",
        "탄소", "에너지", "원자력", "우주", "해양", "양자", "반도체", "소재",
        "로봇", "국방", "안보", "과학기술", "R&D", "기초과학", "표준화",
        "기후변화", "탄소중립", "환경신기술", "국토교통", "재난안전",
        "과학기술인재", "신산업정책", "AI안전", "탄소소재",
    },
    "AI Transformation": {
        "AI", "빅데이터", "디지털", "ICT", "SW", "자동화", "데이터",
        "디지털전환", "플랫폼", "스마트시티", "스마트팩토리", "스마트",
        "클라우드", "메타버스", "블록체인", "사이버", "정보보안",
        "AI시티", "AI빅데이터", "피지컬AI", "필수의료", "예타기획",
        "AI업무자동화", "AI 교육훈련", "AI교육훈련", "AX컨설팅",
    },
    "T2B & Regional Innovation": {
        "기술사업화", "벤처", "스케일업", "지역혁신", "클러스터",
        "환경", "공공", "전자정부", "도시재생",
        "기술이전", "투자", "특허", "창업", "중소기업", "지역균형",
        "사업화", "기술가치", "스타트업",
        "스케일업팁스", "벤처성장지원", "딥테크챌린지", "PMO",
        "토양지하수", "환경보험", "유해물질", "자율제조",
    },
    "Future Workforce": {
        "교육", "인재", "코칭", "컨설팅", "역량강화", "인력양성",
        "직업훈련", "HRD", "연수", "미래인재", "AI교육",
        "AI교육훈련", "AX컨설팅",
    },
}

# 도메인 → 소속 팀이 가산점을 받는 본부 매핑
DOMAIN_DIVISION_MAP: dict[str, list[str]] = {
    "R&D Nexus": ["혁신전략본부"],
    "AI Transformation": ["버티컬AX본부", "AX허브연구소"],
    "T2B & Regional Innovation": ["기술사업화본부", "공공AX본부"],
    "Future Workforce": ["AX허브연구소"],
}


@dataclass
class TeamRecommendation:
    team_name: str
    division: str
    score: int = 0
    score_detail: dict = field(default_factory=dict)
    matched_keywords: list[str] = field(default_factory=list)
    confidence: str = "낮음"
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_pipeline_dict(self) -> dict:
        """bid_pipeline.json 저장용 경량 딕셔너리."""
        return {
            "team": self.team_name,
            "score": self.score,
            "keywords": self.matched_keywords[:5],
            "reason": self.reason,
        }


class TeamRecommender:
    """공고 제목 기반 최적 팀 추천."""

    def __init__(self, team_path: str | Path | None = None, profile_path: str | Path | None = None):
        self.team_path = Path(team_path) if team_path else TEAM_PATH
        self.profile_path = Path(profile_path) if profile_path else PROFILE_PATH
        self._team_data: dict | None = None
        self._profile: dict | None = None

    @property
    def team_data(self) -> dict:
        if self._team_data is None:
            if not self.team_path.exists():
                raise FileNotFoundError(f"팀 구조 파일 없음: {self.team_path}")
            with open(self.team_path, encoding="utf-8") as f:
                self._team_data = json.load(f)
        return self._team_data

    @property
    def profile(self) -> dict | None:
        if self._profile is None and self.profile_path.exists():
            with open(self.profile_path, encoding="utf-8") as f:
                self._profile = json.load(f)
        return self._profile

    def classify_domain(self, title: str) -> tuple[str, int]:
        """공고 제목 → 사업영역 분류 + 매칭 키워드 수."""
        best_domain = ""
        best_count = 0
        for domain, keywords in DOMAIN_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in title)
            if count > best_count:
                best_count = count
                best_domain = domain
        return best_domain, best_count

    def _score_specialization(self, title: str, team: dict) -> tuple[float, list[str]]:
        """시그널 1: 전문분야 키워드 매칭 (50점).

        가중치:
          - 전문분야 키워드가 제목에 정확 포함 (1.0점)
          - 제목 단어(3자 이상)가 전문분야에 포함 (0.5점)
        """
        matched = []
        weighted_hits = 0.0
        title_words = [w for w in title.split() if len(w) >= 2]

        for spec in team["specializations"]:
            # 1) 전문분야 키워드가 제목 문자열에 정확 포함 (강한 매칭)
            if spec in title:
                matched.append(spec)
                weighted_hits += 1.0
                continue
            # 2) 제목 단어(3자 이상)가 전문분야에 부분 포함 (약한 매칭)
            for word in title_words:
                if len(word) >= 3 and word in spec:
                    matched.append(spec)
                    weighted_hits += 0.5
                    break

        if not matched:
            return 0.0, matched

        score = min(weighted_hits / 2.0, 1.0) * 50
        return score, matched

    def _score_track_record(self, title: str, team: dict, client: str = "") -> float:
        """시그널 2: 실적 기반 친화도 (30점)."""
        profile = self.profile
        if not profile or "track_records" not in profile:
            return 0.0

        team_specs = set(team["specializations"])
        total_affinity = 0.0

        for record in profile["track_records"]:
            record_title = record.get("title", "")
            record_keywords = set(record.get("keywords", []))
            record_client = record.get("client", "")

            # 공고와 실적의 유사도 (제목 단어 겹침)
            title_words = set(w for w in title.split() if len(w) >= 2)
            record_words = set(w for w in record_title.split() if len(w) >= 2)
            title_overlap = len(title_words & record_words)

            if title_overlap == 0:
                # 키워드 레벨 매칭
                kw_overlap = len(title_words & record_keywords)
                if kw_overlap == 0:
                    continue
                title_overlap = kw_overlap * 0.5

            # 이 실적의 키워드가 팀 전문분야와 얼마나 겹치는지
            spec_overlap = len(record_keywords & team_specs)
            if spec_overlap == 0:
                # 부분 문자열 매칭 시도
                for kw in record_keywords:
                    for spec in team_specs:
                        if kw in spec or spec in kw:
                            spec_overlap += 0.5
                            break

            if spec_overlap > 0:
                affinity = min(title_overlap, 3) * min(spec_overlap, 3)
                # 발주처 보너스
                if client and (client in record_client or record_client in client):
                    affinity *= 1.5
                total_affinity += affinity

        return min(total_affinity / 3.0, 30.0)

    def _score_domain(self, domain: str, team: dict) -> float:
        """시그널 3: 사업영역 도메인 정렬 (20점)."""
        if not domain:
            return 0.0

        preferred_divisions = DOMAIN_DIVISION_MAP.get(domain, [])
        if team["division"] in preferred_divisions:
            return 20.0

        # 부분 점수: 같은 도메인에 속하지 않지만 전문분야에 관련 키워드가 있으면
        domain_kws = DOMAIN_KEYWORDS.get(domain, set())
        team_specs = set(team["specializations"])
        overlap = len(domain_kws & team_specs)
        if overlap > 0:
            return min(overlap * 5.0, 10.0)

        return 0.0

    def _confidence(self, score: int) -> str:
        if score >= 60:
            return "높음"
        elif score >= 35:
            return "보통"
        return "낮음"

    def _build_reason(self, team: dict, matched_kw: list[str], domain: str) -> str:
        """추천 사유 생성."""
        parts = []
        if matched_kw:
            kw_str = "·".join(matched_kw[:3])
            parts.append(f"{kw_str} 전문")
        if domain:
            parts.append(f"{domain} 영역")

        profile = self.profile
        if profile and "track_records" in profile:
            team_specs = set(team["specializations"])
            related_count = 0
            for r in profile["track_records"]:
                rkw = set(r.get("keywords", []))
                if rkw & team_specs:
                    related_count += 1
            if related_count > 0:
                parts.append(f"관련 실적 {related_count}건")

        return ", ".join(parts) if parts else "일반"

    def recommend(self, title: str, client: str = "", top_n: int = 3) -> tuple[list[TeamRecommendation], str]:
        """
        공고 제목으로 팀 추천.

        Returns:
            (추천 리스트, 분류된 도메인)
        """
        teams = self.team_data.get("teams", [])
        domain, _ = self.classify_domain(title)

        results: list[TeamRecommendation] = []

        for team in teams:
            spec_score, matched_kw = self._score_specialization(title, team)
            track_score = self._score_track_record(title, team, client)
            domain_score = self._score_domain(domain, team)

            total = round(spec_score + track_score + domain_score)

            rec = TeamRecommendation(
                team_name=team["name"],
                division=team["division"],
                score=total,
                score_detail={
                    "specialization": round(spec_score, 1),
                    "track_record": round(track_score, 1),
                    "domain": round(domain_score, 1),
                },
                matched_keywords=matched_kw,
                confidence=self._confidence(total),
                reason=self._build_reason(team, matched_kw, domain),
            )
            results.append(rec)

        # 스코어 내림차순 정렬
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:top_n], domain


# ── CLI ────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("사용법: uv run python scripts/team_recommender.py \"공고 제목\"")
        print("  예: uv run python scripts/team_recommender.py \"바이오빅데이터 활용 AI 기반 신규사업 기획\"")
        sys.exit(1)

    title = sys.argv[1]
    client = sys.argv[2] if len(sys.argv) > 2 else ""

    try:
        recommender = TeamRecommender()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print("먼저 import_team_structure.py를 실행하세요.")
        sys.exit(1)

    results, domain = recommender.recommend(title, client)

    print(f"\n━━━ 팀 추천 결과 ━━━")
    print(f"공고: {title}")
    if client:
        print(f"발주처: {client}")
    print(f"도메인: {domain or '미분류'}\n")

    if not results or results[0].score == 0:
        print("  추천팀 없음 (수동 배정 필요)")
        return

    for i, rec in enumerate(results):
        if rec.score == 0:
            break
        marker = "→" if i == 0 else " "
        kw_str = ", ".join(rec.matched_keywords[:5]) if rec.matched_keywords else "-"
        print(f"  {marker} {rec.team_name}({rec.score}점, {rec.confidence}): {rec.reason}")
        print(f"    키워드: {kw_str}")
        print(f"    세부: 전문분야 {rec.score_detail['specialization']}점 + "
              f"실적 {rec.score_detail['track_record']}점 + "
              f"도메인 {rec.score_detail['domain']}점")
        print()


if __name__ == "__main__":
    main()
