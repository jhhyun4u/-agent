# Bidding 모듈 리스트럭처링 계획 & 2. 현황 분석
Cohesion: 0.12 | Nodes: 16

## Key Nodes
- **Bidding 모듈 리스트럭처링 계획** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **2. 현황 분석** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 4 connections
  - -> contains -> [[21]]
  - -> contains -> [[22-api]]
  - -> contains -> [[23]]
  - <- contains <- [[bidding]]
- **4. 마이그레이션 전략** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 4 connections
  - -> contains -> [[41]]
  - -> contains -> [[42-pricing]]
  - -> contains -> [[43-import]]
  - <- contains <- [[bidding]]
- **4.1 호환성 레이어 (단계적 전환)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- has_code_example <- [[41]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[bidding]]
- **2.1 대상 파일 (서비스 레이어)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **2.2 API·그래프·프롬프트·모델** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **2.3 제외 대상** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **3. 목표 구조** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[bidding]]
- **4.2 pricing/ 이동** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4.3 Import 변경 영향 범위** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **5. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[bidding]]
- **6. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[bidding]]
- **7. 리스크 및 대응** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[bidding]]
- **8. 범위 외** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bidding-restructure.plan.md) -- 1 connections
  - <- contains <- [[bidding]]

## Internal Relationships
- 2. 현황 분석 -> contains -> 2.1 대상 파일 (서비스 레이어) [EXTRACTED]
- 2. 현황 분석 -> contains -> 2.2 API·그래프·프롬프트·모델 [EXTRACTED]
- 2. 현황 분석 -> contains -> 2.3 제외 대상 [EXTRACTED]
- 4. 마이그레이션 전략 -> contains -> 4.1 호환성 레이어 (단계적 전환) [EXTRACTED]
- 4. 마이그레이션 전략 -> contains -> 4.2 pricing/ 이동 [EXTRACTED]
- 4. 마이그레이션 전략 -> contains -> 4.3 Import 변경 영향 범위 [EXTRACTED]
- 4.1 호환성 레이어 (단계적 전환) -> has_code_example -> python [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 1. 배경 및 목적 [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 2. 현황 분석 [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 3. 목표 구조 [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 4. 마이그레이션 전략 [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 5. 구현 순서 [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 6. 성공 기준 [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 7. 리스크 및 대응 [EXTRACTED]
- Bidding 모듈 리스트럭처링 계획 -> contains -> 8. 범위 외 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Bidding 모듈 리스트럭처링 계획, 2. 현황 분석, 4. 마이그레이션 전략를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bidding-restructure.plan.md이다.

### Key Facts
- > 날짜: 2026-03-24 > 유형: 리팩토링 (기능 변경 없음) > 위험도: MEDIUM (import 경로 변경 → 전체 영향)
- **기존 import 경로를 즉시 깨뜨리지 않기 위해** 원래 위치에 re-export 파일을 남깁니다.
- ```python app/services/bid_calculator.py (호환 래퍼) """레거시 호환 — 실제 구현은 app.services.bidding.calculator""" from app.services.bidding.calculator import *  # noqa: F401,F403 ```
- Bidding 관련 파일 26개가 `app/services/` 루트에 flat하게 산재. `pricing/` 패키지만 유일하게 정리됨. 나머지 10개 `bid_*.py`가 다른 서비스(auth, kb, notification 등)와 섞여 가독성·탐색성 저하.
- | 파일 | 줄수 | 관심사 | import 참조 수 | |------|------|--------|:------------:| | `bid_calculator.py` | 190 | 노임단가 계산 (레거시 하드코딩) | 10 | | `bid_recommender.py` | 424 | AI 입찰 추천 | 2 | | `bid_scorer.py` | 391 | 공고 적합도 스코어링 | 3 | | `bid_fetcher.py` | 454 | G2B 공고 수집 + upsert | 2 | | `bid_preprocessor.py` | 101…
