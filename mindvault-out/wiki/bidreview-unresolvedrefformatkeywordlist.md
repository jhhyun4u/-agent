# bid_review & __unresolved__::ref::_format_keyword_list
Cohesion: 0.50 | Nodes: 5

## Key Nodes
- **bid_review** (C:\project\tenopa proposer\-agent-master\app\prompts\bid_review.py) -- 3 connections
  - -> contains -> [[formatkeywordlist]]
  - -> contains -> [[buildreviewersystem]]
  - -> contains -> [[buildunifiedanalysissystem]]
- **__unresolved__::ref::_format_keyword_list** () -- 2 connections
  - <- calls <- [[buildreviewersystem]]
  - <- calls <- [[buildunifiedanalysissystem]]
- **_format_keyword_list** (C:\project\tenopa proposer\-agent-master\app\prompts\bid_review.py) -- 2 connections
  - -> calls -> [[unresolvedrefjoin]]
  - <- contains <- [[bidreview]]
- **build_reviewer_system** (C:\project\tenopa proposer\-agent-master\app\prompts\bid_review.py) -- 2 connections
  - -> calls -> [[unresolvedrefformatkeywordlist]]
  - <- contains <- [[bidreview]]
- **build_unified_analysis_system** (C:\project\tenopa proposer\-agent-master\app\prompts\bid_review.py) -- 2 connections
  - -> calls -> [[unresolvedrefformatkeywordlist]]
  - <- contains <- [[bidreview]]

## Internal Relationships
- build_reviewer_system -> calls -> __unresolved__::ref::_format_keyword_list [EXTRACTED]
- build_unified_analysis_system -> calls -> __unresolved__::ref::_format_keyword_list [EXTRACTED]
- bid_review -> contains -> _format_keyword_list [EXTRACTED]
- bid_review -> contains -> build_reviewer_system [EXTRACTED]
- bid_review -> contains -> build_unified_analysis_system [EXTRACTED]

## Cross-Community Connections
- _format_keyword_list -> calls -> __unresolved__::ref::join (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 bid_review, __unresolved__::ref::_format_keyword_list, _format_keyword_list를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bid_review.py이다.

### Key Facts
- def _format_keyword_list(keywords: list[str]) -> str: """키워드 목록을 프롬프트 불릿 형식으로 변환.""" return "\n".join(f"- {kw}" for kw in keywords)
- def build_reviewer_system( positive: list[str] | None = None, negative: list[str] | None = None, ) -> str: """리뷰어 시스템 프롬프트를 동적 생성. 키워드 목록을 외부에서 주입 가능.""" pos = _format_keyword_list(positive or POSITIVE_KEYWORDS) neg = _format_keyword_list(negative or NEGATIVE_KEYWORDS) return f"""# Role 당신은…
- def build_unified_analysis_system( positive: list[str] | None = None, negative: list[str] | None = None, teams_info: str = "", ) -> str: """통합 분석 시스템 프롬프트를 동적 생성.""" pos = _format_keyword_list(positive or POSITIVE_KEYWORDS) neg = _format_keyword_list(negative or NEGATIVE_KEYWORDS) teams_section =…
