# extract_json_from_response & __unresolved__::ref::asyncanthropic
Cohesion: 0.12 | Nodes: 17

## Key Nodes
- **extract_json_from_response** (C:\project\tenopa proposer\app\utils\claude_utils.py) -- 11 connections
  - -> calls -> [[unresolvedrefstrip]]
  - -> calls -> [[unresolvedrefsplit]]
  - -> calls -> [[unresolvedreffind]]
  - -> calls -> [[unresolvedrefrfind]]
  - -> calls -> [[unresolvedrefloads]]
  - -> calls -> [[unresolvedrefwarning]]
  - -> calls -> [[unresolvedrefrepairtruncatedjson]]
  - -> calls -> [[unresolvedreferror]]
  - -> calls -> [[unresolvedrefclaudeapierror]]
  - -> calls -> [[unresolvedrefstr]]
  - <- contains <- [[claudeutils]]
- **__unresolved__::ref::asyncanthropic** () -- 7 connections
  - <- calls <- [[getclient]]
  - <- calls <- [[init]]
  - <- calls <- [[generatepresentationslides]]
  - <- calls <- [[extracttocwithclaude]]
  - <- calls <- [[init]]
  - <- calls <- [[init]]
  - <- calls <- [[createanthropicclient]]
- **__unresolved__::ref::rfind** () -- 7 connections
  - <- calls <- [[rununifiedanalysis]]
  - <- calls <- [[truncatecontext]]
  - <- calls <- [[parsesummary]]
  - <- calls <- [[parsequalificationresponse]]
  - <- calls <- [[parsereviewresponse]]
  - <- calls <- [[extractjsonfromresponse]]
  - <- calls <- [[repairtruncatedjson]]
- **_parse_summary** (C:\project\tenopa proposer\app\services\bidding\monitor\preprocessor.py) -- 7 connections
  - -> calls -> [[unresolvedreffind]]
  - -> calls -> [[unresolvedrefrfind]]
  - -> calls -> [[unresolvedrefwarning]]
  - -> calls -> [[unresolvedrefloads]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefbidsummary]]
  - <- contains <- [[bidpreprocessor]]
- **BidPreprocessor** (C:\project\tenopa proposer\app\services\bidding\monitor\preprocessor.py) -- 5 connections
  - -> contains -> [[init]]
  - -> contains -> [[preprocess]]
  - -> contains -> [[preprocessbatch]]
  - -> contains -> [[parsesummary]]
  - <- contains <- [[preprocessor]]
- **__unresolved__::ref::preprocess** () -- 3 connections
  - <- calls <- [[runanalysisifneeded]]
  - <- calls <- [[preprocessbatch]]
  - <- calls <- [[reviewsingle]]
- **__init__** (C:\project\tenopa proposer\app\services\bidding\monitor\recommender.py) -- 3 connections
  - -> calls -> [[unresolvedrefasyncanthropic]]
  - -> calls -> [[unresolvedrefbidpreprocessor]]
  - <- contains <- [[bidrecommender]]
- **review_single** (C:\project\tenopa proposer\app\services\bidding\monitor\recommender.py) -- 3 connections
  - -> calls -> [[unresolvedrefpreprocess]]
  - -> calls -> [[unresolvedrefcalltenopareview]]
  - <- contains <- [[bidrecommender]]
- **__init__** (C:\project\tenopa proposer\app\services\phase_executor.py) -- 3 connections
  - -> calls -> [[unresolvedrefasyncanthropic]]
  - -> calls -> [[unresolvedrefset]]
  - <- contains <- [[phaseexecutor]]
- **truncate_context** (C:\project\tenopa proposer\app\services\token_manager.py) -- 3 connections
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefrfind]]
  - <- contains <- [[tokenmanager]]
- **__unresolved__::ref::_call_tenopa_review** () -- 2 connections
  - <- calls <- [[scorebids]]
  - <- calls <- [[reviewsingle]]
- **__unresolved__::ref::bidpreprocessor** () -- 2 connections
  - <- calls <- [[runanalysisifneeded]]
  - <- calls <- [[init]]
- **__init__** (C:\project\tenopa proposer\app\services\bidding\monitor\preprocessor.py) -- 2 connections
  - -> calls -> [[unresolvedrefasyncanthropic]]
  - <- contains <- [[bidpreprocessor]]
- **preprocess_batch** (C:\project\tenopa proposer\app\services\bidding\monitor\preprocessor.py) -- 2 connections
  - -> calls -> [[unresolvedrefpreprocess]]
  - <- contains <- [[bidpreprocessor]]
- **_get_client** (C:\project\tenopa proposer\app\services\claude_client.py) -- 2 connections
  - -> calls -> [[unresolvedrefasyncanthropic]]
  - <- contains <- [[claudeclient]]
- **__unresolved__::ref::_repair_truncated_json** () -- 1 connections
  - <- calls <- [[extractjsonfromresponse]]
- **__unresolved__::ref::bidsummary** () -- 1 connections
  - <- calls <- [[parsesummary]]

## Internal Relationships
- BidPreprocessor -> contains -> __init__ [EXTRACTED]
- BidPreprocessor -> contains -> preprocess_batch [EXTRACTED]
- BidPreprocessor -> contains -> _parse_summary [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::asyncanthropic [EXTRACTED]
- _parse_summary -> calls -> __unresolved__::ref::rfind [EXTRACTED]
- _parse_summary -> calls -> __unresolved__::ref::bidsummary [EXTRACTED]
- preprocess_batch -> calls -> __unresolved__::ref::preprocess [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::asyncanthropic [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::bidpreprocessor [EXTRACTED]
- review_single -> calls -> __unresolved__::ref::preprocess [EXTRACTED]
- review_single -> calls -> __unresolved__::ref::_call_tenopa_review [EXTRACTED]
- _get_client -> calls -> __unresolved__::ref::asyncanthropic [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::asyncanthropic [EXTRACTED]
- truncate_context -> calls -> __unresolved__::ref::rfind [EXTRACTED]
- extract_json_from_response -> calls -> __unresolved__::ref::rfind [EXTRACTED]
- extract_json_from_response -> calls -> __unresolved__::ref::_repair_truncated_json [EXTRACTED]

## Cross-Community Connections
- BidPreprocessor -> contains -> preprocess (-> [[unresolvedrefget-unresolvedrefexecute]])
- _parse_summary -> calls -> __unresolved__::ref::find (-> [[unresolvedrefreact-unresolvedreflibapi]])
- _parse_summary -> calls -> __unresolved__::ref::warning (-> [[unresolvedrefget-unresolvedrefexecute]])
- _parse_summary -> calls -> __unresolved__::ref::loads (-> [[unresolvedrefget-unresolvedrefexecute]])
- _parse_summary -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- __init__ -> calls -> __unresolved__::ref::set (-> [[unresolvedrefget-unresolvedrefexecute]])
- truncate_context -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])
- extract_json_from_response -> calls -> __unresolved__::ref::strip (-> [[unresolvedrefget-unresolvedrefexecute]])
- extract_json_from_response -> calls -> __unresolved__::ref::split (-> [[unresolvedrefreact-unresolvedreflibapi]])
- extract_json_from_response -> calls -> __unresolved__::ref::find (-> [[unresolvedrefreact-unresolvedreflibapi]])
- extract_json_from_response -> calls -> __unresolved__::ref::loads (-> [[unresolvedrefget-unresolvedrefexecute]])
- extract_json_from_response -> calls -> __unresolved__::ref::warning (-> [[unresolvedrefget-unresolvedrefexecute]])
- extract_json_from_response -> calls -> __unresolved__::ref::error (-> [[unresolvedrefget-unresolvedrefexecute]])
- extract_json_from_response -> calls -> __unresolved__::ref::claudeapierror (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- extract_json_from_response -> calls -> __unresolved__::ref::str (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 extract_json_from_response, __unresolved__::ref::asyncanthropic, __unresolved__::ref::rfind를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 claude_client.py, claude_utils.py, phase_executor.py, preprocessor.py, recommender.py이다.

### Key Facts
- def extract_json_from_response(response_text: str) -> Dict[str, Any]: """ Claude 응답에서 JSON 추출 (다단계 폴백)
- try: response = await self.client.messages.create( model=self.model, max_tokens=2500, timeout=self.CLAUDE_TIMEOUT, system=PREPROCESSOR_SYSTEM, messages=[{"role": "user", "content": user_msg}], ) text = response.content[0].text return self._parse_summary(text, bid) except Exception as e:…
- class BidPreprocessor: """Claude 기반 공고문 전처리 에이전트"""
- def __init__(self): self.client = AsyncAnthropic(api_key=settings.anthropic_api_key) self.model = "claude-sonnet-4-5-20250929" self.preprocessor = BidPreprocessor()
- async def review_single( self, bid: BidAnnouncement, pre_summary: "BidSummary | None" = None, ) -> TenopaBidReview | None: """단일 공고 TENOPA 리뷰.
